"""Write the executive summary from the fitted numbers, so it can never drift from them."""
import math

from . import data as data_module
from .model import percent_effect


def rm(value):
    return f"RM{value:,.0f}"


def pct(value, digits=1):
    return f"{value * 100:.{digits}f}%"


def p_text(p_value):
    return "p < 0.001" if p_value < 0.001 else f"p = {p_value:.3f}"


def verdict(p_value):
    if p_value < 0.05:
        return "statistically significant at the 5% level"
    if p_value < 0.1:
        return "significant only at the 10% level"
    return "not statistically distinguishable from zero"


def markdown_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines += ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return "\n".join(lines)


def build_summary(result, scenarios, profile, parameters, skpg):
    policy, simulation = parameters["policy"], parameters["simulation"]
    coefficients = result["coefficients"].set_index("term")
    statistics = result["fit_statistics"]
    frame = result["frame"]
    floor = policy["graduate_floor"]

    def b(term):
        return coefficients.loc[term, "coefficient"]

    def p(term):
        return coefficients.loc[term, "hc3_p_value"]

    published_below = data_module.published_share_at_or_below(
        skpg, floor, simulation["bottom_band_floor"], simulation["top_band_cap"])
    published_below_min = data_module.published_share_at_or_below(
        skpg, policy["new_minimum_wage"], simulation["bottom_band_floor"], simulation["top_band_cap"])
    # Share at or below the floor in each field, from the published bands alone.
    exposure = sorted(
        (
            (row["field_en"], data_module.published_share_at_or_below(
                skpg[skpg["field_en"] == row["field_en"]], floor,
                simulation["bottom_band_floor"], simulation["top_band_cap"]))
            for _, row in skpg[skpg["respondents"] >= 1000].iterrows()
        ),
        key=lambda item: -item[1],
    )
    most_exposed, least_exposed = exposure[:2], exposure[-1]
    central = scenarios.iloc[1]
    floor_only = scenarios.iloc[0]
    exempt = scenarios.iloc[2]
    grown = scenarios.iloc[3]
    minimum_only = scenarios.iloc[4]
    full_time = scenarios.iloc[5]

    coefficient_rows = [
        [row.label, f"{row.coefficient:.4f}", f"{row.hc3_std_error:.4f}", f"{row.hc3_t_value:.2f}",
         p_text(row.hc3_p_value) + (" " + row.hc3_stars if row.hc3_stars else ""),
         f"[{row.hc3_ci_low:.4f}, {row.hc3_ci_high:.4f}]",
         "" if row.term == "const" else f"{row.vif:.2f}"]
        for row in result["coefficients"].itertuples(index=False)
    ]
    diagnostic_rows = [
        [row.test, row.checks, f"{row.statistic:.3f}", p_text(row.p_value),
         "Rejected" if row.rejected_at_5pct else "Not rejected"]
        for row in result["diagnostics"].itertuples(index=False)
    ]
    form_rows = [
        [row.specification, f"{row.r_squared:.3f}", f"{row.log_likelihood_salary_scale:,.1f}",
         f"{row.aic_salary_scale:,.1f}", p_text(row.reset_p_value)]
        for row in result["forms"].itertuples(index=False)
    ]
    quantile_rows = [
        [row.label, f"{row.q25:.4f}", f"{row.q50:.4f}", f"{row.q75:.4f}", f"{coefficients.loc[row.term, 'coefficient']:.4f}"]
        for row in result["quantiles"].itertuples(index=False)
    ]
    scenario_rows = [
        [row.scenario, pct(row.share_below_floor), pct(row.share_receiving_raise),
         rm(row.mean_raise_if_raised), pct(row.wage_bill_increase),
         rm(row.employer_cost_increase_per_1000_grads), pct(row.mid_tier_share_raised),
         f"{rm(row.mid_tier_mean_raise)} ({pct(row.mid_tier_mean_raise_pct)})"]
        for row in scenarios.itertuples(index=False)
    ]
    band_rows = [
        [label, pct(real), pct(drawn)]
        for label, real, drawn in zip(
            data_module.BAND_LABELS, data_module.published_band_shares(skpg),
            data_module.sample_band_shares(frame["salary"]))
    ]
    profile_rows = [
        [rm(row.salary_before), rm(row.salary_after), rm(row.raise_from_floor),
         rm(row.raise_from_spillover), rm(row.total_raise)]
        for row in profile.itertuples(index=False)
        if row.salary_before % 200 == 100 or row.salary_before in (floor, policy["compression_ceiling"])
    ]

    stem_cgpa_effect = b("cgpa_c") + b("cgpa_c_x_stem")
    best_form = result["forms"].sort_values("aic_salary_scale").iloc[0]["specification"]
    heteroscedastic = result["heteroscedastic"]
    max_vif = coefficients["vif"].max()
    reset_p = result["diagnostics"].set_index("test").loc["Ramsey RESET (powers 2, 3)", "p_value"]

    sections = [
        "# Fresh graduate starting salaries and the RM2,500 wage floor",
        "## Read this first",
        f"- **Real:** salaries come from the monthly income bands of {skpg['respondents'].sum():,} first-degree "
        "graduates in KPT's Graduate Tracer Study 2024 (Jadual 4o). The policy figures are from Budget 2027.\n"
        "- **Assumed:** CGPA, internship length and Klang Valley location are not published with income, so they "
        "are simulated and their link to salary is set by assumption. Their coefficients below show that the "
        "method recovers what was put in. They are not findings about the labour market.\n"
        "- **Forward-looking:** the RM2,500 floor is announced but not in force. Its effect is simulated under "
        "stated assumptions, not estimated from data.",

        "## Headline numbers",
        f"- **{pct(published_below)} of first-degree graduates earned {rm(floor)} or less** in the 2024 tracer "
        f"study (published bands, no modelling). {pct(published_below_min)} earned {rm(policy['new_minimum_wage'])} or less.\n"
        f"- In the central scenario, {pct(central.share_receiving_raise)} of graduates get a raise, averaging "
        f"{rm(central.mean_raise_if_raised)} a month, and the graduate wage bill rises {pct(central.wage_bill_increase)}. "
        f"If graduates reporting {rm(policy['likely_part_time_at_or_below'])} or less are outside the floor "
        f"(they are probably not full-time), the rise is {pct(full_time.wage_bill_increase)}.\n"
        f"- That is about {rm(central.employer_cost_increase_per_1000_grads)} a month in extra employment cost "
        "per 1,000 graduates employed, including employer EPF, SOCSO, EIS and the HRD Corp levy.\n"
        f"- STEM graduates earn about {percent_effect(b('stem')):.1f}% more than non-STEM graduates at an average "
        f"CGPA ({p_text(p('stem'))}). This gap comes from the real field-by-field salary bands.",

        "## The sample",
        f"{len(frame):,} simulated graduates, stratified by field of study in proportion to the tracer study's "
        f"respondents. {pct(frame['stem'].mean())} are STEM (engineering, ICT, natural sciences/mathematics/"
        f"statistics). Median salary {rm(frame['salary'].median())}, mean {rm(frame['salary'].mean())}.",
        markdown_table(["Monthly income band", "Published (SKPG 2024)", "Simulated sample"], band_rows),

        "## The regression",
        "ln(salary) = b0 + b1 CGPA_c + b2 internship months + b3 STEM + b4 Klang Valley + b5 (CGPA_c x STEM) + e, "
        f"with CGPA centred on its mean ({result['cgpa_mean']:.3f}). Standard errors are HC3.",
        markdown_table(["Term", "Coefficient", "HC3 std error", "t", "p", "95% CI", "VIF"], coefficient_rows),
        f"n = {statistics['observations']:,}; R-squared = {statistics['r_squared']:.3f}; adjusted R-squared = "
        f"{statistics['adj_r_squared']:.3f}; F = {statistics['f_statistic']:.2f} ({p_text(statistics['f_p_value'])}); "
        f"log-likelihood = {statistics['log_likelihood']:.1f}; AIC = {statistics['aic']:.1f}; "
        f"BIC = {statistics['bic']:.1f}. *** p<0.01, ** p<0.05, * p<0.10.",

        "## What each coefficient means",
        f"- **STEM degree (real data).** At an average CGPA, a STEM graduate's starting salary is about "
        f"{percent_effect(b('stem')):.1f}% higher than a non-STEM graduate's ({p_text(p('stem'))}; "
        f"{verdict(p('stem'))}).\n"
        f"- **CGPA (assumed link).** One extra CGPA point goes with {percent_effect(b('cgpa_c')):.1f}% higher pay "
        f"for non-STEM graduates ({p_text(p('cgpa_c'))}), or about {percent_effect(b('cgpa_c'), 0.1):.1f}% per 0.10 point.\n"
        f"- **CGPA x STEM (assumed link).** For STEM graduates the return to one CGPA point is "
        f"{percent_effect(stem_cgpa_effect):.1f}%. The difference from non-STEM is {verdict(p('cgpa_c_x_stem'))} "
        f"({p_text(p('cgpa_c_x_stem'))}).\n"
        f"- **Internship (assumed link).** Each extra month goes with {percent_effect(b('intern_months')):.1f}% "
        f"higher pay, so 6 months instead of 3 is about {percent_effect(b('intern_months'), 3):.1f}% "
        f"({p_text(p('intern_months'))}).\n"
        f"- **Klang Valley (assumed link).** Working in the Klang Valley goes with "
        f"{percent_effect(b('klang_valley')):.1f}% higher pay ({p_text(p('klang_valley'))}).\n"
        f"- **Intercept.** exp({b('const'):.3f}) x smearing factor {result['smearing']:.3f} = "
        f"{rm(math.exp(b('const')) * result['smearing'])}: the expected salary of a non-STEM graduate outside the "
        "Klang Valley with an average CGPA and, hypothetically, no internship.",

        "## Diagnostics",
        markdown_table(["Test", "Checks", "Statistic", "p", "At 5%"], diagnostic_rows),
        f"- **Multicollinearity:** the largest VIF is {max_vif:.2f}"
        + (", well under the usual warning level of 5." if max_vif < 5 else ", above the usual warning level of 5.") + "\n"
        + ("- **Heteroscedasticity:** constant error variance is rejected, so all inference uses HC3 robust "
           "standard errors.\n" if heteroscedastic else
           "- **Heteroscedasticity:** constant error variance is not rejected. HC3 standard errors are reported "
           "anyway; they are valid either way.\n")
        + f"- **Normality:** residual skewness is {result['residual_moments']['skewness']:.2f} and kurtosis "
        f"{result['residual_moments']['kurtosis']:.2f} (a normal distribution has 0 and 3). The long left tail comes from the "
        "real share of graduates reporting RM1,000 or less. Normality is not needed for OLS to be unbiased, and "
        f"with {statistics['observations']:,} observations the t and F tests remain reliable.\n"
        + ("- **Functional form:** RESET rejects the linear form "
           f"({p_text(reset_p)}). Salaries were drawn from bands, which no smooth equation fits exactly."
           if reset_p < 0.05 else
           f"- **Functional form:** RESET does not reject the specification ({p_text(reset_p)})."),

        "## Log versus level, and effects across the pay distribution",
        markdown_table(["Specification", "R-squared", "Log-likelihood (salary scale)", "AIC (salary scale)", "RESET p"], form_rows),
        f"R-squared cannot be compared across different dependent variables, so the log model's likelihood is "
        f"converted to the salary scale. On that footing the better fit is **{best_form}**.",
        markdown_table(["Term", "25th percentile", "Median", "75th percentile", "OLS (mean)"], quantile_rows),
        "Quantile regressions show whether an effect is the same for low and high earners. Where the columns "
        "differ, the OLS coefficient is averaging over different effects.",

        "## Wage floor simulation",
        markdown_table(
            ["Scenario", "Below floor", "Get a raise", "Mean raise", "Wage bill", "Extra cost per 1,000 graduates / month",
             "Mid-tier raised", "Mid-tier mean raise"], scenario_rows),
        "\n".join(f"- **{row.scenario}:** {row.description}." for row in scenarios.itertuples(index=False)),

        f"## Spillover onto mid-tier salaries ({rm(policy['mid_tier_low'])} to {rm(policy['mid_tier_high'])})",
        f"{pct(central.mid_tier_share_of_graduates)} of graduates already earn in this range. The floor does not "
        f"bind for them, but it removes most of their pay advantage over new colleagues on {rm(floor)}. If "
        f"employers restore {pct(policy['compression_alpha'], 0)} of squeezed pay gaps up to "
        f"{rm(policy['compression_ceiling'])}, {pct(central.mid_tier_share_raised)} of this group get a raise "
        f"averaging {rm(central.mid_tier_mean_raise)} a month ({pct(central.mid_tier_mean_raise_pct)}). "
        f"Spillover lifts the total wage bill increase from {pct(floor_only.wage_bill_increase)} (floor only) to "
        f"{pct(central.wage_bill_increase)}. The median-to-10th-percentile pay ratio falls from "
        f"{central.p50_p10_ratio_before:.2f} to {central.p50_p10_ratio_after:.2f}: pay at the bottom is compressed.",
        markdown_table(["Salary before", "Salary after", "Raise from floor", "Raise from spillover", "Total raise"],
                       profile_rows),

        "## Takeaways",
        "**For HR and compensation planning**\n"
        f"- Budget for the spillover as well as the floor. The floor alone costs {pct(floor_only.wage_bill_increase)} "
        f"of the graduate wage bill; with partial restoration of pay gaps it is {pct(central.wage_bill_increase)}.\n"
        f"- Statutory on-costs add {pct(sum(parameters['statutory'][k] for k in ('epf_employer', 'socso_employer', 'eis_employer', 'hrd_levy')), 2)} "
        "on top of every ringgit of raise, so total cost of employment rises faster than base pay.\n"
        f"- Review the {rm(policy['mid_tier_low'])} to {rm(policy['mid_tier_high'])} bands before the floor starts. "
        "Graduates already paid just above the floor are the group whose premium over new hires shrinks most.\n"
        f"- Exposure differs sharply by field. The published bands put {most_exposed[0][0]} "
        f"({pct(most_exposed[0][1])} at or below the floor) and {most_exposed[1][0]} ({pct(most_exposed[1][1])}) "
        f"highest, and {least_exposed[0]} ({pct(least_exposed[1])}) lowest.",
        "**For national wage compliance**\n"
        f"- The floor is not marginal: {pct(published_below)} of first-degree graduates were at or below it "
        "in 2024.\n"
        f"- Exemptions matter. If only {pct(policy['sme_coverage_rate'], 0)} of graduates work for covered employers, "
        f"the share who get a raise falls from {pct(central.share_receiving_raise)} to {pct(exempt.share_receiving_raise)}.\n"
        f"- Timing matters. With {pct(policy['annual_wage_growth'], 0)} annual pay growth before the floor starts, "
        f"the share below it falls to {pct(grown.share_below_floor)}.\n"
        f"- The RM{policy['new_minimum_wage']:,} minimum wage on its own binds for "
        f"{pct(minimum_only.share_below_floor)} of graduates in the sample; the separate graduate floor binds for "
        f"{pct(central.share_below_floor)}.\n"
        f"- Who counts as covered changes the bill. Leaving out graduates reporting "
        f"{rm(policy['likely_part_time_at_or_below'])} or less cuts the wage bill increase from "
        f"{pct(central.wage_bill_increase)} to {pct(full_time.wage_bill_increase)}.",

        "## Limits",
        f"- The simulation assumes no job losses, no cut in hours and full compliance by covered employers. A floor "
        f"that binds for {pct(published_below, 0)} of a group could change hiring; this model cannot say by how much.\n"
        f"- Graduates reporting {rm(policy['likely_part_time_at_or_below'])} or less (at or below the 2024 minimum "
        "wage) are probably part-time, self-employed or in gig work. Scenario F shows the effect of leaving them out.\n"
        "- Salaries within a band are spread evenly, which is an approximation.\n"
        "- Statutory contributions use flat rates and take-home pay excludes income tax (PCB).\n"
        "- A proper estimate of the CGPA, internship and location effects needs individual-level data, which "
        "neither KPT nor DOSM publishes.",
    ]
    return "\n\n".join(sections) + "\n"
