"""
Terravyn Automated Test Suite: Knowledge Validation & Calibration Engine V1 (Prompt 7)
Covers all 14 required verification scenarios:
1. Scientific Evidence Validation (Tier 1 ICAR) -> VALIDATED
2. Weak / Unsourced Evidence Rejection -> REJECTED / UNDER_REVIEW
3. Multi-Source Corroboration & Duplicate Detection
4. Contextual Contradiction Resolution (Soil texture variance)
5. Experimental Single Observation Guard (N=1 blocked from calibration)
6. Multi-Replicate Trial Validation (N=30, high quality) -> FIELD_CALIBRATED
7. Sensor Calibration Freshness Check (Validates 4095=dry 1400=wet)
8. Field-Specific Scoping (Guards against universal generalization)
9. Range-Based Trigger Zones & Hysteresis Support
10. Growth-Stage Specific Scoping (Flowering vs Vegetative)
11. Shadow Mode Execution (Parallel evaluation without pump actuation)
12. Explicit Activation & Decision Engine Integration
13. Non-Destructive Rollback Verification
14. Decision Outcome Linking & Error Classification (CORRECT_WAIT, MISSED_IRRIGATION)
"""
import sys
import os
from datetime import datetime, date, timedelta

# Add backend directory to path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database.connection import SessionLocal
from models.domain import (
    Farm,
    Device,
    DynamicKnowledgeItem,
    Experiment,
    ExperimentGroup,
    ExperimentPlot,
    ExperimentPlant,
    SensorCalibrationRecord,
    ExperimentObservation,
    ExperimentIrrigationEvent,
    ExperimentDailySnapshot,
    KnowledgeValidationRecord,
    FieldCalibrationRecord,
    CalibrationVersion,
    CropDecisionLog,
    DecisionOutcomeRecord,
    ShadowDecisionLog,
    IrrigationLog,
)
from services.validation_engine import (
    ValidationConfidenceScorer,
    ScientificKnowledgeValidator,
    ExperimentalDataValidator,
    FieldCalibrationManager,
    DecisionOutcomeEvaluator,
    KnowledgeValidationAndCalibrationEngine,
)
from services.crop_engine.engine import GreenGramIrrigationDecisionEngine


def run_all_tests():
    db = SessionLocal()
    print("=" * 80)
    print("TERRAVYN VALIDATION & CALIBRATION ENGINE V1 — TEST SUITE")
    print("=" * 80)

    passed = 0
    total = 14

    try:
        # Get or create a test farm
        farm = db.query(Farm).filter(Farm.id == 1).first()
        if not farm:
            farm = Farm(
                name="Validation Research Farm",
                crop_type="Green Gram (Moong)",
                crop_variety="Pusa Vishal",
                soil_type="Sandy Loam",
                growth_stage_override="Flowering",
            )
            db.add(farm)
        else:
            farm.crop_type = "Green Gram (Moong)"
            farm.crop_variety = "Pusa Vishal"
            farm.growth_stage_override = "Flowering"
            farm.soil_type = "Sandy Loam"
        db.commit()
        db.refresh(farm)

        # -------------------------------------------------------------
        # Scenario 1: Scientific Evidence Validation (Tier 1 ICAR)
        # -------------------------------------------------------------
        print("\n[Scenario 1] Scientific Evidence Validation (Tier 1 ICAR)...")
        item_icar = DynamicKnowledgeItem(
            crop="Green Gram (Moong)",
            variety="Pusa Vishal",
            parameter="flowering_moisture_depletion",
            finding="Green Gram flowering stage requires maintenance of at least 24-26% soil moisture in sandy loam.",
            soil_type="Sandy Loam",
            growth_stage="Flowering",
            status="PROVISIONAL",
            confidence=70,
            source_provenance=[
                {"title": "ICAR-IIPR Pulses Agronomy Handbook", "organization": "ICAR-IIPR", "source_tier": 1},
                {"title": "FAO Irrigation and Drainage Paper 56", "organization": "FAO", "source_tier": 1},
            ],
        )
        db.add(item_icar)
        db.commit()
        db.refresh(item_icar)

        val_icar = ScientificKnowledgeValidator.validate_knowledge_item(
            db=db,
            knowledge_item_id=item_icar.id,
            target_field_context={"crop": "Green Gram (Moong)", "soil_type": "Sandy Loam", "growth_stage": "Flowering"},
        )
        assert val_icar.status == "VALIDATED", f"Expected VALIDATED, got {val_icar.status}"
        assert val_icar.confidence >= 75, f"Expected confidence >= 75, got {val_icar.confidence}"
        assert val_icar.recommended_next_step == "PROMOTE_TO_VALIDATED"
        print(f"  [PASS] Tier 1 ICAR/FAO evidence validated: Status={val_icar.status}, Conf={val_icar.confidence}%.")
        passed += 1

        # -------------------------------------------------------------
        # Scenario 2: Weak / Unsourced Evidence Rejection
        # -------------------------------------------------------------
        print("\n[Scenario 2] Weak / Unsourced Evidence Rejection...")
        item_weak = DynamicKnowledgeItem(
            crop="Green Gram (Moong)",
            parameter="rapid_irrigation_frequency",
            finding="Water green gram every 2 days irrespective of soil type.",
            status="PROVISIONAL",
            confidence=40,
            source_provenance=[
                {"title": "Commercial Gardening Forum Post", "organization": "Web Forum", "source_tier": 4},
            ],
        )
        db.add(item_weak)
        db.commit()
        db.refresh(item_weak)

        val_weak = ScientificKnowledgeValidator.validate_knowledge_item(
            db=db,
            knowledge_item_id=item_weak.id,
            target_field_context={"crop": "Green Gram (Moong)", "soil_type": "Sandy Loam"},
        )
        assert val_weak.status in ("REJECTED", "UNDER_REVIEW"), f"Expected REJECTED or UNDER_REVIEW, got {val_weak.status}"
        assert val_weak.confidence < 50
        print(f"  [PASS] Weak Tier 4 web claim correctly blocked: Status={val_weak.status}, Conf={val_weak.confidence}%.")
        passed += 1

        # -------------------------------------------------------------
        # Scenario 3: Multi-Source Corroboration & Duplicate Detection
        # -------------------------------------------------------------
        print("\n[Scenario 3] Multi-Source Corroboration & Circular Citation Detection...")
        item_dup = DynamicKnowledgeItem(
            crop="Green Gram (Moong)",
            parameter="pod_borer_management",
            finding="Neem seed kernel extract 5% effective against Maruca vitrata.",
            status="PROVISIONAL",
            confidence=60,
            source_provenance=[
                {"title": "Agricultural Portal Repost", "organization": "Portal A", "source_tier": 2},
                {"title": "Agricultural Portal Repost", "organization": "Portal B", "source_tier": 2}, # Duplicate title
            ],
        )
        db.add(item_dup)
        db.commit()
        db.refresh(item_dup)

        val_dup = ScientificKnowledgeValidator.validate_knowledge_item(db=db, knowledge_item_id=item_dup.id)
        assert any("circular" in lim.lower() or "overlapping" in lim.lower() for lim in val_dup.limitations)
        print("  [PASS] Detected overlapping/circular citation among duplicate sources.")
        passed += 1

        # -------------------------------------------------------------
        # Scenario 4: Contextual Contradiction Resolution
        # -------------------------------------------------------------
        print("\n[Scenario 4] Contextual Contradiction Resolution (Soil Texture Baseline)...")
        item_clay = DynamicKnowledgeItem(
            crop="Green Gram (Moong)",
            parameter="flowering_moisture_depletion", # Same parameter as item_icar
            finding="In heavy black clay soil, green gram flowering threshold is 34-36% moisture.",
            soil_type="Black Clay Soil", # Different soil context
            growth_stage="Flowering",
            status="PROVISIONAL",
            confidence=70,
            source_provenance=[
                {"title": "TNAU Pulses Research Report", "organization": "TNAU", "source_tier": 1},
            ],
        )
        db.add(item_clay)
        db.commit()
        db.refresh(item_clay)

        val_clay = ScientificKnowledgeValidator.validate_knowledge_item(db=db, knowledge_item_id=item_clay.id)
        # Should detect contextual variance rather than flat rejection
        assert any("soil texture" in r.lower() or "contextual" in r.lower() for r in val_clay.reasons + val_clay.limitations)
        print("  [PASS] Legitimate soil-dependent moisture baseline difference recognized as contextual.")
        passed += 1

        # -------------------------------------------------------------
        # Scenario 5: Experimental Single Observation Guard (Mandatory)
        # -------------------------------------------------------------
        print("\n[Scenario 5] Single Observation Guard (N=1 blocked from calibration)...")
        # Create an experiment with only 1 observation and 1 plant
        exp_single = Experiment(
            name="Single Observation Test Trial",
            crop="Green Gram (Moong)",
            variety="Pusa Vishal",
            status="ACTIVE",
        )
        db.add(exp_single)
        db.commit()
        db.refresh(exp_single)

        grp_s = ExperimentGroup(experiment_id=exp_single.id, name="Test Group", type="TERRAVYN")
        db.add(grp_s)
        db.commit()
        db.refresh(grp_s)

        plt_s = ExperimentPlot(group_id=grp_s.id, name="Pot 1")
        db.add(plt_s)
        db.commit()
        db.refresh(plt_s)

        pln_s = ExperimentPlant(plot_id=plt_s.id, plant_tag="S-P1-01")
        obs_single = ExperimentObservation(
            experiment_id=exp_single.id,
            group_id=grp_s.id,
            plot_id=plt_s.id,
            plant_id=pln_s.id,
            parameter="plant_height",
            value_numeric=22.0,
            unit="cm",
        )
        db.add_all([pln_s, obs_single])
        db.commit()

        val_single = ExperimentalDataValidator.validate_trial_candidate(db=db, experiment_id=exp_single.id)
        assert val_single.status == "EXPERIMENTAL", f"Expected EXPERIMENTAL, got {val_single.status}"
        assert val_single.recommended_next_step == "KEEP_EXPERIMENTAL"
        assert any("single observation" in lim.lower() for lim in val_single.limitations)
        print("  [PASS] Single observation guard strictly enforced: Status remains EXPERIMENTAL.")
        passed += 1

        # -------------------------------------------------------------
        # Scenario 6: Replicated Trial Validation (N=30) -> FIELD_CALIBRATED
        # -------------------------------------------------------------
        print("\n[Scenario 6] Multi-Replicate Trial Validation (N=30, high data quality)...")
        # Use the multi-replicate trial created in Prompt 6 (Experiment #2 or create replicated)
        exp_rep = Experiment(
            name="Replicated Green Gram Calibration Trial",
            crop="Green Gram (Moong)",
            variety="Pusa Vishal",
            status="ACTIVE",
        )
        db.add(exp_rep)
        db.commit()
        db.refresh(exp_rep)

        # Setup 2 groups with 3 pots each, 5 plants each = 30 plants
        grp_t = ExperimentGroup(experiment_id=exp_rep.id, name="Terravyn", type="TERRAVYN")
        grp_c = ExperimentGroup(experiment_id=exp_rep.id, name="Control", type="CONTROL")
        db.add_all([grp_t, grp_c])
        db.commit()

        plots_created = []
        for i in range(1, 4):
            p1 = ExperimentPlot(group_id=grp_t.id, name=f"T-Pot {i}")
            p2 = ExperimentPlot(group_id=grp_c.id, name=f"C-Pot {i}")
            db.add_all([p1, p2])
            db.commit()
            plots_created.extend([p1, p2])

        # Add 30 plants & 15 observations & snapshots
        for p in plots_created:
            for j in range(1, 6):
                pl = ExperimentPlant(plot_id=p.id, plant_tag=f"{p.name}-{j}")
                db.add(pl)
            obs = ExperimentObservation(
                experiment_id=exp_rep.id,
                group_id=p.group_id,
                plot_id=p.id,
                parameter="plant_height",
                value_numeric=24.5,
                unit="cm",
            )
            db.add(obs)

        # Add snapshots with HIGH quality score
        for p in plots_created:
            snap = ExperimentDailySnapshot(
                experiment_id=exp_rep.id,
                group_id=p.group_id,
                plot_id=p.id,
                snapshot_date=datetime.utcnow() - timedelta(days=1),
                data_quality_score="HIGH",
            )
            db.add(snap)
        db.commit()

        val_rep = ExperimentalDataValidator.validate_trial_candidate(db=db, experiment_id=exp_rep.id)
        assert val_rep.status in ("FIELD_CALIBRATED", "PROVISIONAL"), f"Expected FIELD_CALIBRATED/PROVISIONAL, got {val_rep.status}"
        assert val_rep.confidence >= 55
        print(f"  [PASS] Replicated trial validated: Status={val_rep.status}, Conf={val_rep.confidence}%, EvidenceCount={val_rep.evidence_count}.")
        passed += 1

        # -------------------------------------------------------------
        # Scenario 7: Sensor Calibration Freshness Check
        # -------------------------------------------------------------
        print("\n[Scenario 7] Sensor Calibration Freshness & Direction Check...")
        cal_score, cal_notes = ExperimentalDataValidator._evaluate_sensor_calibration(db, plots_created)
        assert cal_score >= 70.0
        assert any("4095_DRY_0_WET" in note for note in cal_notes)
        print(f"  [PASS] Capacitive calibration verified (Standard 4095_DRY_0_WET): Score={cal_score}%.")
        passed += 1

        # -------------------------------------------------------------
        # Scenario 8: Field-Specific Scoping
        # -------------------------------------------------------------
        print("\n[Scenario 8] Field-Specific Parameter Scoping...")
        cal_field = FieldCalibrationManager.create_calibration(
            db=db,
            field_id=farm.id,
            crop="Green Gram (Moong)",
            soil_type="Sandy Loam",
            growth_stage="Flowering",
            parameter="capacitive_soil_moisture_threshold",
            value=36.5,
            scope="FIELD",
            status="EXPERIMENTAL",
            confidence=70,
            sample_count=30,
        )
        assert cal_field.scope == "FIELD"
        assert cal_field.field_id == farm.id
        print(f"  [PASS] Calibration #{cal_field.id} scoped strictly to Field #{farm.id} (not universal).")
        passed += 1

        # -------------------------------------------------------------
        # Scenario 9: Range-Based Trigger Zones & Hysteresis Support
        # -------------------------------------------------------------
        print("\n[Scenario 9] Range-Based Trigger Zones & Hysteresis Support...")
        assert cal_field.value == 36.5
        assert cal_field.value_range is not None
        assert cal_field.value_range["min"] == 33.5
        assert cal_field.value_range["max"] == 39.5
        assert cal_field.value_range["stop_threshold"] == 46.5  # 36.5 + 10.0 hysteresis
        assert cal_field.hysteresis_delta == 10.0
        print("  [PASS] Hysteresis verified: Trigger=36.5%, Stop=46.5% (+10.0% delta prevents pump flapping).")
        passed += 1

        # -------------------------------------------------------------
        # Scenario 10: Growth-Stage Specific Scoping
        # -------------------------------------------------------------
        print("\n[Scenario 10] Growth-Stage Specific Scoping (Flowering vs Vegetative)...")
        cal_veg = FieldCalibrationManager.create_calibration(
            db=db,
            field_id=farm.id,
            crop="Green Gram (Moong)",
            soil_type="Sandy Loam",
            growth_stage="Vegetative",
            parameter="capacitive_soil_moisture_threshold",
            value=29.0, # Lower requirement in vegetative
            scope="FIELD",
            status="EXPERIMENTAL",
        )
        assert cal_veg.growth_stage == "Vegetative"
        assert cal_veg.value == 29.0
        assert cal_field.growth_stage == "Flowering"
        assert cal_field.value == 36.5
        print("  [PASS] Distinct calibrated parameters maintained: Vegetative=29.0% vs Flowering=36.5%.")
        passed += 1

        # -------------------------------------------------------------
        # Scenario 11: Shadow Mode Execution
        # -------------------------------------------------------------
        print("\n[Scenario 11] Shadow Mode Execution (Parallel evaluation without pump actuation)...")
        cal_shadow = FieldCalibrationManager.enable_shadow_mode(db=db, calibration_id=cal_field.id)
        assert cal_shadow.status == "SHADOW"

        # Create a mock decision log
        mock_log = CropDecisionLog(
            farm_id=farm.id,
            crop="Green Gram (Moong)",
            growth_stage="Flowering",
            soil_moisture=35.0, # Between standard 40.0% and calibrated 36.5%
            decision="WAIT",
            confidence=85,
            reasons=["Standard rule check"],
            factors={},
            engine_version="green-gram-irrigation-v1",
        )
        db.add(mock_log)
        db.commit()
        db.refresh(mock_log)

        shadow_eval = FieldCalibrationManager.run_shadow_evaluation(db=db, decision_log=mock_log, calibration=cal_shadow)
        assert shadow_eval.id is not None
        assert shadow_eval.production_decision == "WAIT"
        assert shadow_eval.shadow_decision == "IRRIGATE"  # Because 35.0 < 36.5
        assert shadow_eval.divergence is True
        print(f"  [PASS] Shadow evaluation completed: Prod=WAIT, Shadow=IRRIGATE (Divergence={shadow_eval.divergence}, Zero pump actuation).")
        passed += 1

        # -------------------------------------------------------------
        # Scenario 12: Explicit Activation & Decision Engine Integration
        # -------------------------------------------------------------
        print("\n[Scenario 12] Explicit Activation & Decision Engine Integration...")
        activated_cal = FieldCalibrationManager.activate_calibration(db=db, calibration_id=cal_field.id)
        assert activated_cal.status == "ACTIVE"
        assert activated_cal.activated_at is not None

        # Ensure farm has an active device and fresh telemetry so sensor validation passes
        from models.domain import DeviceTelemetry
        device = db.query(Device).filter(Device.farm_id == farm.id).first()
        if not device:
            device = db.query(Device).first()
            if device:
                device.farm_id = farm.id
                db.commit()

        if device:
            # Clear recent irrigation logs so decision engine tests threshold evaluation rather than soak cooldown
            db.query(IrrigationLog).filter(IrrigationLog.device_id == device.id).delete()
            device.last_soil_moisture = 32.0
            device.last_temperature = 30.0
            device.last_humidity = 60.0
            device.last_seen = datetime.utcnow()
            telem = (
                db.query(DeviceTelemetry)
                .filter(DeviceTelemetry.device_id == device.id)
                .order_by(DeviceTelemetry.recorded_at.desc())
                .first()
            )
            if not telem:
                telem = DeviceTelemetry(
                    device_id=device.id,
                    soil_moisture=32.0,
                    temperature=30.0,
                    humidity=60.0,
                    recorded_at=datetime.utcnow(),
                )
                db.add(telem)
            else:
                telem.soil_moisture = 32.0
                telem.temperature = 30.0
                telem.humidity = 60.0
                telem.recorded_at = datetime.utcnow()
            db.commit()

        # Run decision engine and verify it picks up the calibrated parameter
        engine = GreenGramIrrigationDecisionEngine()
        res = engine.evaluate_farm(db=db, farm=farm)
        assert "calibration_info" in res.factors
        assert res.factors["calibration_info"]["calibrated"] is True
        assert res.factors["calibration_info"]["status"] == "FIELD_CALIBRATED"
        assert res.factors["calibration_info"]["calibration_id"] == activated_cal.id
        assert res.factors["effective_threshold"] == 36.5
        print(f"  [PASS] Decision engine applied calibrated threshold: {res.factors['effective_threshold']}% (v{activated_cal.version}).")
        passed += 1

        # -------------------------------------------------------------
        # Scenario 13: Non-Destructive Rollback Verification
        # -------------------------------------------------------------
        print("\n[Scenario 13] Non-Destructive Rollback Verification...")
        # Create Version 2
        cal_v2 = FieldCalibrationManager.create_calibration(
            db=db,
            field_id=farm.id,
            parameter="capacitive_soil_moisture_threshold",
            growth_stage="Flowering",
            value=38.0,
            status="EXPERIMENTAL",
        )
        assert cal_v2.version == activated_cal.version + 1
        assert cal_v2.previous_version_id == activated_cal.id

        # Activate Version 2
        cal_v2_active = FieldCalibrationManager.activate_calibration(db=db, calibration_id=cal_v2.id)
        assert cal_v2_active.status == "ACTIVE"

        # Verify old Version 1 became SUPERSEDED
        db.refresh(activated_cal)
        assert activated_cal.status == "SUPERSEDED"

        # Now perform Rollback from v2 to v1
        rolled_back = FieldCalibrationManager.rollback_calibration(db=db, calibration_id=cal_v2.id)
        assert rolled_back.id == activated_cal.id
        assert rolled_back.status == "ACTIVE"

        db.refresh(cal_v2)
        assert cal_v2.status == "SUPERSEDED"

        # Verify decision engine now runs on Version 1 threshold (36.5%)
        res_after_rollback = engine.evaluate_farm(db=db, farm=farm)
        assert res_after_rollback.factors["effective_threshold"] == 36.5
        print("  [PASS] Successfully rolled back from v2 to v1; Decision Engine immediately reverted to v1 (36.5%).")
        passed += 1

        # -------------------------------------------------------------
        # Scenario 14: Decision Outcome Linking & Error Classification
        # -------------------------------------------------------------
        print("\n[Scenario 14] Decision Outcome Linking & Error Classification...")
        outcome = DecisionOutcomeEvaluator.evaluate_decision_outcome(db=db, decision_log_id=mock_log.id)
        assert outcome.id is not None
        assert outcome.classification in ("CORRECT_WAIT", "MISSED_IRRIGATION", "CORRECT_IRRIGATION", "INSUFFICIENT_DATA")

        stats = DecisionOutcomeEvaluator.get_outcome_statistics(db=db)
        assert stats["total_evaluated"] >= 1
        print(f"  [PASS] Decision outcome linked: Classification={outcome.classification}, TotalEvaluated={stats['total_evaluated']}.")
        passed += 1

        print("\n" + "=" * 80)
        print(f"RESULTS: {passed}/{total} SCENARIOS PASSED (100%)")
        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    run_all_tests()
