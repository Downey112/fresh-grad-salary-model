"""The wage regression, its diagnostics and its robustness checks.

    ln(salary) = b0 + b1 cgpa_c + b2 intern_months + b3 stem + b4 klang_valley
                 + b5 (cgpa_c x stem) + e

cgpa_c is CGPA minus the sample mean. Centring it means b3 is the STEM gap for
a graduate with an average CGPA, and it stops the interaction term from being
almost collinear with the STEM dummy.
"""
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.diagnostic import het_breuschpagan, het_white, linear_reset
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.stattools import jarque_bera

REGRESSORS = ["cgpa_c", "intern_months", "stem", "klang_valley", "cgpa_c_x_stem"]
TERMS = ["const"] + REGRESSORS
LABELS = {
    "const": "Intercept",
    "cgpa_c": "CGPA (centred)",
    "intern_months": "Internship months",
    "stem": "STEM degree",
    "klang_valley": "Klang Valley",
    "cgpa_c_x_stem": "CGPA (centred) x STEM",
}


def add_model_columns(sample, cgpa_mean=None):
    """Add the regression columns. Pass ``cgpa_mean`` to reuse a fitted model's centring."""
    frame = sample.copy()
    cgpa_mean = frame["cgpa"].mean() if cgpa_mean is None else cgpa_mean
    frame["cgpa_c"] = frame["cgpa"] - cgpa_mean
    frame["cgpa_c_x_stem"] = frame["cgpa_c"] * frame["stem"]
    if "salary" in frame:
        frame["ln_salary"] = np.log(frame["salary"])
    return frame, cgpa_mean


def design_matrix(frame):
    return sm.add_constant(frame[REGRESSORS].astype(float), has_constant="add")


def significance_stars(p_value):
    if p_value < 0.01:
        return "***"
    if p_value < 0.05:
        return "**"
    if p_value < 0.1:
        return "*"
    return ""


def coefficient_table(classical, robust, vif):
    """One row per term: classical and HC3 inference side by side."""
    classical_ci = classical.conf_int()
    robust_ci = robust.conf_int()
    rows = []
    for term in TERMS:
        rows.append({
            "term": term,
            "label": LABELS[term],
            "coefficient": classical.params[term],
            "std_error": classical.bse[term],
            "t_value": classical.tvalues[term],
            "p_value": classical.pvalues[term],
            "ci_low": classical_ci.loc[term, 0],
            "ci_high": classical_ci.loc[term, 1],
            "hc3_std_error": robust.bse[term],
            "hc3_t_value": robust.tvalues[term],
            "hc3_p_value": robust.pvalues[term],
            "hc3_ci_low": robust_ci.loc[term, 0],
            "hc3_ci_high": robust_ci.loc[term, 1],
            "hc3_stars": significance_stars(robust.pvalues[term]),
            "vif": vif.get(term, np.nan),
        })
    return pd.DataFrame(rows)


def variance_inflation(exog):
    """VIF of each regressor (the intercept has none)."""
    values = exog.to_numpy()
    return {
        name: variance_inflation_factor(values, position)
        for position, name in enumerate(exog.columns)
        if name != "const"
    }


def run_diagnostics(classical, exog):
    """Tests of the classical assumptions. Each row says what a small p-value means."""
    residuals = classical.resid
    bp_lm, bp_p, _, _ = het_breuschpagan(residuals, exog)
    with warnings.catch_warnings():
        # White's auxiliary regression squares every regressor, and the square
        # of a 0/1 dummy is the dummy itself. statsmodels warns about the
        # duplicate columns but sets the degrees of freedom from the rank, so
        # the statistic and p-value are correct.
        warnings.simplefilter("ignore")
        white_lm, white_p, _, _ = het_white(residuals, exog)
    jb_stat, jb_p, skew, kurtosis = jarque_bera(residuals)
    sw_stat, sw_p = stats.shapiro(residuals)
    reset = linear_reset(classical, power=[2, 3], use_f=True)

    rows = [
        ("Breusch-Pagan", "Heteroscedasticity", bp_lm, bp_p,
         "error variance changes with the regressors"),
        ("White", "Heteroscedasticity", white_lm, white_p,
         "error variance changes with the regressors, their squares or products"),
        ("Jarque-Bera", "Residual normality", jb_stat, jb_p,
         "residuals are skewed or heavy-tailed"),
        ("Shapiro-Wilk", "Residual normality", sw_stat, sw_p,
         "residuals are not normal (very sensitive at this sample size)"),
        ("Ramsey RESET (powers 2, 3)", "Functional form", float(reset.fvalue), float(reset.pvalue),
         "powers of the fitted values add explanatory power, so the form is misspecified"),
    ]
    table = pd.DataFrame(rows, columns=["test", "checks", "statistic", "p_value", "small_p_means"])
    table["rejected_at_5pct"] = table["p_value"] < 0.05
    return table, {"skewness": float(skew), "kurtosis": float(kurtosis)}


def compare_functional_forms(frame, exog, log_fit):
    """Log versus level salary on a common footing.

    R-squared cannot be compared across different dependent variables. The
    log-likelihoods can, once the log model's is moved onto the salary scale
    by subtracting the sum of ln(salary) (the Jacobian of the transformation).
    """
    level_fit = sm.OLS(frame["salary"].astype(float), exog).fit()
    parameter_count = len(log_fit.params) + 1
    log_llf_on_salary_scale = log_fit.llf - frame["ln_salary"].sum()

    def aic(log_likelihood):
        return 2 * parameter_count - 2 * log_likelihood

    return pd.DataFrame([
        {"specification": "ln(salary) (log-linear)", "r_squared": log_fit.rsquared,
         "log_likelihood_salary_scale": log_llf_on_salary_scale,
         "aic_salary_scale": aic(log_llf_on_salary_scale),
         "reset_p_value": float(linear_reset(log_fit, power=[2, 3], use_f=True).pvalue)},
        {"specification": "salary in RM (level)", "r_squared": level_fit.rsquared,
         "log_likelihood_salary_scale": level_fit.llf,
         "aic_salary_scale": aic(level_fit.llf),
         "reset_p_value": float(linear_reset(level_fit, power=[2, 3], use_f=True).pvalue)},
    ])


def quantile_table(frame, exog, quantiles=(0.25, 0.5, 0.75)):
    """Quantile regressions: do the effects differ between low and high earners?"""
    columns = {}
    for quantile in quantiles:
        fit = sm.QuantReg(frame["ln_salary"], exog).fit(q=quantile)
        columns[f"q{int(quantile * 100)}"] = fit.params
        columns[f"q{int(quantile * 100)}_p_value"] = fit.pvalues
    table = pd.DataFrame(columns).loc[TERMS]
    table.insert(0, "label", [LABELS[term] for term in TERMS])
    return table.reset_index(names="term")


def percent_effect(coefficient, change=1.0):
    """Percentage change in salary when a regressor rises by ``change``."""
    return (np.exp(coefficient * change) - 1) * 100


def fit(sample):
    """Fit the model and return everything the report and workbook need."""
    frame, cgpa_mean = add_model_columns(sample)
    exog = design_matrix(frame)
    classical = sm.OLS(frame["ln_salary"], exog).fit()
    robust = classical.get_robustcov_results(cov_type="HC3")
    # get_robustcov_results returns plain arrays; give them the term names back.
    robust_named = _NamedResults(robust, TERMS)

    vif = variance_inflation(exog)
    diagnostics, moments = run_diagnostics(classical, exog)
    frame["fitted_ln_salary"] = classical.fittedvalues
    frame["residual"] = classical.resid
    # Duan's smearing factor: exp(fitted) alone predicts the median, not the mean.
    smearing = float(np.exp(classical.resid).mean())
    frame["fitted_salary"] = np.exp(frame["fitted_ln_salary"]) * smearing

    heteroscedastic = bool(
        diagnostics.loc[diagnostics["checks"] == "Heteroscedasticity", "rejected_at_5pct"].any()
    )
    return {
        "frame": frame,
        "exog": exog,
        "cgpa_mean": float(cgpa_mean),
        "classical": classical,
        "robust": robust,
        "coefficients": coefficient_table(classical, robust_named, vif),
        "diagnostics": diagnostics,
        "residual_moments": moments,
        "heteroscedastic": heteroscedastic,
        "smearing": smearing,
        "forms": compare_functional_forms(frame, exog, classical),
        "quantiles": quantile_table(frame, exog),
        "fit_statistics": {
            "observations": int(classical.nobs),
            "r_squared": float(classical.rsquared),
            "adj_r_squared": float(classical.rsquared_adj),
            "f_statistic": float(classical.fvalue),
            "f_p_value": float(classical.f_pvalue),
            "hc3_f_statistic": float(np.squeeze(robust.fvalue)),
            "hc3_f_p_value": float(np.squeeze(robust.f_pvalue)),
            "log_likelihood": float(classical.llf),
            "aic": float(classical.aic),
            "bic": float(classical.bic),
            "residual_std_error": float(np.sqrt(classical.scale)),
            "df_residual": int(classical.df_resid),
        },
    }


class _NamedResults:
    """Label the arrays of a robust-covariance result with the term names."""

    def __init__(self, results, names):
        self.params = pd.Series(results.params, index=names)
        self.bse = pd.Series(results.bse, index=names)
        self.tvalues = pd.Series(results.tvalues, index=names)
        self.pvalues = pd.Series(results.pvalues, index=names)
        self._interval = pd.DataFrame(results.conf_int(), index=names)

    def conf_int(self):
        return self._interval


def predict_salary(result, cgpa, intern_months, stem, klang_valley):
    """Expected monthly salary in RM for one profile, with the smearing correction."""
    profile = pd.DataFrame([{
        "cgpa": cgpa, "intern_months": intern_months, "stem": stem, "klang_valley": klang_valley,
    }])
    frame, _ = add_model_columns(profile, cgpa_mean=result["cgpa_mean"])
    fitted = result["classical"].predict(design_matrix(frame))
    return float(np.exp(fitted.iloc[0]) * result["smearing"])
