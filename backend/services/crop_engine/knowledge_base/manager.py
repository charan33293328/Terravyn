"""
Central Green Gram Knowledge Base Manager.
Coordinates access across all scientific domains, provenance tracking, and real-time risk synthesis.
"""

from typing import Dict, Any, List, Optional
from .provenance import (
    SOURCES, SourceReference, ConfidenceLevel, KnowledgeStatus, get_source
)
from .fundamentals import CROP_FUNDAMENTALS
from .varieties import (
    VARIETIES, VarietyModel, get_variety, list_all_varieties
)
from .growth_stages import (
    GROWTH_STAGES, GrowthStageDefinition, get_stage_by_name, list_all_stages
)
from .climate import (
    CLIMATE_KNOWLEDGE, evaluate_climate_risk
)
from .soil import (
    SOIL_PROFILES, SoilTypeProfile, get_soil_profile, evaluate_soil_chemical_status
)
from .water_irrigation import (
    WATER_REQUIREMENTS_KNOWLEDGE, MASTER_IRRIGATION_RULES,
    IrrigationRuleModel, get_irrigation_rules_for_stage
)
from .nutrients import (
    NUTRIENT_GUIDELINES, FOLIAR_NUTRITION_TECHNOLOGY, diagnose_chlorosis
)
from .diseases import (
    DISEASES, DiseaseModel, evaluate_disease_risk
)
from .pests import (
    PESTS, PestModel, evaluate_pest_risk
)
from .extreme_conditions import (
    EXTREME_PROTOCOLS, evaluate_extreme_conditions
)
from .regional import (
    REGIONAL_PROFILES, RegionalProfile, get_regional_profile
)

class GreenGramKnowledgeBase:
    """
    Unified, scientifically grounded, machine-readable Knowledge Base for Green Gram.
    """
    def __init__(self):
        self.fundamentals = CROP_FUNDAMENTALS
        self.sources = SOURCES

    def get_summary_profile(self) -> Dict[str, Any]:
        """Returns the high-level botanical and agronomic crop profile."""
        return {
            "crop": self.fundamentals["botanical_name"],
            "common_names": self.fundamentals["common_names"],
            "family": self.fundamentals["family"],
            "classification": self.fundamentals["crop_classification"],
            "duration_range_days": self.fundamentals["duration_range_days"],
            "seasons": self.fundamentals["major_growing_seasons"],
            "symbiotic_fixation": self.fundamentals["symbiotic_nitrogen_fixation"],
            "total_varieties_cataloged": len(VARIETIES),
            "total_growth_stages": len(GROWTH_STAGES),
            "total_sources_cataloged": len(self.sources)
        }

    def get_variety(self, name: Optional[str]) -> VarietyModel:
        return get_variety(name)

    def list_varieties(self) -> List[VarietyModel]:
        return list_all_varieties()

    def get_stage(self, stage_name: Optional[str]) -> GrowthStageDefinition:
        return get_stage_by_name(stage_name)

    def list_stages(self) -> List[GrowthStageDefinition]:
        return list_all_stages()

    def get_soil(self, soil_type: Optional[str]) -> SoilTypeProfile:
        return get_soil_profile(soil_type)

    def get_irrigation_rules(self, growth_stage: Optional[str] = None) -> List[IrrigationRuleModel]:
        if growth_stage:
            return get_irrigation_rules_for_stage(growth_stage)
        return MASTER_IRRIGATION_RULES

    def get_nutrient_guidelines(self) -> Dict[str, Any]:
        return {
            "nutrients": NUTRIENT_GUIDELINES,
            "foliar_technology": FOLIAR_NUTRITION_TECHNOLOGY
        }

    def get_diseases(self) -> Dict[str, DiseaseModel]:
        return DISEASES

    def get_pests(self) -> Dict[str, PestModel]:
        return PESTS

    def get_regional(self, region_name: Optional[str] = None) -> RegionalProfile:
        return get_regional_profile(region_name)

    def get_all_sources(self) -> Dict[str, SourceReference]:
        return self.sources

    def evaluate_climate_risk(
        self,
        temperature: Optional[float],
        humidity: Optional[float],
        growth_stage: str
    ) -> Dict[str, Any]:
        return evaluate_climate_risk(temperature, humidity, growth_stage)

    def evaluate_disease_risk(
        self,
        growth_stage: str,
        temperature: Optional[float] = None,
        humidity: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        return evaluate_disease_risk(growth_stage, temperature, humidity)

    def evaluate_pest_risk(self, growth_stage: str) -> List[Dict[str, Any]]:
        return evaluate_pest_risk(growth_stage)

    def evaluate_extreme_conditions(
        self,
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
        rainfall_forecast: Optional[float] = None,
        growth_stage: str = "Vegetative",
        soil_moisture: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        return evaluate_extreme_conditions(
            temperature=temperature,
            humidity=humidity,
            rainfall_forecast=rainfall_forecast,
            growth_stage=growth_stage,
            soil_moisture=soil_moisture
        )

    def synthesize_crop_status(
        self,
        growth_stage: str,
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
        soil_moisture: Optional[float] = None,
        soil_type: Optional[str] = None,
        rainfall_forecast_24h: Optional[float] = None,
        soil_ph: Optional[float] = None,
        soil_ec: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Synthesize multi-factor environmental, agronomic, disease, and pest status.
        Used by API and Dashboard for comprehensive crop status cards.
        """
        stage_def = self.get_stage(growth_stage)
        soil_prof = self.get_soil(soil_type)

        # 1. Climate & Environment
        climate_eval = evaluate_climate_risk(
            temperature=temperature,
            humidity=humidity,
            growth_stage=growth_stage
        )

        # 2. Water Status Synthesis
        water_sensitivity = stage_def.water_sensitivity
        water_status = "OPTIMAL"
        water_notes = []

        if soil_moisture is not None:
            effective_thresh = 35.0 + soil_prof.capacitive_moisture_offset
            if growth_stage in ["Flowering", "Pod Formation"]:
                effective_thresh = 40.0 + soil_prof.capacitive_moisture_offset

            if soil_moisture < effective_thresh:
                water_status = "DEFICIT"
                water_notes.append(
                    f"Soil moisture ({soil_moisture:.1f}%) is below {effective_thresh:.1f}% threshold for {growth_stage} in {soil_prof.soil_type}."
                )
            else:
                water_notes.append(f"Soil moisture ({soil_moisture:.1f}%) is adequate for {growth_stage}.")
        else:
            water_status = "UNKNOWN"
            water_notes.append("Live soil moisture telemetry currently unavailable.")

        if rainfall_forecast_24h and rainfall_forecast_24h >= 5.0:
            water_notes.append(f"Upcoming rainfall ({rainfall_forecast_24h:.1f} mm forecast in 24h).")

        # 3. Nutrient Status
        nutrient_eval = evaluate_soil_chemical_status(ph=soil_ph, ec=soil_ec)
        nutrient_advisory = {
            "stage_priority": stage_def.nutrient_priority,
            "soil_test_status": "AVAILABLE" if (soil_ph is not None or soil_ec is not None) else "NOT_PROVIDED (SOIL TEST REQUIRED)",
            "soil_health": nutrient_eval["status"],
            "advisory_notes": nutrient_eval["notes"],
            "disclaimer": "Nutrient recommendations are strictly advisory. Conduct lab soil tests before commercial fertilizer application."
        }

        # 4. Disease Risks
        disease_risks = evaluate_disease_risk(
            growth_stage=growth_stage,
            temperature=temperature,
            humidity=humidity
        )

        # 5. Pest Risks
        pest_risks = evaluate_pest_risk(growth_stage=growth_stage)

        # 6. Extreme Weather Protocols
        extreme_protocols = evaluate_extreme_conditions(
            temperature=temperature,
            humidity=humidity,
            rainfall_forecast=rainfall_forecast_24h,
            growth_stage=growth_stage,
            soil_moisture=soil_moisture
        )

        return {
            "crop": "Green Gram (Moong)",
            "growth_stage": stage_def.stage_name,
            "water_sensitivity": water_sensitivity,
            "crop_coefficient_kc": stage_def.crop_coefficient_kc,
            "environmental_status": {
                "status": climate_eval["status"],
                "temperature_c": temperature,
                "humidity_pct": humidity,
                "heat_stress": climate_eval["heat_stress"],
                "cold_stress": climate_eval["cold_stress"],
                "high_humidity_risk": climate_eval["high_rh_disease_risk"],
                "active_risks": climate_eval["risks"]
            },
            "water_status": {
                "status": water_status,
                "soil_moisture_pct": soil_moisture,
                "soil_type": soil_prof.soil_type,
                "drainage": soil_prof.drainage_character,
                "waterlogging_risk": soil_prof.waterlogging_risk,
                "notes": water_notes
            },
            "nutrient_advisory": nutrient_advisory,
            "disease_risks": disease_risks,
            "pest_risks": pest_risks,
            "extreme_conditions": extreme_protocols,
            "management_advisory": stage_def.management_advisory,
            "primary_source": stage_def.source
        }

# Global singleton instance
knowledge_base = GreenGramKnowledgeBase()
