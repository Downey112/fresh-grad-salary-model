"""Load the published SKPG income bands and build a sample calibrated to them.

What is real and what is assumed:

* Field of study, the STEM share and every salary are drawn from the published
  SKPG 2024 band percentages, field by field, so the sample's salary
  distribution within each field reproduces the report's.
* CGPA, internship length and Klang Valley location are not published with
  income. They are simulated, and how strongly each one relates to salary is
  an assumption (the ``weight_*`` parameters).
"""
import math

import numpy as np
import pandas as pd
from scipy import stats

from . import config

# (column in the SKPG file, lower bound, upper bound) in RM per month. None
# marks an open end, which the simulation closes with an assumed bound.
BANDS = [
    ("pct_le_1000", None, 1000),
    ("pct_1001_1500", 1001, 1500),
    ("pct_1501_2000", 1501, 2000),
    ("pct_2001_2500", 2001, 2500),
    ("pct_2501_3000", 2501, 3000),
    ("pct_3001_4000", 3001, 4000),
    ("pct_4001_5000", 4001, 5000),
    ("pct_5001_10000", 5001, 10000),
    ("pct_gt_10000", 10001, None),
]
BAND_COLUMNS = [name for name, _, _ in BANDS]
BAND_LABELS = [
    "RM1,000 and below",
    "RM1,001 - RM1,500",
    "RM1,501 - RM2,000",
    "RM2,001 - RM2,500",
    "RM2,501 - RM3,000",
    "RM3,001 - RM4,000",
    "RM4,001 - RM5,000",
    "RM5,001 - RM10,000",
    "More than RM10,000",
]


def load_skpg(path=config.SKPG_PATH):
    return pd.read_csv(path)


def published_band_shares(skpg):
    """Share of all first-degree respondents in each band, as fractions summing to 1."""
    counts = skpg[BAND_COLUMNS].multiply(skpg["respondents"], axis=0).sum()
    return (counts / counts.sum()).to_numpy()


def published_share_at_or_below(skpg, amount, bottom_floor, top_cap):
    """Share of respondents earning ``amount`` or less, straight from the bands.

    Exact when ``amount`` is a band edge (RM2,500 is). Otherwise the band that
    contains it is split in proportion, which assumes salaries are spread
    evenly inside that band.
    """
    total = 0.0
    for share, (_, low, high) in zip(published_band_shares(skpg), BANDS):
        low = bottom_floor if low is None else low
        high = top_cap if high is None else high
        if amount >= high:
            total += share
        elif amount >= low:
            total += share * (amount - low + 1) / (high - low + 1)
    return total


def largest_remainder(weights, total):
    """Split ``total`` into whole numbers in proportion to ``weights``."""
    weights = np.asarray(weights, dtype=float)
    exact = weights / weights.sum() * total
    counts = np.floor(exact).astype(int)
    shortfall = total - counts.sum()
    order = np.argsort(-(exact - counts), kind="stable")
    counts[order[:shortfall]] += 1
    return counts


def draw_salaries(band_counts, simulation, rng):
    """Salaries for one field: the given number per band, spread evenly inside it."""
    step = simulation["salary_rounding"]
    salaries = []
    for count, (_, low, high) in zip(band_counts, BANDS):
        low = simulation["bottom_band_floor"] if low is None else low
        high = simulation["top_band_cap"] if high is None else high
        first, last = math.ceil(low / step), math.floor(high / step)
        salaries.append(rng.integers(first, last + 1, size=count) * step)
    return np.concatenate(salaries).astype(float)


def standardise(values):
    values = np.asarray(values, dtype=float)
    return (values - values.mean()) / values.std()


def simulate(parameters, skpg=None):
    """Build the calibrated sample. The same parameters always give the same sample."""
    skpg = load_skpg() if skpg is None else skpg
    simulation = parameters["simulation"]
    rng = np.random.default_rng(parameters["seed"])
    size = parameters["sample_size"]

    field_counts = largest_remainder(skpg["respondents"], size)
    field = np.repeat(skpg["field_en"].to_numpy(), field_counts)
    stem = np.repeat(skpg["stem"].to_numpy(), field_counts)

    mean, sd = simulation["cgpa_mean"], simulation["cgpa_sd"]
    lower, upper = simulation["cgpa_min"], simulation["cgpa_max"]
    cgpa = stats.truncnorm.rvs(
        (lower - mean) / sd, (upper - mean) / sd, loc=mean, scale=sd, size=size, random_state=rng
    ).round(2)
    months = np.array([int(m) for m in simulation["intern_months_probabilities"]])
    intern_months = rng.choice(
        months, size=size, p=list(simulation["intern_months_probabilities"].values())
    )
    klang_valley = (rng.random(size) < simulation["klang_valley_share"]).astype(int)

    # A hidden "employability" score ties the assumed traits to pay. Within
    # each field the graduate with the highest score gets the highest of that
    # field's published salaries, the next gets the next, and so on.
    cgpa_weight = simulation["weight_cgpa"] * np.where(stem == 1, simulation["stem_cgpa_multiplier"], 1.0)
    systematic = (
        cgpa_weight * standardise(cgpa)
        + simulation["weight_intern"] * standardise(intern_months)
        + simulation["weight_klang_valley"] * standardise(klang_valley)
    )
    explained = (
        (simulation["weight_cgpa"] * simulation["stem_cgpa_multiplier"]) ** 2
        + simulation["weight_intern"] ** 2
        + simulation["weight_klang_valley"] ** 2
    )
    score = systematic + math.sqrt(1 - explained) * rng.standard_normal(size)

    salary = np.empty(size)
    start = 0
    for row, count in zip(skpg.itertuples(index=False), field_counts):
        if count == 0:
            continue
        members = np.arange(start, start + count)
        band_counts = largest_remainder([getattr(row, name) for name in BAND_COLUMNS], count)
        salary[members[np.argsort(score[members], kind="stable")]] = np.sort(
            draw_salaries(band_counts, simulation, rng)
        )
        start += count

    sample = pd.DataFrame({
        "field": field,
        "stem": stem,
        "cgpa": cgpa,
        "intern_months": intern_months,
        "klang_valley": klang_valley,
        "salary": salary.astype(int),
    })
    sample = sample.sample(frac=1, random_state=parameters["seed"]).reset_index(drop=True)
    sample.insert(0, "graduate_id", np.arange(1, size + 1))
    return sample


def sample_band_shares(salaries):
    """Share of a salary array in each published band."""
    salaries = np.asarray(salaries, dtype=float)
    shares = []
    for _, low, high in BANDS:
        above = np.ones(len(salaries), dtype=bool) if low is None else salaries >= low
        below = np.ones(len(salaries), dtype=bool) if high is None else salaries <= high
        shares.append((above & below).mean())
    return np.array(shares)
