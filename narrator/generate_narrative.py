from pathlib import Path
import json
import os
import re

from sklearn.preprocessing import normalize

ROOT = Path(__file__).resolve().parents[1]
FINDINGS_PATH = ROOT / "narrator" / "findings.json"

def generate_scr_narrative_offline(findings: dict) -> dict:
    revenue = findings["cleaned_total_revenue_inr"]
    raw = findings["raw_total_revenue_inr"]
    delta = findings["duplicate_reconciliation_delta_inr"]
    rates = findings["return_rate_by_payment"]
    risk = findings["highest_risk_segment"]
    peak = findings["true_peak_month"]
    inflated = findings["outlier_inflated_month"]

    narrative = f"""Situation

The cleaned order data shows total revenue of {revenue:,.2f} INR. Return rates vary by payment method, with COD at {rates["COD"]:.1f}%, CARD at {rates["CARD"]:.1f}%, and UPI at {rates["UPI"]:.1f}%.

Complication

The highest-risk segment is COD in Tier-{risk["city_tier"]} cities, with a {risk["return_rate_pct"]:.1f}% return rate. The raw revenue of {raw:,.2f} INR also included five duplicate orders. Removing those duplicates explains a reconciliation delta of {delta:,.2f} INR. The apparent January peak of {inflated["apparent_revenue_inr"]:,.2f} INR was inflated by the two bulk orders; after correction, January is {inflated["corrected_revenue_inr"]:,.2f} INR.

Resolution

Use the verified cleaned figures for operational and finance reporting, focus return investigation on COD in Tier-{risk["city_tier"]} cities, and use the outlier-corrected series for trend decisions. The true peak month is {peak["month"]} with {peak["revenue_inr"]:,.2f} INR in revenue."""
    return {"status": "success", "narrative": narrative, "tokens": None}

def generate_scr_narrative(findings: dict) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return generate_scr_narrative_offline(findings)

    try:
        from google import genai
        from google.genai.types import GenerateContentConfig, HttpOptions

        client = genai.Client(api_key=api_key)
        system_instruction = (
            "You are a senior data analyst writing for Mamaearth's regional ops and finance heads. "
            "Write exactly three labeled sections: Situation, Complication, Resolution. "
            "Every number in the output must come only from the supplied findings and must appear "
            "with the same value. Do not invent statistics, estimates, or additional figures."
        )
        contents = (
            "Create the SCR narrative from this supplied findings dictionary. "
            "Do not hardcode or invent any figures:\n"
            + json.dumps(findings, indent=2)
        )
        # temperature=0.0 because this is a factual business report, not creative writing.
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0,
                max_output_tokens=500,
                http_options=HttpOptions(timeout=15000),
            ),
        )
        usage = getattr(response, "usage_metadata", None)
        tokens = getattr(usage, "total_token_count", None) if usage else None
        return {
            "status": "success",
            "narrative": response.text,
            "tokens": tokens,
        }
    except Exception as err:
        return {"status": "error", "narrative": None, "message": str(err)}

def check_numeric_accuracy(narrative: str) -> bool:
    normalized = narrative.replace(",", "")
    checks = [
        ("97358.3", "cleaned total revenue"),
        ("44.4", "COD return rate"),
        ("54.5", "COD + Tier-2 return rate"),
        ("2501.9", "duplicate reconciliation delta"),
        ("March", "true peak month"),
        ("20318.9", "true peak revenue"),
    ]
    passed = True
    for needle, label in checks:
        ok = needle in normalized

        if label == "true peak month":
            ok = ok or "2026-03" in normalized
        print(f"{label}: {'PASS' if ok else 'FAIL'}")
        passed = passed and ok
    return passed

def main():
    findings = json.loads(FINDINGS_PATH.read_text())
    result = generate_scr_narrative(findings)
    print("Narrative status:", result["status"])
    if result["status"] == "success":
        print(result["narrative"])
        check_numeric_accuracy(result["narrative"])
        (ROOT / "narrator" / "sample_output.txt").write_text(result["narrative"])
    else:
        print("Online Gemini call failed; using deterministic offline fallback.")
        fallback = generate_scr_narrative_offline(findings)
        print(fallback["narrative"])
        check_numeric_accuracy(fallback["narrative"])
        (ROOT / "narrator" / "sample_output.txt").write_text(fallback["narrative"])

if __name__ == "__main__":
    main()
