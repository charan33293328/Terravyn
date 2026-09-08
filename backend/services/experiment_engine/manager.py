"""
Terravyn Experiment Engine: Lifecycle & Hierarchy Manager
Manages experiments, groups (TERRAVYN vs CONTROL), replicate plots/pots, plant units, and agronomic baseline.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from models.domain import (
    Experiment,
    ExperimentGroup,
    ExperimentPlot,
    ExperimentPlant,
    ExperimentBaseline,
    ExperimentEvent,
)


class ExperimentManager:
    """Manages the creation, hierarchy, and status updates of agricultural experiments."""

    @classmethod
    def create_experiment(
        cls,
        db: Session,
        name: str,
        crop: str = "Green Gram (Moong)",
        scientific_name: str = "Vigna radiata",
        variety: Optional[str] = "Pusa Vishal",
        start_date: Optional[datetime] = None,
        expected_end_date: Optional[datetime] = None,
        location: Optional[str] = None,
        protocol: Optional[Dict[str, Any]] = None,
        created_by: Optional[int] = None,
    ) -> Experiment:
        """Initializes a new experiment trial."""
        exp = Experiment(
            name=name,
            crop=crop,
            scientific_name=scientific_name,
            variety=variety,
            start_date=start_date or datetime.utcnow(),
            expected_end_date=expected_end_date,
            location=location,
            protocol=protocol or {},
            status="ACTIVE",
            created_by=created_by,
        )
        db.add(exp)
        db.commit()
        db.refresh(exp)

        # Log creation event
        cls.log_event(
            db=db,
            experiment_id=exp.id,
            event_type="EXPERIMENT_CREATED",
            notes=f"Experiment '{name}' initialized for variety '{variety}'.",
        )
        return exp

    @classmethod
    def setup_default_trial_hierarchy(
        cls,
        db: Session,
        experiment_id: int,
        terravyn_device_id: Optional[int] = None,
        control_device_id: Optional[int] = None,
        pots_per_group: int = 3,
        plants_per_pot: int = 5,
        sowing_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Sets up the standard 2-group comparative trial structure:
        - Group: TERRAVYN (Pots 1..N)
        - Group: CONTROL (Pots 1..N)
        With specified individual plant tags (e.g., T-P1-01..05, C-P1-01..05).
        """
        sow_dt = sowing_date or datetime.utcnow()

        # 1. Create TERRAVYN group
        grp_terravyn = ExperimentGroup(
            experiment_id=experiment_id,
            name="Terravyn Guided",
            type="TERRAVYN",
            description="Replicates managed with Terravyn advisory and scientific thresholds.",
        )
        # 2. Create CONTROL group
        grp_control = ExperimentGroup(
            experiment_id=experiment_id,
            name="Control Practice",
            type="CONTROL",
            description="Replicates managed according to conventional farmer calendar practice.",
        )
        db.add_all([grp_terravyn, grp_control])
        db.commit()
        db.refresh(grp_terravyn)
        db.refresh(grp_control)

        created_plots = []
        created_plants = []

        # Populate pots and plants for Terravyn
        for pot_idx in range(1, pots_per_group + 1):
            plot = ExperimentPlot(
                group_id=grp_terravyn.id,
                name=f"Terravyn Pot {pot_idx}",
                plot_type="POT",
                device_id=terravyn_device_id,
                soil_profile={"soil_type": "sandy_loam", "replicate_idx": pot_idx},
            )
            db.add(plot)
            db.commit()
            db.refresh(plot)
            created_plots.append(plot)

            for plant_idx in range(1, plants_per_pot + 1):
                plant = ExperimentPlant(
                    plot_id=plot.id,
                    plant_tag=f"T-P{pot_idx}-{plant_idx:02d}",
                    sowing_date=sow_dt,
                    status="ALIVE",
                )
                db.add(plant)
                created_plants.append(plant)

        # Populate pots and plants for Control
        for pot_idx in range(1, pots_per_group + 1):
            plot = ExperimentPlot(
                group_id=grp_control.id,
                name=f"Control Pot {pot_idx}",
                plot_type="POT",
                device_id=control_device_id,
                soil_profile={"soil_type": "sandy_loam", "replicate_idx": pot_idx},
            )
            db.add(plot)
            db.commit()
            db.refresh(plot)
            created_plots.append(plot)

            for plant_idx in range(1, plants_per_pot + 1):
                plant = ExperimentPlant(
                    plot_id=plot.id,
                    plant_tag=f"C-P{pot_idx}-{plant_idx:02d}",
                    sowing_date=sow_dt,
                    status="ALIVE",
                )
                db.add(plant)
                created_plants.append(plant)

        db.commit()

        cls.log_event(
            db=db,
            experiment_id=experiment_id,
            event_type="TRIAL_STRUCTURE_SETUP",
            notes=f"Setup 2 groups with {pots_per_group} pots each and {plants_per_pot} plants per pot.",
        )

        return {
            "groups": [grp_terravyn.id, grp_control.id],
            "total_plots": len(created_plots),
            "total_plants": len(created_plants),
        }

    @classmethod
    def set_baseline(
        cls,
        db: Session,
        experiment_id: int,
        baseline_data: Dict[str, Any],
    ) -> ExperimentBaseline:
        """Records or updates pre-sowing soil chemistry, seed provenance, and plot baseline."""
        existing = (
            db.query(ExperimentBaseline)
            .filter(ExperimentBaseline.experiment_id == experiment_id)
            .first()
        )
        if existing:
            for k, v in baseline_data.items():
                if hasattr(existing, k) and v is not None:
                    setattr(existing, k, v)
            db.commit()
            db.refresh(existing)
            return existing

        baseline = ExperimentBaseline(
            experiment_id=experiment_id,
            soil_type=baseline_data.get("soil_type", "sandy_loam"),
            soil_ph=baseline_data.get("soil_ph"),
            soil_ec=baseline_data.get("soil_ec"),
            organic_carbon=baseline_data.get("organic_carbon"),
            available_n=baseline_data.get("available_n"),
            available_p=baseline_data.get("available_p"),
            available_k=baseline_data.get("available_k"),
            seed_source=baseline_data.get("seed_source"),
            sowing_date=baseline_data.get("sowing_date") or datetime.utcnow(),
            seed_quantity=baseline_data.get("seed_quantity"),
            planting_depth_cm=baseline_data.get("planting_depth_cm", 3.0),
            spacing_cm=baseline_data.get("spacing_cm", "30x10"),
            irrigation_source=baseline_data.get("irrigation_source"),
            irrigation_method=baseline_data.get("irrigation_method", "pot_drip"),
            fertilizer_baseline=baseline_data.get("fertilizer_baseline"),
            latitude=baseline_data.get("latitude"),
            longitude=baseline_data.get("longitude"),
            elevation_m=baseline_data.get("elevation_m"),
        )
        db.add(baseline)
        db.commit()
        db.refresh(baseline)

        cls.log_event(
            db=db,
            experiment_id=experiment_id,
            event_type="BASELINE_RECORDED",
            notes=f"Recorded baseline soil profile and seed provenance for experiment #{experiment_id}.",
        )
        return baseline

    @classmethod
    def get_experiment_hierarchy(cls, db: Session, experiment_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves full nested hierarchy of an experiment: groups, plots/pots, plants, baseline."""
        exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not exp:
            return None

        baseline = (
            db.query(ExperimentBaseline)
            .filter(ExperimentBaseline.experiment_id == experiment_id)
            .first()
        )

        groups = db.query(ExperimentGroup).filter(ExperimentGroup.experiment_id == experiment_id).all()
        group_list = []
        for g in groups:
            plots = db.query(ExperimentPlot).filter(ExperimentPlot.group_id == g.id).all()
            plot_list = []
            for p in plots:
                plants = db.query(ExperimentPlant).filter(ExperimentPlant.plot_id == p.id).all()
                plot_list.append({
                    "id": p.id,
                    "name": p.name,
                    "plot_type": p.plot_type,
                    "device_id": p.device_id,
                    "soil_profile": p.soil_profile,
                    "plants": [
                        {
                            "id": pl.id,
                            "plant_tag": pl.plant_tag,
                            "sowing_date": pl.sowing_date.isoformat() if pl.sowing_date else None,
                            "germination_date": pl.germination_date.isoformat() if pl.germination_date else None,
                            "status": pl.status,
                            "notes": pl.notes,
                        }
                        for pl in plants
                    ],
                })
            group_list.append({
                "id": g.id,
                "name": g.name,
                "type": g.type,
                "description": g.description,
                "plots": plot_list,
            })

        return {
            "id": exp.id,
            "name": exp.name,
            "crop": exp.crop,
            "scientific_name": exp.scientific_name,
            "variety": exp.variety,
            "status": exp.status,
            "start_date": exp.start_date.isoformat() if exp.start_date else None,
            "expected_end_date": exp.expected_end_date.isoformat() if exp.expected_end_date else None,
            "location": exp.location,
            "protocol": exp.protocol,
            "baseline": {
                "soil_type": baseline.soil_type if baseline else None,
                "soil_ph": baseline.soil_ph if baseline else None,
                "soil_ec": baseline.soil_ec if baseline else None,
                "organic_carbon": baseline.organic_carbon if baseline else None,
                "available_n": baseline.available_n if baseline else None,
                "available_p": baseline.available_p if baseline else None,
                "available_k": baseline.available_k if baseline else None,
                "seed_source": baseline.seed_source if baseline else None,
                "sowing_date": baseline.sowing_date.isoformat() if baseline and baseline.sowing_date else None,
                "planting_depth_cm": baseline.planting_depth_cm if baseline else None,
                "spacing_cm": baseline.spacing_cm if baseline else None,
                "irrigation_source": baseline.irrigation_source if baseline else None,
                "irrigation_method": baseline.irrigation_method if baseline else None,
            } if baseline else None,
            "groups": group_list,
        }

    @classmethod
    def log_event(
        cls,
        db: Session,
        experiment_id: int,
        event_type: str,
        group_id: Optional[int] = None,
        plot_id: Optional[int] = None,
        actor: str = "system",
        notes: Optional[str] = None,
    ) -> ExperimentEvent:
        """Logs an audit or agronomic milestone event."""
        event = ExperimentEvent(
            experiment_id=experiment_id,
            group_id=group_id,
            plot_id=plot_id,
            timestamp=datetime.utcnow(),
            event_type=event_type,
            actor=actor,
            notes=notes,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @classmethod
    def complete_experiment(
        cls,
        db: Session,
        experiment_id: int,
        notes: Optional[str] = None,
    ) -> Optional[Experiment]:
        """Transitions an experiment to COMPLETED status and logs completion."""
        exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not exp:
            return None
        exp.status = "COMPLETED"
        exp.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(exp)

        cls.log_event(
            db=db,
            experiment_id=exp.id,
            event_type="EXPERIMENT_COMPLETED",
            notes=notes or "Experiment concluded. Final trial analysis ready.",
        )
        return exp
