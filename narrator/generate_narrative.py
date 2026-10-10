from pathlib import Path
import json
import os

ROOT = Path(__file__).resolve().parents[1]
FINDINGS_PATH = ROOT / "narrator" / "findings.json"
OUTPUT_PATH = ROOT / "narrator" / "sample_output.txt"


def build_verified_narrative(findings: dict) -> str:
    """Build the SCR report from verified findings; never rely on the LLM for figures."""
    revenue = findings["cleaned_total_revenue_inr"]
    raw = findings["raw_total_revenue_inr"]
    delta = findings["duplicate_reconciliation_delta_inr"]
    rates = findings["return_rate_by_payment"]
    risk = findings["highest_risk_segment"]
    peak = findings["true_peak_month"]
    inflated = findings["outlier_inflated_month"]

    return f"""Situation

The cleaned order data shows total revenue of {revenue:,.2f} INR. Return rates vary by payment method, with COD at {rates['COD']:.1f}%, CARD at {rates['CARD']:.1f}%, and UPI at {rates['UPI']:.1f}%.

Complication

The highest-risk segment is COD in Tier-{risk['city_tier']} cities, with a {risk['return_rate_pct']:.1f}% return rate. The raw revenue of {raw:,.2f} INR also included five duplicate orders. Removing those duplicates explains a reconciliation delta of {delta:,.2f} INR. The apparent January peak of {inflated['apparent_revenue_inr']:,.2f} INR was inflated by the two bulk orders; after correction, January is {inflated['corrected_revenue_inr']:,.2f} INR.

Resolution

Use the verified cleaned figures for operational and finance reporting, focus return investigation on COD in Tier-{risk['city_tier']} cities, and use the outlier-corrected series for trend decisions. The true peak month is {peak['month']} with {peak['revenue_inr']:,.2f} INR in revenue."""


def generate_gemini_interpretation(findings: dict) -> dict:
    """Request interpretation only. Verified figures are added separately by Python."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "status": "skipped",
            "interpretation": None,
            "message": "GEMINI_API_KEY is not set; using offline report.",
        }

    client = None
    try:
        from google import genai
        from google.genai.types import GenerateContentConfig, HttpOptions

        client = genai.Client(
            api_key=api_key,
            http_options=HttpOptions(timeout=60000),
        )
        prompt = (
            "You are a senior data analyst advising Mamaearth regional operations and finance leaders. "
            "Using the findings JSON below, provide exactly three concise bullet points: "
            "(1) overall business situation, (2) key return-risk complication, and "
            "(3) recommended operational action. Explain the implications, not the numeric values. "
            "Do not include headings, repeat metrics, or invent facts. Keep the response under 150 words.\n\n"
            "Findings JSON:\n" + json.dumps(findings, indent=2)
        )
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=1500,
            ),
        )

        interpretation = (getattr(response, "text", None) or "").strip()
        if not interpretation:
            return {
                "status": "error",
                "interpretation": None,
                "message": "Gemini returned an empty interpretation.",
            }
        return {
            "status": "success",
            "interpretation": interpretation,
            "tokens": getattr(getattr(response, "usage_metadata", None), "total_token_count", None),
        }
    except Exception as err:
        return {"status": "error", "interpretation": None, "message": str(err)}
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                pass


def check_numeric_accuracy(narrative: str, findings: dict) -> bool:
    """Check required figures against findings and ensure the SCR headings exist."""
    normalized = narrative.replace(",", "").lower()
    rates = findings["return_rate_by_payment"]
    risk = findings["highest_risk_segment"]
    delta = findings["duplicate_reconciliation_delta_inr"]
    peak = findings["true_peak_month"]

    checks = [
        (f"{findings['cleaned_total_revenue_inr']:.1f}".lower(), "cleaned total revenue"),
        (f"{rates['COD']:.1f}".lower(), "COD return rate"),
        (f"{risk['return_rate_pct']:.1f}".lower(), "COD + Tier-2 return rate"),
        (f"{delta:.1f}".lower(), "duplicate reconciliation delta"),
        (str(peak["month"]).lower(), "true peak month"),
        (f"{peak['revenue_inr']:.1f}".lower(), "true peak revenue"),
    ]
    passed = True
    for needle, label in checks:
        ok = needle in normalized
        if label == "true peak month" and not ok:
            month = str(peak["month"])
            ok = month[:7] in normalized or month[-2:] in normalized
        print(f"{label}: {'PASS' if ok else 'FAIL'}")
        passed = passed and ok

    for heading in ("situation", "complication", "resolution"):
        ok = heading in normalized
        print(f"{heading.title()} section: {'PASS' if ok else 'FAIL'}")
        passed = passed and ok
    return passed


def main() -> None:
    findings = json.loads(FINDINGS_PATH.read_text(encoding="utf-8"))
    verified_narrative = build_verified_narrative(findings)
    gemini = generate_gemini_interpretation(findings)

    print("Gemini status:", gemini["status"])
    final_narrative = verified_narrative
    if gemini["status"] == "success":
        final_narrative += (
            "\n\nGemini-generated business interpretation\n\n"
            + gemini["interpretation"]
        )
        print("Gemini interpretation received.")
    else:
        if gemini.get("message"):
            print("Gemini message:", gemini["message"])
        print("Using deterministic offline report; no Gemini interpretation was added.")

    print("\nFinal narrative:\n")
    print(final_narrative)
    valid = check_numeric_accuracy(final_narrative, findings)
    print("Validation:", "PASS" if valid else "FAIL")

    if valid:
        OUTPUT_PATH.write_text(final_narrative + "\n", encoding="utf-8")
        print(f"Saved validated narrative to {OUTPUT_PATH}.")
    else:
        print("Output was not saved because validation failed.")


if __name__ == "__main__":
    main()
