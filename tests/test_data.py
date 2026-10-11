import copy

import numpy as np
import pytest

from fgsalary import config, data

# The overall first-degree row printed in SKPG 2024, Jadual 4o.
PUBLISHED_OVERALL = [6.9, 6.2, 17.5, 19.1, 16.6, 22.7, 6.6, 3.8, 0.6]
PUBLISHED_RESPONDENTS = 109_414


def test_field_rows_add_up_to_the_published_total(skpg):
    assert skpg["respondents"].sum() == PUBLISHED_RESPONDENTS


def test_field_rows_reproduce_the_published_overall_distribution(skpg):
    # A transcription slip in any field row would move the weighted total
    # away from the row the report prints. Rounding to 0.1 allows 0.1 points.
    shares = data.published_band_shares(skpg) * 100
    assert shares == pytest.approx(PUBLISHED_OVERALL, abs=0.1)


def test_each_field_row_sums_to_100_percent(skpg):
    assert skpg[data.BAND_COLUMNS].sum(axis=1).to_numpy() == pytest.approx(100, abs=0.3)


def test_half_of_first_degree_graduates_earn_the_floor_or_less(skpg, parameters):
    simulation = parameters["simulation"]
    share = data.published_share_at_or_below(
        skpg, 2500, simulation["bottom_band_floor"], simulation["top_band_cap"])
    assert share == pytest.approx(0.497, abs=0.002)


def test_share_at_or_below_interpolates_inside_a_band(skpg, parameters):
    simulation = parameters["simulation"]
    bounds = (simulation["bottom_band_floor"], simulation["top_band_cap"])
    at_2000 = data.published_share_at_or_below(skpg, 2000, *bounds)
    at_2250 = data.published_share_at_or_below(skpg, 2250, *bounds)
    at_2500 = data.published_share_at_or_below(skpg, 2500, *bounds)
    assert at_2000 < at_2250 < at_2500
    assert at_2250 == pytest.approx((at_2000 + at_2500) / 2, abs=0.001)


def test_largest_remainder_keeps_the_total_and_the_proportions():
    counts = data.largest_remainder([50, 30, 20], 7)
    assert counts.sum() == 7
    assert list(counts) == [4, 2, 1]
    assert data.largest_remainder([1, 1, 1], 100).sum() == 100


def test_sample_has_the_configured_size_and_valid_values(sample, parameters):
    simulation = parameters["simulation"]
    assert len(sample) == parameters["sample_size"]
    assert sample["graduate_id"].is_unique
    assert sample["cgpa"].between(simulation["cgpa_min"], simulation["cgpa_max"]).all()
    assert set(sample["intern_months"]) == {3, 6, 9}
    assert set(sample["stem"]) == {0, 1}
    assert set(sample["klang_valley"]) == {0, 1}
    assert sample["salary"].between(simulation["bottom_band_floor"], simulation["top_band_cap"]).all()
    assert not sample.isna().any().any()


def test_sample_is_reproducible(parameters, skpg, sample):
    assert data.simulate(parameters, skpg).equals(sample)


def test_sample_salary_bands_match_the_published_ones(sample, skpg):
    simulated = data.sample_band_shares(sample["salary"])
    assert simulated.sum() == pytest.approx(1)
    assert simulated == pytest.approx(data.published_band_shares(skpg), abs=0.01)


def test_sample_field_mix_matches_the_respondents(sample, skpg):
    expected = skpg.set_index("field_en")["respondents"] / skpg["respondents"].sum()
    actual = sample["field"].value_counts(normalize=True)
    for field, share in actual.items():
        assert share == pytest.approx(expected[field], abs=0.001)


def test_assumptions_never_change_the_salaries_themselves(parameters, skpg, sample):
    # The assumed weights decide WHO gets which salary inside a field. The set
    # of salaries in each field comes from the published bands and must not move.
    altered = copy.deepcopy(parameters)
    altered["simulation"].update(weight_cgpa=0.05, weight_intern=0.5, weight_klang_valley=0.0)
    other = data.simulate(altered, skpg)
    for field in sample["field"].unique():
        original = np.sort(sample.loc[sample["field"] == field, "salary"].to_numpy())
        changed = np.sort(other.loc[other["field"] == field, "salary"].to_numpy())
        assert np.array_equal(original, changed)


def test_invalid_parameters_are_rejected(parameters):
    broken = copy.deepcopy(parameters)
    broken["policy"]["compression_ceiling"] = broken["policy"]["graduate_floor"]
    with pytest.raises(ValueError):
        config.validate(broken)

    broken = copy.deepcopy(parameters)
    broken["simulation"]["weight_cgpa"] = 0.9
    with pytest.raises(ValueError):
        config.validate(broken)
