"""
Terravyn Validation Engine: Multi-Dimensional Confidence Scorer
Evaluates evidence across 10 scientific dimensions:
1. Source Quality
2. Applicability
3. Repeatability
4. Sample Size
5. Measurement Quality
6. Experimental Design
7. Consistency
8. Confounding Risk
9. Temporal Consistency
10. Environmental Context

Produces explainable confidence ratings and actionable recommendations without pretending to be a pure probability.
"""
from typing import Dict, Any, List, Tuple


class ValidationConfidenceScorer:
    """Computes explainable, multi-dimensional scientific confidence."""

    @classmethod
    def score_dimensions(
        cls,
        source_quality: float = 50.0,
        applicability: float = 50.0,
        repeatability: float = 50.0,
        sample_size: float = 50.0,
        measurement_quality: float = 50.0,
        experimental_design: float = 50.0,
        consistency: float = 50.0,
        confounding_risk: float = 50.0,
        temporal_consistency: float = 50.0,
        environmental_context: float = 50.0,
    ) -> Dict[str, float]:
        """Clamps and records the 10 dimensional scores (0-100 scale)."""
        dims = {
            "source_quality": max(0.0, min(100.0, float(source_quality))),
            "applicability": max(0.0, min(100.0, float(applicability))),
            "repeatability": max(0.0, min(100.0, float(repeatability))),
            "sample_size": max(0.0, min(100.0, float(sample_size))),
            "measurement_quality": max(0.0, min(100.0, float(measurement_quality))),
            "experimental_design": max(0.0, min(100.0, float(experimental_design))),
            "consistency": max(0.0, min(100.0, float(consistency))),
            "confounding_risk": max(0.0, min(100.0, float(confounding_risk))),
            "temporal_consistency": max(0.0, min(100.0, float(temporal_consistency))),
            "environmental_context": max(0.0, min(100.0, float(environmental_context))),
        }
        return dims

    @classmethod
    def compute_overall_confidence(
        cls,
        dimensions: Dict[str, float],
        is_experimental: bool = False,
    ) -> Tuple[int, str, List[str], List[str], str]:
        """
        Computes weighted composite score and determines:
        - confidence (0-100)
        - confidence_level ("LOW", "MEDIUM", "HIGH")
        - reasons (list of positive/explanatory findings)
        - limitations (list of caveats/data gaps)
        - recommended_next_step
        """
        reasons = []
        limitations = []

        if is_experimental:
            # Empirical trial weighting
            weights = {
                "sample_size": 0.15,
                "measurement_quality": 0.15,
                "repeatability": 0.15,
                "consistency": 0.15,
                "confounding_risk": 0.10,
                "experimental_design": 0.10,
                "applicability": 0.10,
                "temporal_consistency": 0.05,
                "environmental_context": 0.05,
                "source_quality": 0.00,
            }
        else:
            # External scientific literature weighting
            weights = {
                "source_quality": 0.25,
                "applicability": 0.20,
                "consistency": 0.15,
                "environmental_context": 0.10,
                "sample_size": 0.10,
                "experimental_design": 0.05,
                "repeatability": 0.05,
                "temporal_consistency": 0.05,
                "measurement_quality": 0.05,
                "confounding_risk": 0.00,
            }

        score = 0.0
        for dim, weight in weights.items():
            dim_val = dimensions.get(dim, 50.0)
            score += dim_val * weight

        confidence = int(round(max(0.0, min(100.0, score))))

        # If source quality is low (Tier 4 / unsourced), cap overall confidence
        if not is_experimental and dimensions.get("source_quality", 0) <= 30:
            confidence = min(confidence, int(dimensions.get("source_quality", 0) * 1.5))

        # Categorical level
        if confidence >= 75:
            confidence_level = "HIGH"
        elif confidence >= 50:
            confidence_level = "MEDIUM"
        else:
            confidence_level = "LOW"

        # Formulate explainable reasons & limitations
        if dimensions.get("source_quality", 0) >= 80:
            reasons.append("Peer-reviewed Tier 1 institutional research (ICAR/IIPR/FAO standards).")
        elif dimensions.get("source_quality", 0) < 45:
            limitations.append("Source quality is below peer-reviewed scientific threshold.")

        if dimensions.get("sample_size", 0) >= 70:
            reasons.append("Sample size exceeds statistical minimum for replicate observations.")
        elif dimensions.get("sample_size", 0) <= 25:
            limitations.append("Small sample size (insufficient independent plant/plot replicates).")

        if dimensions.get("measurement_quality", 0) >= 80:
            reasons.append("Sensor probes calibrated with fresh 2-point 4095=dry/1400=wet references.")
        elif dimensions.get("measurement_quality", 0) < 50:
            limitations.append("Probe calibration unverified or telemetry completeness degraded.")

        if dimensions.get("consistency", 0) >= 75:
            reasons.append("Observed relationship remained consistent across multiple evaluation cycles.")
        elif dimensions.get("consistency", 0) < 50:
            limitations.append("High variance or conflicting observations observed across cycles.")

        if dimensions.get("applicability", 0) < 60:
            limitations.append("Soil, variety, or microclimate conditions diverge from field situation.")

        # Determine Recommended Next Step
        if is_experimental:
            if dimensions.get("sample_size", 0) <= 25:
                # Single observation guard!
                recommended_next_step = "KEEP_EXPERIMENTAL"
                limitations.append("Single or preliminary observation cannot be calibrated yet.")
            elif confidence >= 75 and dimensions.get("measurement_quality", 0) >= 75:
                recommended_next_step = "SHADOW_TEST"
            elif confidence >= 50:
                recommended_next_step = "PROMOTE_TO_PROVISIONAL"
            else:
                recommended_next_step = "REVIEW_REQUIRED"
        else:
            if dimensions.get("source_quality", 0) < 40:
                recommended_next_step = "REJECT" if dimensions.get("source_quality", 0) <= 25 else "REVIEW_REQUIRED"
            elif confidence >= 80 and dimensions.get("applicability", 0) >= 70:
                recommended_next_step = "PROMOTE_TO_VALIDATED"
            elif confidence >= 60:
                recommended_next_step = "PROMOTE_TO_PROVISIONAL"
            elif confidence < 40:
                recommended_next_step = "REJECT"
            else:
                recommended_next_step = "REVIEW_REQUIRED"

        return confidence, confidence_level, reasons, limitations, recommended_next_step
