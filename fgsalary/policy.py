"""Forward-looking simulation of the graduate wage floor.

The floor has been announced but is not in force, so its effect cannot be
estimated from data. This module applies it to the pre-policy salary
distribution under stated assumptions and reports what changes.

Wage compression rule
---------------------
Raising the floor to F squeezes the pay gap between graduates who used to earn
different amounts. Employers typically restore part of that gap. The rule here
blends two extremes for anyone earning below the ceiling C:

* no spillover: pay is max(w, F);
* full rank-preserving spillover: the old range [m, C] is squeezed evenly into
  [F, C], so pay is F + (w - m) (C - F) / (C - m), where m is the minimum wage
  before the policy.

alpha is the weight on the second: 0 means employers only meet the floor, 1
means they restore differentials in full. Pay at or above C is unchanged. The
rule is continuous and never reverses anyone's pay ranking.
"""
import numpy as np
import pandas as pd


def post_policy_wage(wage, floor, anchor, ceiling, alpha):
    wage = np.asarray(wage, dtype=float)
    floored = np.maximum(wage, floor)
    remapped = floor + (np.clip(wage, anchor, ceiling) - anchor) * (ceiling - floor) / (ceiling - anchor)
    blended = (1 - alpha) * floored + alpha * remapped
    return np.where(wage >= ceiling, wage, blended)


def employer_cost(wage, statutory):
    """Total cost of employment: pay plus the employer's statutory contributions."""
    rate = (
        statutory["epf_employer"] + statutory["socso_employer"]
        + statutory["eis_employer"] + statutory["hrd_levy"]
    )
    return np.asarray(wage, dtype=float) * (1 + rate)


def take_home(wage, statutory):
    """Pay after the employee's EPF, SOCSO and EIS. Income tax (PCB) is not deducted."""
    rate = statutory["epf_employee"] + statutory["socso_employee"] + statutory["eis_employee"]
    return np.asarray(wage, dtype=float) * (1 - rate)


def scenario_definitions(policy):
    """The scenarios reported. Each differs from the central case in one respect."""
    span = policy["compression_ceiling"] - policy["graduate_floor"]
    growth = (1 + policy["annual_wage_growth"]) ** policy["years_to_policy"]
    central = {
        "floor": policy["graduate_floor"],
        "ceiling": policy["compression_ceiling"],
        "alpha": policy["compression_alpha"],
        "coverage": 1.0,
        "growth": 1.0,
        "exclude_at_or_below": 0,
    }
    return [
        {"scenario": "A. Floor only, no spillover", **central, "alpha": 0.0,
         "description": f"RM{policy['graduate_floor']:,} floor, every employer complies, "
                        "nobody above the floor gets a raise"},
        {"scenario": "B. Central: floor with spillover", **central,
         "description": f"As A, plus employers restore {policy['compression_alpha']:.0%} of "
                        f"squeezed pay gaps up to RM{policy['compression_ceiling']:,}"},
        {"scenario": "C. Central with SME exemption", **central,
         "coverage": policy["sme_coverage_rate"],
         "description": f"As B, but only {policy['sme_coverage_rate']:.0%} of graduates work "
                        "for employers the floor applies to (assumed)"},
        {"scenario": "D. Central after wage growth", **central, "growth": growth,
         "description": f"As B, after {policy['annual_wage_growth']:.0%} a year of pay growth "
                        f"for {policy['years_to_policy']} years (2024 data to a 2027 start)"},
        {"scenario": "E. Minimum wage only", **central,
         "floor": policy["new_minimum_wage"],
         "ceiling": policy["new_minimum_wage"] + span,
         "description": f"Only the RM{policy['new_minimum_wage']:,} national minimum wage "
                        "applies to graduates; no separate graduate floor"},
        {"scenario": "F. Central, full-time jobs only", **central,
         "exclude_at_or_below": policy["likely_part_time_at_or_below"],
         "description": f"As B, but graduates reporting RM{policy['likely_part_time_at_or_below']:,} or less "
                        "(at or below the 2024 minimum wage, so probably not in full-time employment) "
                        "are treated as outside the floor"},
    ]


def simulate_scenario(salaries, definition, policy, statutory, seed):
    """Apply one scenario and return (pre-policy pay, post-policy pay)."""
    before = np.asarray(salaries, dtype=float) * definition["growth"]
    after = post_policy_wage(
        before, definition["floor"], policy["current_minimum_wage"],
        definition["ceiling"], definition["alpha"],
    )
    if definition["coverage"] < 1:
        covered = np.random.default_rng(seed).random(len(before)) < definition["coverage"]
        after = np.where(covered, after, before)
    after = np.where(before > definition["exclude_at_or_below"], after, before)
    return before, after


def summarise(before, after, definition, policy, statutory):
    raise_amount = after - before
    raised = raise_amount > 1e-9
    below_floor = before < definition["floor"]
    mid_tier = (before >= policy["mid_tier_low"]) & (before <= policy["mid_tier_high"])
    cost_before = employer_cost(before, statutory).sum()
    cost_after = employer_cost(after, statutory).sum()

    def mean_or_zero(values):
        return float(values.mean()) if len(values) else 0.0

    return {
        "scenario": definition["scenario"],
        "description": definition["description"],
        "floor": definition["floor"],
        "share_below_floor": float(below_floor.mean()),
        "share_receiving_raise": float(raised.mean()),
        "mean_raise_if_raised": mean_or_zero(raise_amount[raised]),
        "median_salary_before": float(np.median(before)),
        "median_salary_after": float(np.median(after)),
        "wage_bill_increase": float(after.sum() / before.sum() - 1),
        "employer_cost_increase_per_1000_grads": float((cost_after - cost_before) / len(before) * 1000),
        "mid_tier_share_of_graduates": float(mid_tier.mean()),
        "mid_tier_share_raised": mean_or_zero(raised[mid_tier].astype(float)),
        "mid_tier_mean_raise": mean_or_zero(raise_amount[mid_tier]),
        "mid_tier_mean_raise_pct": mean_or_zero(raise_amount[mid_tier] / before[mid_tier]),
        "p50_p10_ratio_before": float(np.percentile(before, 50) / np.percentile(before, 10)),
        "p50_p10_ratio_after": float(np.percentile(after, 50) / np.percentile(after, 10)),
    }


def run_scenarios(salaries, parameters):
    policy, statutory = parameters["policy"], parameters["statutory"]
    rows = []
    for definition in scenario_definitions(policy):
        before, after = simulate_scenario(salaries, definition, policy, statutory, parameters["seed"])
        rows.append(summarise(before, after, definition, policy, statutory))
    return pd.DataFrame(rows)


def spillover_profile(parameters, step=100):
    """Raise at each pre-policy salary under the central case, for the workbook and report."""
    policy = parameters["policy"]
    wages = np.arange(policy["current_minimum_wage"], policy["compression_ceiling"] + step, step)
    after = post_policy_wage(
        wages, policy["graduate_floor"], policy["current_minimum_wage"],
        policy["compression_ceiling"], policy["compression_alpha"],
    )
    floor_only = np.maximum(wages, policy["graduate_floor"])
    return pd.DataFrame({
        "salary_before": wages,
        "salary_after": after,
        "raise_from_floor": floor_only - wages,
        "raise_from_spillover": after - floor_only,
        "total_raise": after - wages,
    })
