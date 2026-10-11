import numpy as np
import pytest

from fgsalary import model


def test_coefficients_equal_the_closed_form_solution(result):
    x = result["exog"].to_numpy()
    y = result["frame"]["ln_salary"].to_numpy()
    closed_form = np.linalg.solve(x.T @ x, x.T @ y)
    assert result["coefficients"]["coefficient"].to_numpy() == pytest.approx(closed_form, abs=1e-10)


def test_classical_standard_errors_equal_the_textbook_formula(result):
    x = result["exog"].to_numpy()
    residuals = result["frame"]["residual"].to_numpy()
    variance = residuals @ residuals / (len(x) - x.shape[1])
    expected = np.sqrt(variance * np.diag(np.linalg.inv(x.T @ x)))
    assert result["coefficients"]["std_error"].to_numpy() == pytest.approx(expected, rel=1e-9)


def test_hc3_standard_errors_equal_the_textbook_formula(result):
    x = result["exog"].to_numpy()
    residuals = result["frame"]["residual"].to_numpy()
    inverse = np.linalg.inv(x.T @ x)
    leverage = np.einsum("ij,jk,ik->i", x, inverse, x)
    weights = (residuals / (1 - leverage)) ** 2
    covariance = inverse @ (x.T * weights) @ x @ inverse
    assert result["coefficients"]["hc3_std_error"].to_numpy() == pytest.approx(
        np.sqrt(np.diag(covariance)), rel=1e-9)


def test_table_has_one_row_per_term_in_order(result):
    assert list(result["coefficients"]["term"]) == model.TERMS


def test_centring_keeps_the_interaction_from_inflating_vif(result):
    vif = result["coefficients"].set_index("term")["vif"].dropna()
    assert (vif < 5).all()


def test_stem_premium_is_positive_as_in_the_published_bands(result):
    row = result["coefficients"].set_index("term").loc["stem"]
    assert row["coefficient"] > 0
    assert row["hc3_p_value"] < 0.05


def test_smearing_factor_corrects_the_retransformation(result):
    frame = result["frame"]
    # exp() of a mean-zero residual averages above 1 (Jensen's inequality).
    assert result["smearing"] > 1
    # With the factor, predicted salaries average close to actual salaries.
    assert frame["fitted_salary"].mean() == pytest.approx(frame["salary"].mean(), rel=0.03)
    naive = np.exp(frame["fitted_ln_salary"]).mean()
    assert abs(frame["fitted_salary"].mean() - frame["salary"].mean()) < abs(naive - frame["salary"].mean())


def test_predict_salary_matches_the_fitted_column(result):
    row = result["frame"].iloc[0]
    predicted = model.predict_salary(
        result, row["cgpa"], row["intern_months"], row["stem"], row["klang_valley"])
    assert predicted == pytest.approx(row["fitted_salary"], rel=1e-9)


def test_diagnostics_cover_every_required_test(result):
    tests = set(result["diagnostics"]["test"])
    assert tests == {
        "Breusch-Pagan", "White", "Jarque-Bera", "Shapiro-Wilk", "Ramsey RESET (powers 2, 3)",
    }
    assert result["diagnostics"]["p_value"].between(0, 1).all()


def test_functional_form_comparison_is_on_one_scale(result):
    forms = result["forms"].set_index("specification")
    log_row = forms.loc["ln(salary) (log-linear)"]
    expected = result["classical"].llf - result["frame"]["ln_salary"].sum()
    assert log_row["log_likelihood_salary_scale"] == pytest.approx(expected)
    assert len(forms) == 2


def test_quantile_regressions_report_every_term(result):
    quantiles = result["quantiles"]
    assert list(quantiles["term"]) == model.TERMS
    assert {"q25", "q50", "q75"} <= set(quantiles.columns)


def test_percent_effect():
    assert model.percent_effect(0) == 0
    assert model.percent_effect(np.log(1.1)) == pytest.approx(10)
    assert model.percent_effect(np.log(1.1), change=2) == pytest.approx(21)


@pytest.mark.parametrize("p_value, stars", [(0.001, "***"), (0.03, "**"), (0.07, "*"), (0.5, "")])
def test_significance_stars(p_value, stars):
    assert model.significance_stars(p_value) == stars
