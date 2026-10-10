# Mamaearth Returns & Growth Intelligence Pipeline

**Capstone Project — Data Analytics with AI & GenAI**  
**E&ICT Academy, IIT Roorkee**

An end-to-end analytics pipeline for investigating order returns and revenue trends using SQL, Python, data cleaning, exploratory data analysis (EDA), visualizations, and Gemini-powered Situation–Complication–Resolution (SCR) narrative generation with an offline fallback.

## Project Structure

```text
mamaearth-returns-growth-intelligence/
├── analysis/
│   ├── clean_and_eda.py
│   └── visualize.py
├── data/
│   ├── customers.csv
│   ├── orders.csv
│   └── products.csv
├── narrator/
│   ├── generate_narrative.py
│   ├── findings.json
│   └── sample_output.txt
├── sql/
│   ├── schema.sql
│   ├── seed_data.sql
│   └── reports.sql
├── visualizations/
│   ├── monthly_revenue_trend.png
│   └── return_rate_by_payment.png
├── mamaearth.db
└── README.md
```

The SQLite database `mamaearth.db` is intentionally included as a **raw, uncleaned** submission artifact. The original files in `data/` must also remain unchanged. Part 1 SQL reports run against the raw database; Part 2 reads the original CSV files independently and performs cleaning in Python. Do not manually edit the CSVs or pre-clean the database: the raw SQL layer is expected to retain 180 orders, including duplicates O0176–O0180 and the original missing values.

## Features

- **SQL data model and reporting:** Schema creation, seed data, and analytical SQL reports.
- **Data cleaning and EDA:** Python/Pandas processing, duplicate handling, missing-value treatment, and outlier investigation.
- **Visualizations:** Monthly revenue trend after outlier correction and return rates by payment method.
- **Gemini-assisted narrative generation:** Python builds the verified Situation–Complication–Resolution (SCR) report from `findings.json`; Gemini generates an additional business interpretation from the same findings.
- **Offline fallback:** If the terminal environment variable `GEMINI_API_KEY` is missing or the Gemini request fails, the verified SCR report is still generated without an API call.
- **Validation:** Checks six required numeric findings and the presence of the Situation, Complication, and Resolution sections before saving the output. These checks validate the verified report; they do not independently prove the factual completeness of Gemini's interpretation.

## Dataset and Key Findings

The project analyzes customer, product, and order CSV data. Expected analytical figures include:

| Metric | Result |
|---|---:|
| Customers | 45 |
| Products | 16 |
| Raw orders | 180 |
| Raw revenue | ₹99,860.20 |
| Cleaned revenue | ₹97,358.30 |
| Duplicate reconciliation delta | ₹2,501.90 |
| COD return rate | 44.4% |
| UPI return rate | 18.9% |
| CARD return rate | 14.7% |
| COD Tier-2 return rate | 54.5% |
| Outlier-corrected peak month | March 2026 |
| Corrected March revenue | ₹20,318.90 |

The analysis identifies five duplicate orders (O0176–O0180), missing discounts, missing ratings, and unusually large order quantities that affect the revenue trend.

## Requirements

- Python 3.9 or newer
- SQLite 3
- Python packages: `pandas`, `matplotlib`
- Optional for online AI narration: `google-genai`

Install the Python dependencies from the project root:

```bash
python -m pip install pandas matplotlib google-genai
```

## Run the Project

Run commands from the repository root.

### 1. Database setup

The submitted `mamaearth.db` is included for convenience and must remain raw. To recreate it from scratch, run the SQL scripts in this order. Run the SQL reports before the Python cleaning pipeline so the raw and cleaned results remain distinct.

**Windows PowerShell:**

```powershell
sqlite3 mamaearth.db ".read sql/schema.sql"
sqlite3 mamaearth.db ".read sql/seed_data.sql"
sqlite3 mamaearth.db ".read sql/reports.sql"
```

**macOS/Linux:**

```bash
sqlite3 mamaearth.db < sql/schema.sql
sqlite3 mamaearth.db < sql/seed_data.sql
sqlite3 mamaearth.db < sql/reports.sql
```

> Recreating the database may add duplicate seed rows if run against an already populated database. For a fresh rebuild, back up or remove the existing database first, then run the commands above.

### 2. Clean data and run EDA

```bash
python analysis/clean_and_eda.py
```

This step performs cleaning and analysis and generates or refreshes `narrator/findings.json` with key numeric findings used by the narrative generator.

### 3. Generate visualizations

```bash
python analysis/visualize.py
```

The charts are saved in the `visualizations/` directory.

### 4. Generate the SCR narrative

The generator supports Gemini online generation and an offline fallback.

**Windows PowerShell — online Gemini mode:**

```powershell
$env:GEMINI_API_KEY = "YOUR_API_KEY"
python narrator/generate_narrative.py
```

**macOS/Linux — online Gemini mode:**

```bash
export GEMINI_API_KEY="YOUR_API_KEY"
python narrator/generate_narrative.py
```

Obtain your API key from Google AI Studio. Keep the real key private; do not paste it into source code, commit it, or include it in screenshots.

**Windows PowerShell — offline mode:**

```powershell
Remove-Item Env:GEMINI_API_KEY -ErrorAction SilentlyContinue
python narrator/generate_narrative.py
```

**macOS/Linux — offline mode:**

```bash
unset GEMINI_API_KEY
python narrator/generate_narrative.py
```

The generated report is saved to `narrator/sample_output.txt`. In online mode, the saved report contains the verified SCR narrative plus Gemini's business interpretation. In offline mode, it contains the verified SCR narrative without a Gemini interpretation. To document the online Gemini path, run the generator with your API key configured and confirm that the console reports Gemini success and validation passes. The numeric checks validate the required figures and SCR headings; review Gemini's interpretation separately for completeness and unsupported claims.

## Expected Analytical Highlights

- **Payment-method returns:** COD 44.4%, UPI 18.9%, and CARD 14.7%.
- **Highest-risk segment:** COD orders in Tier-2 cities, with a 54.5% return rate.
- **Duplicate reconciliation:** Five duplicate orders (O0176–O0180) account for ₹2,501.90 in raw-revenue difference.
- **Outlier-corrected trend:** March 2026 is the true peak month at ₹20,318.90.
- **January outlier impact:** Apparent January revenue of ₹29,582.10 is corrected to ₹11,637.10 after the bulk-order outliers are addressed.

Use corrected figures for trend analysis and the cleaned dataset for operational and finance reporting.

## Repository and Security Notes

- The repository is intended to be public for capstone review.
- `mamaearth.db` is intentionally included as a submission artifact.
- Never commit a real Gemini API key, an `.env` file containing secrets, or credentials. Enter the key only in the terminal as the `GEMINI_API_KEY` environment variable; never hardcode it in Python or README files.
- Keep the SQL scripts, unchanged raw input CSV files, Python source files, generated findings, narrative sample, raw database, and chart images in the repository.
- Remove accidental placeholder files such as `sql/junk` or `visualizations/junk` before submission.
