"""
Terravyn Green Gram Irrigation Decision Engine V1.
Deterministic, explainable, rule-based agronomic decision engine.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.domain import Farm, Device, DeviceTelemetry, IrrigationLog, CropDecisionLog
from services.weather import WeatherService
from .models import (
    NormalizedDecisionInput, CropInput, FieldInput, SoilInput,
    EnvironmentInput, WeatherInput, IrrigationHistoryInput,
    DecisionResult, DecisionFactors
)
from .green_gram_config import (
    determine_growth_stage, STAGE_MATURITY, STAGE_FLOWERING,
    STAGE_POD_FORMATION, STAGE_POD_FILLING, STAGE_VEGETATIVE,
    STAGE_SEEDLING, STAGE_GERMINATION, STAGE_SOWING
)
from .rules import (
    AGRONOMIC_RULES, get_soil_factor, STATUS_VALIDATED, STATUS_PRELIMINARY
)
from .sensor_validator import validate_sensor_telemetry
from .weather_validator import validate_weather_data
from .stability import check_irrigation_cooldown
from .knowledge_base import (
    knowledge_base, KnowledgeStatus, ConfidenceLevel, get_source
)

logger = logging.getLogger(__name__)

ENGINE_VERSION = "green-gram-irrigation-v1"


class GreenGramIrrigationDecisionEngine:
    def __init__(
        self,
        weather_service: Optional[WeatherService] = None,
        research_service: Optional[Any] = None
    ):
        self.weather_service = weather_service or WeatherService()
        if research_service is None:
            from services.research_engine.service import ResearchAndKnowledgeAcquisitionService
            self.research_service = ResearchAndKnowledgeAcquisitionService()
        else:
            self.research_service = research_service

    def build_normalized_input(
        self,
        db: Session,
        farm: Farm,
        current_time: Optional[datetime] = None
    ) -> NormalizedDecisionInput:
        """
        Extract and normalize inputs across Farm, Device, Telemetry, Weather, and Irrigation logs.
        """
        now = current_time or datetime.utcnow()

        # 1. Growth Stage & Crop Profile
        stage_info = determine_growth_stage(
            sowing_date=farm.sowing_date,
            variety_name=farm.crop_variety,
            manual_override=farm.growth_stage_override
        )
        crop_input = CropInput(
            crop_name=farm.crop_type or "Green Gram (Moong)",
            variety=farm.crop_variety,
            sowing_date=farm.sowing_date,
            age_days=stage_info["age_days"],
            growth_stage=stage_info["stage"],
            is_stage_manual=stage_info["is_manual"]
        )

        # 2. Field Profile
        field_input = FieldInput(
            farm_id=farm.id,
            farm_name=farm.name,
            area=farm.area,
            area_unit=farm.area_unit or "Acres",
            soil_type=farm.soil_type or "Sandy Loam",
            latitude=farm.latitude,
            longitude=farm.longitude,
            plot_type=getattr(farm, "plot_type", "STANDARD") or "STANDARD",
            experiment_active=getattr(farm, "experiment_active", False) or False
        )

        # 3. Device & In-Situ Sensor Telemetry
        device = db.query(Device).filter(Device.farm_id == farm.id).first()
        latest_telem = None
        moisture = None
        temp_c = None
        humidity_pct = None
        last_telem_time = None
        telem_age_sec = None

        if device:
            last_telem_time = device.last_seen
            moisture = device.last_soil_moisture
            temp_c = device.last_temperature
            humidity_pct = device.last_humidity

            latest_telem = (
                db.query(DeviceTelemetry)
                .filter(DeviceTelemetry.device_id == device.id)
                .order_by(desc(DeviceTelemetry.recorded_at))
                .first()
            )
            if latest_telem:
                if latest_telem.soil_moisture is not None:
                    moisture = latest_telem.soil_moisture
                if latest_telem.temperature is not None:
                    temp_c = latest_telem.temperature
                if latest_telem.humidity is not None:
                    humidity_pct = latest_telem.humidity
                if latest_telem.recorded_at:
                    last_telem_time = latest_telem.recorded_at

            if last_telem_time:
                telem_age_sec = int((now - last_telem_time).total_seconds())

        soil_input = SoilInput(
            moisture_pct=moisture,
            ph=getattr(farm, "soil_ph", None),
            ec=getattr(farm, "soil_ec", None)
        )
        env_input = EnvironmentInput(
            temperature=temp_c,
            humidity=humidity_pct,
            light=None
        )

        # 4. Weather & Evapotranspiration
        weather_res = self.weather_service.get_weather_for_farm(db, farm, force_refresh=False)
        curr_w = weather_res.get("current") or {}
        daily_w = weather_res.get("daily") or []
        w_available = weather_res.get("location_configured", False) and weather_res.get("current") is not None
        rain_sum_24h = daily_w[0].get("precipitation_sum") if daily_w else None
        rain_prob_24h = daily_w[0].get("precipitation_probability_max") if daily_w else None
        et0_val = daily_w[0].get("et0_fao_evapotranspiration") if daily_w else curr_w.get("et0_fao_evapotranspiration")

        weather_input = WeatherInput(
            current_temp=curr_w.get("temperature"),
            current_humidity=curr_w.get("relative_humidity"),
            precipitation=curr_w.get("precipitation"),
            precipitation_probability_24h=rain_prob_24h,
            forecast_rainfall_24h=rain_sum_24h,
            wind_speed=curr_w.get("wind_speed_10m"),
            et0_today=et0_val,
            is_available=w_available,
            is_stale=False,
            last_updated=weather_res.get("last_updated")
        )

        # 5. Irrigation History & Cooldown
        last_irr_log = None
        hrs_since_last_irr = None
        recent_count = 0

        if device:
            last_irr_log = (
                db.query(IrrigationLog)
                .filter(IrrigationLog.device_id == device.id, IrrigationLog.action.ilike("%on%"))
                .order_by(desc(IrrigationLog.timestamp))
                .first()
            )
            if last_irr_log and last_irr_log.timestamp:
                hrs_since_last_irr = (now - last_irr_log.timestamp).total_seconds() / 3600.0

            since_24h = now - timedelta(hours=24)
            recent_count = (
                db.query(IrrigationLog)
                .filter(IrrigationLog.device_id == device.id, IrrigationLog.timestamp >= since_24h)
                .count()
            )

        irr_history = IrrigationHistoryInput(
            last_irrigation_at=last_irr_log.timestamp if last_irr_log else None,
            hours_since_last_irrigation=hrs_since_last_irr,
            last_action=last_irr_log.action if last_irr_log else None,
            recent_events_count_24h=recent_count
        )

        return NormalizedDecisionInput(
            crop=crop_input,
            field=field_input,
            soil=soil_input,
            environment=env_input,
            weather=weather_input,
            irrigation=irr_history,
            device_id=device.id if device else None,
            device_uid=device.device_uid if device else None,
            telemetry_age_seconds=telem_age_sec,
            evaluated_at=now
        )

    def evaluate(
        self,
        input_data: NormalizedDecisionInput,
        db: Optional[Session] = None
    ) -> DecisionResult:
        """
        Execute deterministic, explainable agronomic decision logic grounded in Green Gram Knowledge Base.
        """
        reasons: List[str] = []
        evidence: List[Dict[str, Any]] = []
        citations: List[Dict[str, Any]] = []
        experimental_parameters: List[Dict[str, Any]] = []
        now = input_data.evaluated_at
        stage = input_data.crop.growth_stage
        all_sources = knowledge_base.get_all_sources()

        stage_def = knowledge_base.get_stage(stage)
        soil_prof = knowledge_base.get_soil(input_data.field.soil_type)

        def add_citation(source_id: str):
            src = all_sources.get(source_id)
            if src:
                src_dict = src.dict() if hasattr(src, "dict") else dict(src)
                if not any(c.get("source_id") == source_id for c in citations):
                    citations.append(src_dict)

        # -------------------------------------------------------------
        # STEP 1: Sensor Telemetry Validation (Failsafe)
        # -------------------------------------------------------------
        sensor_valid, sensor_issues = validate_sensor_telemetry(
            soil_moisture=input_data.soil.moisture_pct,
            temperature=input_data.environment.temperature,
            humidity=input_data.environment.humidity,
            last_telemetry_at=now - timedelta(seconds=input_data.telemetry_age_seconds) if input_data.telemetry_age_seconds is not None else None,
            current_time=now
        )

        if not sensor_valid:
            for issue in sensor_issues:
                reasons.append(f"Sensor anomaly detected: {issue}")
            
            evidence.append({
                "parameter": "sensor_integrity",
                "status": KnowledgeStatus.VALIDATED.value,
                "confidence": ConfidenceLevel.HIGH.value,
                "source": "TERRAVYN-EXPERIMENTAL",
                "description": "Failsafe sensor telemetry validation rejected out-of-bounds, disconnected, or stale telemetry."
            })
            add_citation("TERRAVYN-EXPERIMENTAL")

            factors = {
                "soil_moisture": input_data.soil.moisture_pct,
                "crop_stage": stage,
                "sensor_status": "FAULT / DISCONNECTED",
                "weather_status": "N/A",
                "evidence": evidence,
                "citations": citations,
                "water_sensitivity": stage_def.water_sensitivity,
                "crop_coefficient_kc": stage_def.crop_coefficient_kc,
                "research_intelligence": {
                    "research_triggered": False,
                    "sufficiency": "N/A",
                    "research_engine_version": "research-engine-v1"
                }
            }
            res = DecisionResult(
                decision="ALERT",
                confidence=0,
                reasons=reasons,
                factors=factors,
                recommended_action="Inspect ESP32 device, probe wiring, and power before initiating irrigation.",
                engine_version=ENGINE_VERSION,
                generated_at=now,
                evidence=evidence,
                citations=citations,
                experimental_disclaimer="Preliminary / Experimental agronomic thresholds are used. Recommendations are advisory only."
            )
            if db:
                self._persist_decision(db, input_data, res)
            return res

        # -------------------------------------------------------------
        # STEP 2: Weather Data Validation & Fallback Flag
        # -------------------------------------------------------------
        w_usable, w_stale, w_advisories = validate_weather_data(
            is_available=input_data.weather.is_available,
            last_updated=input_data.weather.last_updated,
            current_temp=input_data.weather.current_temp,
            forecast_rainfall_24h=input_data.weather.forecast_rainfall_24h,
            et0_today=input_data.weather.et0_today,
            current_time=now
        )
        for adv in w_advisories:
            reasons.append(adv)

        # -------------------------------------------------------------
        # STEP 3: Maturity Stage Rule (Validated ICAR-IIPR)
        # -------------------------------------------------------------
        if stage in [STAGE_MATURITY, "Maturity", "Harvest", "Maturity / Harvest"]:
            reasons.append(
                "Crop is in Maturity / Harvest stage. All irrigation must cease 10–12 days prior to harvest "
                "to ensure uniform pod desiccation and prevent pod shattering (ICAR-IIPR Rule)."
            )
            evidence.append({
                "parameter": "growth_stage",
                "rule_id": "RULE-IRR-MATURITY-CEASE-01",
                "status": KnowledgeStatus.VALIDATED.value,
                "confidence": ConfidenceLevel.HIGH.value,
                "source": "ICAR-IIPR-2018",
                "description": "Stop irrigation 10-12 days prior to harvest to prevent pod decay and vivipary."
            })
            add_citation("ICAR-IIPR-2018")

            factors = {
                "soil_moisture": input_data.soil.moisture_pct,
                "crop_stage": stage,
                "water_sensitivity": stage_def.water_sensitivity,
                "crop_coefficient_kc": stage_def.crop_coefficient_kc,
                "rainfall_forecast_24h": input_data.weather.forecast_rainfall_24h,
                "rainfall_probability_24h": input_data.weather.precipitation_probability_24h,
                "et0": input_data.weather.et0_today,
                "sensor_status": "VALID",
                "weather_status": "VALID" if w_usable else "FALLBACK",
                "research_intelligence": {
                    "research_triggered": False,
                    "sufficiency": "SUFFICIENT",
                    "research_engine_version": "research-engine-v1"
                },
                "evidence": evidence,
                "citations": citations
            }
            res = DecisionResult(
                decision="WAIT",
                confidence=95,
                reasons=reasons,
                factors=factors,
                recommended_action="Maintain dry field conditions. Prepare for harvest.",
                engine_version=ENGINE_VERSION,
                generated_at=now,
                evidence=evidence,
                citations=citations,
                experimental_disclaimer="Preliminary / Experimental agronomic thresholds are used. Recommendations are advisory only."
            )
            if db:
                self._persist_decision(db, input_data, res)
            return res

        # -------------------------------------------------------------
        # STEP 4: Post-Irrigation Cooldown / Redistribution Check
        # -------------------------------------------------------------
        in_cooldown, cooldown_msg = check_irrigation_cooldown(
            input_data.irrigation.hours_since_last_irrigation
        )
        if in_cooldown:
            reasons.append(cooldown_msg)
            evidence.append({
                "parameter": "hours_since_last_irrigation",
                "rule_id": "RULE-IRR-COOLDOWN-SOAK-03",
                "status": KnowledgeStatus.VALIDATED.value,
                "confidence": ConfidenceLevel.HIGH.value,
                "source": "TERRAVYN-EXPERIMENTAL",
                "description": "Enforce minimum 2-hour soak and hydraulic redistribution window."
            })
            add_citation("TERRAVYN-EXPERIMENTAL")

            factors = {
                "soil_moisture": input_data.soil.moisture_pct,
                "crop_stage": stage,
                "water_sensitivity": stage_def.water_sensitivity,
                "crop_coefficient_kc": stage_def.crop_coefficient_kc,
                "hours_since_last_irrigation": input_data.irrigation.hours_since_last_irrigation,
                "sensor_status": "VALID",
                "weather_status": "VALID" if w_usable else "FALLBACK",
                "research_intelligence": {
                    "research_triggered": False,
                    "sufficiency": "SUFFICIENT",
                    "research_engine_version": "research-engine-v1"
                },
                "evidence": evidence,
                "citations": citations
            }
            res = DecisionResult(
                decision="WAIT",
                confidence=85,
                reasons=reasons,
                factors=factors,
                recommended_action="Allow applied water to redistribute into the subsoil root zone before taking action.",
                engine_version=ENGINE_VERSION,
                generated_at=now,
                evidence=evidence,
                citations=citations,
                experimental_disclaimer="Preliminary / Experimental agronomic thresholds are used. Recommendations are advisory only."
            )
            if db:
                self._persist_decision(db, input_data, res)
            return res

        # -------------------------------------------------------------
        # STEP 5: Agronomic Moisture Evaluation (Stage + Soil Type)
        # -------------------------------------------------------------
        moisture = float(input_data.soil.moisture_pct)
        soil_offset = soil_prof.capacitive_moisture_offset

        # Base threshold table (Preliminary/Experimental capacitive sensor calibration)
        if stage in [STAGE_FLOWERING, STAGE_POD_FORMATION, "Flowering", "Pod Formation"]:
            base_threshold = 40.0 # Peak sensitive stage
            stage_priority = "CRITICAL"
        elif stage in [STAGE_POD_FILLING, "Pod Filling"]:
            base_threshold = 35.0
            stage_priority = "HIGH"
        elif stage in [STAGE_VEGETATIVE, "Vegetative", "Branching"]:
            base_threshold = 30.0
            stage_priority = "MODERATE"
        elif stage in [STAGE_SEEDLING, STAGE_GERMINATION, STAGE_SOWING, "Seedling", "Germination", "Sowing"]:
            base_threshold = 28.0
            stage_priority = "MODERATE"
        else:
            base_threshold = 32.0
            stage_priority = "MODERATE"

        # Check for ACTIVE field-specific calibration
        active_cal = None
        if db:
            try:
                from services.validation_engine.calibration_manager import FieldCalibrationManager
                active_cal = FieldCalibrationManager.get_active_calibration(
                    db=db,
                    field_id=input_data.field.farm_id,
                    soil_type=input_data.field.soil_type,
                    growth_stage=stage,
                    crop=input_data.crop.crop_name or "Green Gram (Moong)"
                )
            except Exception as e:
                logger.warning(f"[CropDecisionEngine] Active calibration lookup non-fatal error: {e}")

        if active_cal and active_cal.value is not None:
            effective_threshold = float(active_cal.value)
            calibration_info = {
                "calibrated": True,
                "calibration_id": active_cal.id,
                "version": active_cal.version,
                "status": "FIELD_CALIBRATED",
                "scope": active_cal.scope,
                "range": active_cal.value_range,
                "hysteresis_delta": active_cal.hysteresis_delta
            }
            experimental_parameters.append({
                "parameter": "capacitive_soil_moisture_threshold",
                "value": effective_threshold,
                "unit": active_cal.unit or "% volumetric",
                "status": "FIELD_CALIBRATED",
                "note": f"Field-specific calibrated parameter v{active_cal.version} (Scope: {active_cal.scope})"
            })
            evidence.append({
                "parameter": "capacitive_soil_moisture_threshold",
                "status": "FIELD_CALIBRATED",
                "confidence": ConfidenceLevel.HIGH.value if active_cal.confidence >= 75 else ConfidenceLevel.MEDIUM.value,
                "source": "FIELD-CALIBRATED-v" + str(active_cal.version),
                "description": f"Field-calibrated moisture threshold of {effective_threshold}% applied for {stage} stage."
            })
        else:
            calibration_info = {"calibrated": False, "status": "DEFAULT_AGRONOMIC_RULE"}
            effective_threshold = base_threshold + soil_offset
            experimental_parameters.append({
                "parameter": "capacitive_soil_moisture_threshold",
                "value": effective_threshold,
                "unit": "% volumetric",
                "status": KnowledgeStatus.EXPERIMENTAL.value,
                "note": "Experimental Terravyn parameter (field calibration required)"
            })

        # Atmospheric demand & rainfall
        et0 = input_data.weather.et0_today
        rain_24h = input_data.weather.forecast_rainfall_24h or 0.0
        rain_prob = input_data.weather.precipitation_probability_24h or 0

        # Environmental & Climate Risk Checks
        climate_eval = knowledge_base.evaluate_climate_risk(
            temperature=input_data.environment.temperature,
            humidity=input_data.environment.humidity,
            growth_stage=stage
        )
        for risk in climate_eval.get("risks", []):
            reasons.append(f"Agronomic Climate Alert: {risk['message']}")
            src_id = risk["source"].source_id if hasattr(risk["source"], "source_id") else "ICAR-IIPR-2018"
            evidence.append({
                "parameter": "climate_stress",
                "status": KnowledgeStatus.VALIDATED.value,
                "source": src_id,
                "description": risk["message"]
            })
            add_citation(src_id)

        # Extreme Weather Checks
        extreme_eval = knowledge_base.evaluate_extreme_conditions(
            temperature=input_data.environment.temperature,
            humidity=input_data.environment.humidity,
            rainfall_forecast=rain_24h,
            growth_stage=stage,
            soil_moisture=moisture
        )
        for ext in extreme_eval:
            reasons.append(f"Extreme Weather Protocol ({ext['condition']}): {ext['action']}")
            src_id = ext["source"].source_id if hasattr(ext["source"], "source_id") else "CRIDA-CONTINGENCY-2019"
            add_citation(src_id)

        # Active Disease and Pest Risks for Current Stage
        active_diseases = knowledge_base.evaluate_disease_risk(
            growth_stage=stage,
            temperature=input_data.environment.temperature,
            humidity=input_data.environment.humidity
        )
        active_pests = knowledge_base.evaluate_pest_risk(growth_stage=stage)

        # -------------------------------------------------------------
        # STEP 5B: Closed-Loop Research & Dynamic Knowledge Acquisition
        # -------------------------------------------------------------
        from services.research_engine.service import ENGINE_VERSION as RESEARCH_ENGINE_VERSION
        from services.research_engine.fingerprint import build_fingerprint_from_inputs

        research_info = {
            "research_triggered": False,
            "research_engine_version": RESEARCH_ENGINE_VERSION,
            "fingerprint_hash": None,
            "sufficiency": "SUFFICIENT"
        }
        if db:
            try:
                fingerprint = build_fingerprint_from_inputs(
                    crop_name=input_data.crop.crop_name,
                    variety=input_data.crop.variety,
                    growth_stage=stage,
                    soil_type=input_data.field.soil_type,
                    soil_moisture_pct=moisture,
                    temperature_c=input_data.environment.temperature,
                    humidity_pct=input_data.environment.humidity,
                    forecast_rain_mm=rain_24h,
                    rain_probability_pct=rain_prob,
                    et0_mm=et0,
                    recent_rain=getattr(input_data.weather, "recent_rain_detected", False) or False,
                    recent_irrigation=(input_data.irrigation.hours_since_last_irrigation is not None and input_data.irrigation.hours_since_last_irrigation < 24.0),
                    target_threshold=effective_threshold
                )
                research_res = self.research_service.process_field_situation(
                    db=db,
                    fingerprint=fingerprint,
                    farm_id=input_data.field.farm_id
                )
                research_info["research_triggered"] = research_res.research_triggered
                research_info["fingerprint_hash"] = fingerprint.compute_hash()
                research_info["sufficiency"] = research_res.match_result.sufficiency.value
                research_info["similarity_score"] = research_res.match_result.similarity_score

                if research_res.research_triggered and research_res.sources_searched > 0:
                    reasons.append(
                        f"Relevant agricultural research acquired from approved sources "
                        f"({research_res.sources_searched} sources evaluated, {research_res.claims_extracted} evidence claims analyzed)."
                    )
                for cit in research_res.citations:
                    citations.append({
                        "source_id": cit.get("sourceTitle"),
                        "title": cit.get("sourceTitle"),
                        "organization": cit.get("organization"),
                        "url": cit.get("url"),
                        "source_tier": cit.get("sourceTier", 1),
                        "evidence_status": cit.get("status", "PROVISIONAL"),
                        "confidence": "HIGH" if cit.get("sourceTier") == 1 else "MEDIUM"
                    })
                for promo in research_res.promoted_items:
                    evidence.append({
                        "parameter": promo.get("parameter", "research_finding"),
                        "status": promo.get("status", "PROVISIONAL"),
                        "confidence": "HIGH",
                        "source": "RESEARCH-ACQUIRED",
                        "description": promo.get("finding") or "Acquired research evidence applied."
                    })
            except Exception as e:
                logger.warning(f"[CropDecisionEngine] Research processing non-fatal exception: {e}")

        factors = {
            "soil_moisture": moisture,
            "effective_threshold": effective_threshold,
            "crop_stage": stage,
            "stage_priority": stage_priority,
            "soil_type": input_data.field.soil_type,
            "soil_drainage": soil_prof.drainage_character,
            "soil_waterlogging_risk": soil_prof.waterlogging_risk,
            "water_sensitivity": stage_def.water_sensitivity,
            "crop_coefficient_kc": stage_def.crop_coefficient_kc,
            "rainfall_forecast_24h": rain_24h,
            "rainfall_probability_24h": rain_prob,
            "et0": et0,
            "temperature": input_data.environment.temperature,
            "humidity": input_data.environment.humidity,
            "sensor_status": "VALID",
            "weather_status": "VALID" if w_usable else "FALLBACK",
            "disease_risks_active": [d["disease_name"] for d in active_diseases],
            "pest_risks_active": [p["pest_name"] for p in active_pests],
            "experimental_parameters": experimental_parameters,
            "calibration_info": calibration_info,
            "research_intelligence": research_info,
            "evidence": evidence,
            "citations": citations
        }

        # -------------------------------------------------------------
        # STEP 6: Decision Synthesis
        # -------------------------------------------------------------
        if moisture >= effective_threshold:
            # Case 1: Adequate Moisture
            decision = "MONITOR"
            confidence = 85
            reasons.append(
                f"Current soil moisture ({moisture:.1f}%) is above the {effective_threshold:.1f}% threshold for the {stage} stage "
                f"in {input_data.field.soil_type} soil."
            )
            evidence.append({
                "parameter": "soil_moisture",
                "status": KnowledgeStatus.VALIDATED.value,
                "confidence": ConfidenceLevel.HIGH.value,
                "source": "ICAR-IIPR-2018",
                "description": f"Soil moisture exceeds baseline depletion threshold for {stage} stage."
            })
            add_citation("ICAR-IIPR-2018")

            if et0 and et0 >= 5.5:
                reasons.append(f"Atmospheric evaporative demand (ET₀ = {et0:.1f} mm/day) is high; soil moisture depletion may accelerate.")
                add_citation("FAO-56-CROPWAT")

            recommended_action = "Soil moisture is satisfactory. Continue monitoring root zone levels."

        else:
            # Case 2: Moisture is Low -> Check Weather Forecast!
            if w_usable and rain_24h >= 5.0 and rain_prob >= 50:
                # Meaningful rain forecast -> Hold off!
                decision = "WAIT"
                confidence = 90
                reasons.append(
                    f"Soil moisture ({moisture:.1f}%) is below the {effective_threshold:.1f}% stage target, BUT significant rainfall "
                    f"({rain_24h:.1f} mm, {rain_prob}% probability) is forecast within the next 24 hours."
                )
                reasons.append(
                    "Irrigation is suspended to conserve water and protect Green Gram roots against surface waterlogging (Agromet Rule)."
                )
                evidence.append({
                    "parameter": "forecast_rainfall_24h",
                    "rule_id": "RULE-IRR-RAIN-FORECAST-02",
                    "status": KnowledgeStatus.VALIDATED.value,
                    "confidence": ConfidenceLevel.HIGH.value,
                    "source": "CRIDA-CONTINGENCY-2019",
                    "description": "Suspend irrigation when >= 5mm rain is forecast with >= 50% probability."
                })
                add_citation("CRIDA-CONTINGENCY-2019")
                recommended_action = "Wait for anticipated precipitation. Re-evaluate moisture 6 hours post-rainfall."

            else:
                # No meaningful rain -> Need to Irrigate!
                decision = "IRRIGATE"
                confidence = 85 if w_usable else 75
                reasons.append(
                    f"Soil moisture ({moisture:.1f}%) is below the {effective_threshold:.1f}% threshold for the {stage} stage "
                    f"in {input_data.field.soil_type} soil."
                )
                evidence.append({
                    "parameter": "capacitive_soil_moisture",
                    "status": KnowledgeStatus.EXPERIMENTAL.value,
                    "confidence": ConfidenceLevel.MEDIUM.value,
                    "source": "TERRAVYN-EXPERIMENTAL",
                    "note": "Experimental Terravyn parameter (field calibration required)",
                    "description": f"Capacitive reading ({moisture:.1f}%) triggered irrigation below {effective_threshold:.1f}%."
                })
                add_citation("TERRAVYN-EXPERIMENTAL")
                add_citation("ICAR-IIPR-2018")

                if stage in [STAGE_FLOWERING, STAGE_POD_FORMATION, "Flowering", "Pod Formation"]:
                    reasons.append(
                        f"Crop is in a {stage_priority} moisture-sensitive stage ({stage}). Moisture stress at this stage will cause "
                        "flower drop and reduced pod setting (ICAR Agronomic Standard)."
                    )
                    evidence.append({
                        "parameter": "water_sensitivity",
                        "status": KnowledgeStatus.VALIDATED.value,
                        "confidence": ConfidenceLevel.HIGH.value,
                        "source": "ICAR-IIPR-2018",
                        "description": "Flowering and pod formation are critical water-stress sensitive stages."
                    })
                    add_citation("ICAR-IIPR-2018")

                if w_usable:
                    if rain_24h < 5.0 or rain_prob < 50:
                        reasons.append(f"No significant rain is forecast in the next 24h ({rain_24h:.1f} mm, {rain_prob}% prob).")
                    if et0 and et0 >= 5.0:
                        reasons.append(f"High reference evapotranspiration (ET₀ = {et0:.1f} mm/day) indicates rapid crop water consumption.")
                        add_citation("FAO-56-CROPWAT")
                else:
                    reasons.append("Meteorological forecast is offline/stale; decision grounds safely on live in-situ soil moisture deficit.")

                recommended_action = (
                    "Apply light, controlled irrigation (recommended depth 25–35 mm). "
                    "Avoid standing water; Green Gram roots are vulnerable to hypoxia."
                )

        res = DecisionResult(
            decision=decision,
            confidence=confidence,
            reasons=reasons,
            factors=factors,
            recommended_action=recommended_action,
            engine_version=ENGINE_VERSION,
            generated_at=now,
            evidence=evidence,
            citations=citations,
            experimental_disclaimer="Preliminary / Experimental agronomic thresholds are used. Recommendations are advisory only."
        )

        if db:
            self._persist_decision(db, input_data, res)

        return res

    def evaluate_farm(
        self,
        db: Session,
        farm: Farm,
        current_time: Optional[datetime] = None
    ) -> DecisionResult:
        """
        High-level wrapper: builds normalized input from DB and evaluates decision.
        """
        input_data = self.build_normalized_input(db, farm, current_time=current_time)
        return self.evaluate(input_data, db=db)

    def _persist_decision(
        self,
        db: Session,
        input_data: NormalizedDecisionInput,
        result: DecisionResult
    ):
        """
        Persist evaluation to crop_decision_logs for historical traceability.
        """
        try:
            log_entry = CropDecisionLog(
                farm_id=input_data.field.farm_id,
                device_id=input_data.device_id,
                timestamp=result.generated_at,
                crop=input_data.crop.crop_name,
                variety=input_data.crop.variety,
                growth_stage=input_data.crop.growth_stage,
                growth_stage_manual=input_data.crop.is_stage_manual,
                soil_moisture=input_data.soil.moisture_pct,
                temperature=input_data.environment.temperature,
                humidity=input_data.environment.humidity,
                rainfall_forecast_24h=input_data.weather.forecast_rainfall_24h,
                rainfall_probability_24h=input_data.weather.precipitation_probability_24h,
                et0=input_data.weather.et0_today,
                recent_irrigation_age_hours=input_data.irrigation.hours_since_last_irrigation,
                decision=result.decision,
                confidence=result.confidence,
                reasons=result.reasons,
                factors=result.factors,
                recommended_action=result.recommended_action,
                engine_version=result.engine_version
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            logger.info(f"[CropDecisionEngine] Logged decision {result.decision} for farm {input_data.field.farm_id}")

            # Check for active SHADOW calibrations to evaluate in parallel
            try:
                from services.validation_engine.calibration_manager import FieldCalibrationManager
                shadow_cals = FieldCalibrationManager.get_shadow_calibrations(
                    db=db,
                    field_id=input_data.field.farm_id,
                    growth_stage=input_data.crop.growth_stage
                )
                for s_cal in shadow_cals:
                    FieldCalibrationManager.run_shadow_evaluation(db, log_entry, s_cal)
            except Exception as shadow_err:
                logger.warning(f"[CropDecisionEngine] Parallel shadow evaluation non-fatal error: {shadow_err}")

        except Exception as e:
            logger.error(f"[CropDecisionEngine] Failed to persist decision log: {e}", exc_info=True)
            db.rollback()
