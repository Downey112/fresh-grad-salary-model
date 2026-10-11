"""Project paths and the parameter file."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARAMETERS_PATH = ROOT / "config" / "parameters.json"
SKPG_PATH = ROOT / "data" / "skpg_2024_first_degree_income_by_field.csv"
SAMPLE_PATH = ROOT / "data" / "simulated_graduates.csv"
OUTPUT_DIR = ROOT / "outputs"
WORKBOOK_NAME = "FreshGrad_Salary_Regression_Model.xlsx"


def load_parameters(path=PARAMETERS_PATH):
    with open(path, encoding="utf-8") as handle:
        parameters = json.load(handle)
    validate(parameters)
    return parameters


def validate(parameters):
    policy = parameters["policy"]
    if not policy["current_minimum_wage"] < policy["graduate_floor"] < policy["compression_ceiling"]:
        raise ValueError(
            "policy needs current_minimum_wage < graduate_floor < compression_ceiling"
        )
    if not policy["current_minimum_wage"] < policy["new_minimum_wage"]:
        raise ValueError("policy needs current_minimum_wage < new_minimum_wage")
    if not 0 <= policy["compression_alpha"] <= 1:
        raise ValueError("compression_alpha must be between 0 and 1")
    if not 0 <= policy["sme_coverage_rate"] <= 1:
        raise ValueError("sme_coverage_rate must be between 0 and 1")

    simulation = parameters["simulation"]
    probabilities = simulation["intern_months_probabilities"].values()
    if abs(sum(probabilities) - 1) > 1e-9:
        raise ValueError("intern_months_probabilities must sum to 1")
    explained = (
        (simulation["weight_cgpa"] * simulation["stem_cgpa_multiplier"]) ** 2
        + simulation["weight_intern"] ** 2
        + simulation["weight_klang_valley"] ** 2
    )
    if explained >= 1:
        raise ValueError("simulation weights leave no room for unexplained variation")
