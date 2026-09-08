"""
Terravyn Research Engine: Research Question Generator
Synthesizes precise, narrowly scoped agronomic research queries from SituationFingerprints.
"""
from typing import Optional
from .fingerprint import SituationFingerprint


class ResearchQuestionGenerator:
    BOTANICAL_NAMES = {
        "green_gram": "Vigna radiata",
        "mung_bean": "Vigna radiata",
        "black_gram": "Vigna mungo",
        "chickpea": "Cicer arietinum",
        "pigeonpea": "Cajanus cajan"
    }

    def generate_question(
        self,
        fingerprint: SituationFingerprint,
        target_parameter: Optional[str] = None
    ) -> str:
        """
        Synthesize a scientifically grounded, targeted research query.
        Example: 'Vigna radiata flowering stage water stress irrigation threshold sandy loam high temperature'
        """
        botanical = self.BOTANICAL_NAMES.get(fingerprint.crop.lower(), fingerprint.crop)
        stage = fingerprint.growth_stage.replace("_", " ")
        soil = fingerprint.soil_type.replace("_", " ")
        problem = fingerprint.problem_type.replace("_", " ")

        query_components = [botanical]

        if fingerprint.variety:
            query_components.append(f"variety {fingerprint.variety}")

        query_components.append(f"{stage} stage")
        query_components.append(f"{soil} soil")
        query_components.append(problem)

        if fingerprint.temperature_state in ["high", "extreme_heat"]:
            query_components.append("heat stress high temperature")
        
        if fingerprint.eto_state == "high":
            query_components.append("high evaporative demand ET0")

        if fingerprint.rain_forecast == "significant":
            query_components.append("rainfall forecast suspension")

        if target_parameter:
            query_components.append(f"parameter {target_parameter}")
        else:
            query_components.append("irrigation threshold water requirement")

        return " ".join(query_components)
