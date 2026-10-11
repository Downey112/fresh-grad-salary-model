# Fresh graduate starting salaries and the RM2,500 wage floor

## Read this first

- **Real:** salaries come from the monthly income bands of 109,414 first-degree graduates in KPT's Graduate Tracer Study 2024 (Jadual 4o). The policy figures are from Budget 2027.
- **Assumed:** CGPA, internship length and Klang Valley location are not published with income, so they are simulated and their link to salary is set by assumption. Their coefficients below show that the method recovers what was put in. They are not findings about the labour market.
- **Forward-looking:** the RM2,500 floor is announced but not in force. Its effect is simulated under stated assumptions, not estimated from data.

## Headline numbers

- **49.7% of first-degree graduates earned RM2,500 or less** in the 2024 tracer study (published bands, no modelling). 30.6% earned RM2,000 or less.
- In the central scenario, 70.1% of graduates get a raise, averaging RM571 a month, and the graduate wage bill rises 14.4%. If graduates reporting RM1,500 or less are outside the floor (they are probably not full-time), the rise is 7.1%.
- That is about RM464,035 a month in extra employment cost per 1,000 graduates employed, including employer EPF, SOCSO, EIS and the HRD Corp levy.
- STEM graduates earn about 16.1% more than non-STEM graduates at an average CGPA (p < 0.001). This gap comes from the real field-by-field salary bands.

## The sample

1,000 simulated graduates, stratified by field of study in proportion to the tracer study's respondents. 35.6% are STEM (engineering, ICT, natural sciences/mathematics/statistics). Median salary RM2,510, mean RM2,783.

| Monthly income band | Published (SKPG 2024) | Simulated sample |
|---|---|---|
| RM1,000 and below | 6.9% | 7.0% |
| RM1,001 - RM1,500 | 6.2% | 6.2% |
| RM1,501 - RM2,000 | 17.5% | 17.5% |
| RM2,001 - RM2,500 | 19.1% | 19.2% |
| RM2,501 - RM3,000 | 16.6% | 16.6% |
| RM3,001 - RM4,000 | 22.7% | 22.7% |
| RM4,001 - RM5,000 | 6.6% | 6.6% |
| RM5,001 - RM10,000 | 3.8% | 3.7% |
| More than RM10,000 | 0.6% | 0.5% |

## The regression

ln(salary) = b0 + b1 CGPA_c + b2 internship months + b3 STEM + b4 Klang Valley + b5 (CGPA_c x STEM) + e, with CGPA centred on its mean (3.207). Standard errors are HC3.

| Term | Coefficient | HC3 std error | t | p | 95% CI | VIF |
|---|---|---|---|---|---|---|
| Intercept | 7.4583 | 0.0507 | 147.24 | p < 0.001 *** | [7.3589, 7.5577] |  |
| CGPA (centred) | 0.3521 | 0.0605 | 5.82 | p < 0.001 *** | [0.2334, 0.4707] | 1.65 |
| Internship months | 0.0331 | 0.0075 | 4.44 | p < 0.001 *** | [0.0184, 0.0477] | 1.00 |
| STEM degree | 0.1495 | 0.0317 | 4.71 | p < 0.001 *** | [0.0872, 0.2118] | 1.01 |
| Klang Valley | 0.2406 | 0.0316 | 7.62 | p < 0.001 *** | [0.1787, 0.3026] | 1.01 |
| CGPA (centred) x STEM | 0.0297 | 0.0901 | 0.33 | p = 0.742 | [-0.1471, 0.2066] | 1.65 |

n = 1,000; R-squared = 0.139; adjusted R-squared = 0.134; F = 31.99 (p < 0.001); log-likelihood = -707.2; AIC = 1426.4; BIC = 1455.8. *** p<0.01, ** p<0.05, * p<0.10.

## What each coefficient means

- **STEM degree (real data).** At an average CGPA, a STEM graduate's starting salary is about 16.1% higher than a non-STEM graduate's (p < 0.001; statistically significant at the 5% level).
- **CGPA (assumed link).** One extra CGPA point goes with 42.2% higher pay for non-STEM graduates (p < 0.001), or about 3.6% per 0.10 point.
- **CGPA x STEM (assumed link).** For STEM graduates the return to one CGPA point is 46.5%. The difference from non-STEM is not statistically distinguishable from zero (p = 0.742).
- **Internship (assumed link).** Each extra month goes with 3.4% higher pay, so 6 months instead of 3 is about 10.4% (p < 0.001).
- **Klang Valley (assumed link).** Working in the Klang Valley goes with 27.2% higher pay (p < 0.001).
- **Intercept.** exp(7.458) x smearing factor 1.128 = RM1,956: the expected salary of a non-STEM graduate outside the Klang Valley with an average CGPA and, hypothetically, no internship.

## Diagnostics

| Test | Checks | Statistic | p | At 5% |
|---|---|---|---|---|
| Breusch-Pagan | Heteroscedasticity | 11.028 | p = 0.051 | Not rejected |
| White | Heteroscedasticity | 21.313 | p = 0.127 | Not rejected |
| Jarque-Bera | Residual normality | 45.659 | p < 0.001 | Rejected |
| Shapiro-Wilk | Residual normality | 0.980 | p < 0.001 | Rejected |
| Ramsey RESET (powers 2, 3) | Functional form | 2.073 | p = 0.126 | Not rejected |

- **Multicollinearity:** the largest VIF is 1.65, well under the usual warning level of 5.
- **Heteroscedasticity:** constant error variance is not rejected. HC3 standard errors are reported anyway; they are valid either way.
- **Normality:** residual skewness is -0.14 and kurtosis 4.01 (a normal distribution has 0 and 3). The long left tail comes from the real share of graduates reporting RM1,000 or less. Normality is not needed for OLS to be unbiased, and with 1,000 observations the t and F tests remain reliable.
- **Functional form:** RESET does not reject the specification (p = 0.126).

## Log versus level, and effects across the pay distribution

| Specification | R-squared | Log-likelihood (salary scale) | AIC (salary scale) | RESET p |
|---|---|---|---|---|
| ln(salary) (log-linear) | 0.139 | -8,502.1 | 17,018.2 | p = 0.126 |
| salary in RM (level) | 0.096 | -8,745.1 | 17,504.2 | p = 0.918 |

R-squared cannot be compared across different dependent variables, so the log model's likelihood is converted to the salary scale. On that footing the better fit is **ln(salary) (log-linear)**.

| Term | 25th percentile | Median | 75th percentile | OLS (mean) |
|---|---|---|---|---|
| Intercept | 7.2048 | 7.5471 | 7.8484 | 7.4583 |
| CGPA (centred) | 0.3356 | 0.2679 | 0.2106 | 0.3521 |
| Internship months | 0.0318 | 0.0216 | 0.0212 | 0.0331 |
| STEM degree | 0.2103 | 0.1860 | 0.1069 | 0.1495 |
| Klang Valley | 0.2262 | 0.2096 | 0.1982 | 0.2406 |
| CGPA (centred) x STEM | -0.0637 | -0.0020 | 0.0849 | 0.0297 |

Quantile regressions show whether an effect is the same for low and high earners. Where the columns differ, the OLS coefficient is averaging over different effects.

## Wage floor simulation

| Scenario | Below floor | Get a raise | Mean raise | Wage bill | Extra cost per 1,000 graduates / month | Mid-tier raised | Mid-tier mean raise |
|---|---|---|---|---|---|---|---|
| A. Floor only, no spillover | 49.6% | 49.6% | RM757 | 13.5% | RM435,102 | 0.0% | RM0 (0.0%) |
| B. Central: floor with spillover | 49.6% | 70.1% | RM571 | 14.4% | RM464,035 | 100.0% | RM56 (2.1%) |
| C. Central with SME exemption | 49.6% | 41.2% | RM572 | 8.5% | RM273,490 | 55.9% | RM32 (1.2%) |
| D. Central after wage growth | 41.9% | 63.4% | RM517 | 10.8% | RM380,126 | 100.0% | RM56 (2.1%) |
| E. Minimum wage only | 30.1% | 56.3% | RM326 | 6.6% | RM212,549 | 35.6% | RM3 (0.1%) |
| F. Central, full-time jobs only | 49.6% | 56.9% | RM349 | 7.1% | RM230,465 | 100.0% | RM56 (2.1%) |

- **A. Floor only, no spillover:** RM2,500 floor, every employer complies, nobody above the floor gets a raise.
- **B. Central: floor with spillover:** As A, plus employers restore 25% of squeezed pay gaps up to RM3,200.
- **C. Central with SME exemption:** As B, but only 60% of graduates work for employers the floor applies to (assumed).
- **D. Central after wage growth:** As B, after 3% a year of pay growth for 3 years (2024 data to a 2027 start).
- **E. Minimum wage only:** Only the RM2,000 national minimum wage applies to graduates; no separate graduate floor.
- **F. Central, full-time jobs only:** As B, but graduates reporting RM1,500 or less (at or below the 2024 minimum wage, so probably not in full-time employment) are treated as outside the floor.

## Spillover onto mid-tier salaries (RM2,500 to RM3,100)

18.8% of graduates already earn in this range. The floor does not bind for them, but it removes most of their pay advantage over new colleagues on RM2,500. If employers restore 25% of squeezed pay gaps up to RM3,200, 100.0% of this group get a raise averaging RM56 a month (2.1%). Spillover lifts the total wage bill increase from 13.5% (floor only) to 14.4%. The median-to-10th-percentile pay ratio falls from 2.06 to 1.04: pay at the bottom is compressed.

| Salary before | Salary after | Raise from floor | Raise from spillover | Total raise |
|---|---|---|---|---|
| RM1,700 | RM2,500 | RM800 | RM0 | RM800 |
| RM1,900 | RM2,523 | RM600 | RM23 | RM623 |
| RM2,100 | RM2,547 | RM400 | RM47 | RM447 |
| RM2,300 | RM2,570 | RM200 | RM70 | RM270 |
| RM2,500 | RM2,593 | RM0 | RM93 | RM93 |
| RM2,700 | RM2,767 | RM0 | RM67 | RM67 |
| RM2,900 | RM2,940 | RM0 | RM40 | RM40 |
| RM3,100 | RM3,113 | RM0 | RM13 | RM13 |
| RM3,200 | RM3,200 | RM0 | RM0 | RM0 |

## Takeaways

**For HR and compensation planning**
- Budget for the spillover as well as the floor. The floor alone costs 13.5% of the graduate wage bill; with partial restoration of pay gaps it is 14.4%.
- Statutory on-costs add 15.95% on top of every ringgit of raise, so total cost of employment rises faster than base pay.
- Review the RM2,500 to RM3,100 bands before the floor starts. Graduates already paid just above the floor are the group whose premium over new hires shrinks most.
- Exposure differs sharply by field. The published bands put Education (77.2% at or below the floor) and Arts and humanities (75.0%) highest, and Information and communication technologies (27.7%) lowest.

**For national wage compliance**
- The floor is not marginal: 49.7% of first-degree graduates were at or below it in 2024.
- Exemptions matter. If only 60% of graduates work for covered employers, the share who get a raise falls from 70.1% to 41.2%.
- Timing matters. With 3% annual pay growth before the floor starts, the share below it falls to 41.9%.
- The RM2,000 minimum wage on its own binds for 30.1% of graduates in the sample; the separate graduate floor binds for 49.6%.
- Who counts as covered changes the bill. Leaving out graduates reporting RM1,500 or less cuts the wage bill increase from 14.4% to 7.1%.

## Limits

- The simulation assumes no job losses, no cut in hours and full compliance by covered employers. A floor that binds for 50% of a group could change hiring; this model cannot say by how much.
- Graduates reporting RM1,500 or less (at or below the 2024 minimum wage) are probably part-time, self-employed or in gig work. Scenario F shows the effect of leaving them out.
- Salaries within a band are spread evenly, which is an approximation.
- Statutory contributions use flat rates and take-home pay excludes income tax (PCB).
- A proper estimate of the CGPA, internship and location effects needs individual-level data, which neither KPT nor DOSM publishes.
