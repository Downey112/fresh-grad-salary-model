"""Run the whole project: build the sample, fit the model, simulate the policy, write the outputs.

    python run_pipeline.py

Everything is rebuilt from data/skpg_2024_first_degree_income_by_field.csv and
config/parameters.json. The same inputs always give the same outputs.
"""
import json

from fgsalary import config, data, model, policy, report, workbook


def main():
    parameters = config.load_parameters()
    skpg = data.load_skpg()
    config.OUTPUT_DIR.mkdir(exist_ok=True)

    sample = data.simulate(parameters, skpg)
    sample.to_csv(config.SAMPLE_PATH, index=False)

    result = model.fit(sample)
    scenarios = policy.run_scenarios(sample["salary"], parameters)
    profile = policy.spillover_profile(parameters)

    result["coefficients"].to_csv(config.OUTPUT_DIR / "coefficients.csv", index=False)
    result["diagnostics"].to_csv(config.OUTPUT_DIR / "diagnostics.csv", index=False)
    result["forms"].to_csv(config.OUTPUT_DIR / "functional_forms.csv", index=False)
    result["quantiles"].to_csv(config.OUTPUT_DIR / "quantile_regressions.csv", index=False)
    scenarios.to_csv(config.OUTPUT_DIR / "policy_scenarios.csv", index=False)
    profile.to_csv(config.OUTPUT_DIR / "spillover_profile.csv", index=False)
    with open(config.OUTPUT_DIR / "model_fit.json", "w", encoding="utf-8") as handle:
        json.dump(
            {**result["fit_statistics"], "smearing_factor": result["smearing"],
             "cgpa_mean": result["cgpa_mean"], "heteroscedastic": result["heteroscedastic"],
             **{f"residual_{name}": value for name, value in result["residual_moments"].items()}},
            handle, indent=2,
        )

    workbook_path = workbook.build_workbook(
        result, scenarios, profile, parameters, skpg, config.OUTPUT_DIR / config.WORKBOOK_NAME)
    summary_path = config.OUTPUT_DIR / "executive_summary.md"
    summary_path.write_text(
        report.build_summary(result, scenarios, profile, parameters, skpg), encoding="utf-8")

    print(result["classical"].summary())
    print("\nHC3 robust results")
    print(result["coefficients"][
        ["label", "coefficient", "hc3_std_error", "hc3_t_value", "hc3_p_value", "hc3_stars", "vif"]
    ].to_string(index=False))
    print("\nDiagnostics")
    print(result["diagnostics"][["test", "statistic", "p_value", "rejected_at_5pct"]].to_string(index=False))
    print("\nPolicy scenarios")
    print(scenarios[
        ["scenario", "share_below_floor", "share_receiving_raise", "mean_raise_if_raised", "wage_bill_increase"]
    ].to_string(index=False))
    print(f"\nWorkbook: {workbook_path}")
    print(f"Summary:  {summary_path}")


if __name__ == "__main__":
    main()
