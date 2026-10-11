# Fresh graduate starting salaries and the RM2,500 wage floor

Budget 2027 (9 October 2026) raises Malaysia's minimum wage from RM1,700 to RM2,000 from
June 2027 and introduces a RM2,500 monthly floor for graduates and semi-skilled workers.
This project asks two questions:

1. How many graduates does a RM2,500 floor reach, and what does it cost employers once
   pay just above the floor is adjusted too?
2. What does a multiple linear regression of starting salary look like, with a full set
   of diagnostics, and can Excel reproduce it with native formulas?

**Read the results:** [`outputs/executive_summary.md`](outputs/executive_summary.md)
**Open the workbook:** `outputs/FreshGrad_Salary_Regression_Model.xlsx`

## What is real and what is not

| | Status | Source |
|---|---|---|
| Salary distribution by field of study | **Real** | KPT, *Laporan Kajian Pengesanan Graduan 2024*, Jadual 4o: monthly income bands of 109,414 first-degree graduates |
| Policy figures (RM2,500, RM2,000, RM1,700) | **Real** | Budget 2027 speech |
| Statutory contribution rates | **Real, simplified** | Flat-rate EPF, SOCSO, EIS and HRD Corp levy |
| CGPA, internship months, Klang Valley location | **Simulated** | Not published alongside income |
| How strongly those three relate to salary | **Assumed** | `config/parameters.json`, `simulation.weight_*` |
| Effect of the wage floor | **Simulated, forward-looking** | The floor is announced but not in force |

Neither KPT nor DOSM publishes individual-level graduate records, so the 1,000-row
dataset is simulated. It is built so that the salaries in each field reproduce the
published bands exactly; the assumed variables only decide which simulated graduate
receives which of those salaries. In practice:

- The **STEM coefficient** and every **policy number** rest on published data.
- The **CGPA, internship, location and interaction coefficients** show what the method
  recovers from the assumptions. They are not findings about the labour market.

Details and citations are in [`data/SOURCES.md`](data/SOURCES.md).

## Main results

- **49.7% of first-degree graduates earned RM2,500 or less** in the 2024 tracer study.
  This comes straight from the published bands, with no modelling. 30.6% earned RM2,000
  or less.
- With the floor alone, the graduate wage bill rises 13.5%. If employers also restore a
  quarter of the squeezed pay gaps up to RM3,200, it rises 14.4% and 70.1% of graduates
  get a raise.
- The estimate is sensitive to who is covered. Treating graduates who reported RM1,500
  or less as outside the floor (they are probably not in full-time work) cuts the rise
  to 7.1%. A 60% coverage rate for SME exemptions gives 8.5%.
- Exposure varies widely by field: 77.2% of education graduates and 75.0% of arts and
  humanities graduates were at or below RM2,500, against 27.7% in ICT.
- STEM graduates earn about 16% more than non-STEM graduates at an average CGPA.

These figures are from the committed run; `python run_pipeline.py` regenerates them.

## Run it

Python 3.11 or newer.

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python run_pipeline.py
python -m pytest tests
```

`run_pipeline.py` rebuilds everything from the two inputs (`data/skpg_2024_...csv` and
`config/parameters.json`). The seed is fixed, so the same inputs give the same outputs.

## What it produces

| File | Contents |
|---|---|
| `data/simulated_graduates.csv` | The 1,000-row calibrated sample |
| `outputs/executive_summary.md` | Results, interpretation, takeaways and limits, written from the fitted numbers |
| `outputs/FreshGrad_Salary_Regression_Model.xlsx` | The Excel model (below) |
| `outputs/coefficients.csv` | Estimates with classical and HC3 standard errors, t, p, 95% intervals and VIF |
| `outputs/diagnostics.csv` | Breusch-Pagan, White, Jarque-Bera, Shapiro-Wilk and Ramsey RESET |
| `outputs/functional_forms.csv` | Log versus level specification on a common likelihood scale |
| `outputs/quantile_regressions.csv` | The same model at the 25th, 50th and 75th percentiles |
| `outputs/policy_scenarios.csv` | Six wage-floor scenarios |
| `outputs/spillover_profile.csv` | Raise at each pre-policy salary in the central scenario |
| `outputs/model_fit.json` | R-squared, F, log-likelihood, AIC, BIC and the smearing factor |

## The model

```
ln(salary) = b0 + b1 CGPA_c + b2 internship_months + b3 STEM + b4 Klang_Valley
             + b5 (CGPA_c x STEM) + e
```

- **Log salary.** Coefficients read as approximate percentage effects. The log form
  fits better than salary in ringgit when the two likelihoods are put on the same scale.
- **Centred CGPA.** `CGPA_c` is CGPA minus the sample mean, so `b3` is the STEM gap at
  an average CGPA and the interaction does not inflate the VIFs.
- **HC3 standard errors** are reported whatever the heteroscedasticity tests say; they
  are valid either way.
- **Smearing correction.** `exp(prediction)` gives the median salary, not the mean, so
  ringgit predictions are multiplied by Duan's smearing factor.
- **No policy dummy.** The floor is not in force, so there is no post-policy cohort to
  estimate an effect from. The policy is simulated instead.

## The wage floor simulation

For a graduate earning `w` below the ceiling `C`, post-policy pay blends two extremes:

- no spillover: `max(w, F)`, where `F` is the floor;
- full spillover: the old range `[m, C]` squeezed evenly into `[F, C]`, where `m` is the
  minimum wage before the policy.

`alpha` (0.25 by default) is the weight on the second. Pay at or above `C` is unchanged.
The rule is continuous and never reverses anyone's pay ranking. All of `F`, `m`, `C` and
`alpha` are in `config/parameters.json` and on the workbook's Parameters tab.

## The Excel workbook

| Tab | What it does |
|---|---|
| `Parameters` | Policy and statutory inputs, each a named range |
| `Data_and_Residuals` | The dataset, the design matrix, fitted values and residuals as live formulas |
| `OLS_Native_Formulas` | The regression twice in native Excel: `LINEST`, and `MMULT(MINVERSE(MMULT(TRANSPOSE(X),X)),MMULT(TRANSPOSE(X),Y))`, with standard errors, t, p, intervals and fit statistics, each beside the statsmodels value |
| `Summary_Dashboard` | Coefficient table with significance stars and VIFs, and a what-if calculator: baseline salary, post-policy salary, wage compression adjustment, total cost of employment and take-home pay |
| `Policy_Simulation` | The six scenarios, the spillover profile and the calibration check |
| `Notes` | What is real, what is assumed, and the limits |

Change a salary or a parameter and the regression, the residuals and the calculator all
recalculate. Array formulas are entered as classic arrays and the statistical functions
are the long-standing ones (`TDIST`, `TINV`, `FDIST`), so the file works in Excel 2007
and later.

## Tests

`python -m pytest tests` runs 45 tests. Among other things they check that:

- the transcribed field rows add up to the report's published total and reproduce its
  overall distribution;
- changing the assumptions never changes the salaries drawn from the published bands;
- the coefficients, classical standard errors and HC3 standard errors equal the textbook
  matrix formulas;
- the compression rule is continuous, rank-preserving and never pays below the floor;
- every named range a workbook formula uses is defined.

One more test opens the workbook in Excel itself and compares Excel's coefficients and
calculator with Python's. It needs Windows with Excel installed:

```powershell
$env:FGSALARY_EXCEL = "1"; python -m pytest tests -k excel_itself
```

## Limits

- The simulation assumes no job losses, no cut in hours and full compliance by covered
  employers.
- Salaries within a band are spread evenly; the bottom band starts at RM500 and the top
  band is capped at RM15,000.
- SOCSO and EIS follow contribution tables with a wage ceiling in reality; flat rates
  are an approximation. Take-home pay excludes income tax (PCB).
- "STEM" here means engineering, ICT, and natural sciences, mathematics and statistics.
  Health and agriculture are counted as non-STEM.
- The salary data are from 2024. Scenario D shows the effect of pay growth before the
  floor starts.
