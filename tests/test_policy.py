import numpy as np
import pytest

from fgsalary import policy

FLOOR, ANCHOR, CEILING = 2500, 1700, 3200


def after(wage, alpha=0.25):
    return policy.post_policy_wage(wage, FLOOR, ANCHOR, CEILING, alpha)


def test_no_spillover_is_just_the_floor():
    wages = np.array([800, 1700, 2499, 2500, 2900, 3200, 6000])
    assert after(wages, alpha=0) == pytest.approx(np.maximum(wages, FLOOR))


def test_full_spillover_squeezes_the_old_range_evenly():
    # [1700, 3200] maps onto [2500, 3200]: the midpoint 2450 lands on 2850.
    assert after(1700, alpha=1) == pytest.approx(2500)
    assert after(2450, alpha=1) == pytest.approx(2850)
    assert after(3200, alpha=1) == pytest.approx(3200)


def test_worked_example_at_the_floor():
    # Someone already on RM2,500: remapped pay is 2500 + 800 * 700 / 1500 = 2873.33,
    # and a quarter of that gap is restored.
    assert after(2500) == pytest.approx(0.75 * 2500 + 0.25 * 2873.3333)


def test_nobody_ends_up_below_the_floor_or_worse_off():
    wages = np.linspace(500, 15000, 2000)
    result = after(wages)
    assert (result >= FLOOR - 1e-9).all()
    assert (result >= wages - 1e-9).all()


def test_pay_at_or_above_the_ceiling_is_untouched():
    wages = np.array([3200, 3201, 5000, 12000])
    assert after(wages) == pytest.approx(wages)


def test_ranking_is_preserved_and_there_are_no_jumps():
    wages = np.arange(500, 4000, 1.0)
    result = after(wages)
    steps = np.diff(result)
    assert (steps >= -1e-9).all()
    assert steps.max() <= 1 + 1e-9


def test_statutory_costs_use_the_configured_rates(parameters):
    statutory = parameters["statutory"]
    assert policy.employer_cost(1000, statutory) == pytest.approx(1159.5)
    assert policy.take_home(1000, statutory) == pytest.approx(883)


def test_scenarios_behave_as_described(sample, parameters):
    scenarios = policy.run_scenarios(sample["salary"], parameters).set_index("scenario")
    floor_only = scenarios.loc["A. Floor only, no spillover"]
    central = scenarios.loc["B. Central: floor with spillover"]
    exempt = scenarios.loc["C. Central with SME exemption"]
    grown = scenarios.loc["D. Central after wage growth"]
    minimum_only = scenarios.loc["E. Minimum wage only"]
    full_time = scenarios.loc["F. Central, full-time jobs only"]

    # Without spillover only graduates below the floor are raised.
    assert floor_only["share_receiving_raise"] == pytest.approx(floor_only["share_below_floor"])
    assert floor_only["mid_tier_share_raised"] == 0
    # Spillover reaches more people and costs more.
    assert central["share_receiving_raise"] > floor_only["share_receiving_raise"]
    assert central["wage_bill_increase"] > floor_only["wage_bill_increase"]
    assert central["mid_tier_mean_raise"] > 0
    # Exemptions and prior wage growth both shrink the effect.
    assert exempt["wage_bill_increase"] < central["wage_bill_increase"]
    assert grown["share_below_floor"] < central["share_below_floor"]
    # A RM2,000 floor binds for fewer graduates than a RM2,500 one.
    assert minimum_only["share_below_floor"] < central["share_below_floor"]
    # Leaving out the lowest earners removes the largest raises.
    assert full_time["wage_bill_increase"] < central["wage_bill_increase"]
    assert full_time["share_receiving_raise"] < central["share_receiving_raise"]
    # The floor compresses pay at the bottom.
    assert central["p50_p10_ratio_after"] < central["p50_p10_ratio_before"]


def test_spillover_profile_adds_up(parameters):
    profile = policy.spillover_profile(parameters)
    assert (profile["raise_from_floor"] + profile["raise_from_spillover"]).to_numpy() == pytest.approx(
        profile["total_raise"].to_numpy())
    assert profile["total_raise"].iloc[-1] == pytest.approx(0)
    assert (profile["raise_from_spillover"] >= -1e-9).all()
