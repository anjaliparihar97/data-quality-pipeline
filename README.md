# 🔍 Statista Data Quality Audit Engine

**Author:** Anjali Parihar  
**Purpose:** Automated data quality checks for company financial data  
**Tech Stack:** Python · Pandas · Streamlit · OpenPyXL

---

## 📋 What This Does

Automatically checks company financial data across **3 quality dimensions:**

| Dimension | What It Checks |
|---|---|
| ✅ Completeness | Missing required fields (Revenue, Currency, Company Name) |
| 🔄 Consistency | Revenue/unit mismatches, fiscal period format issues |
| ⚠️ Validity | Negative revenue, statistical outliers, extreme YoY changes |

---

## 🚀 How To Run — 3 Simple Steps

### Step 1 — Install Python
Download Python 3.10+ from https://python.org/downloads
Make sure to tick "Add Python to PATH" during installation

### Step 2 — Install dependencies
Open Terminal (Mac/Linux) or Command Prompt (Windows) and run:
```
pip install -r requirements.txt
```

### Step 3 — Launch the app
```
streamlit run app.py
```

The app opens automatically in your browser at http://localhost:8501

---

## 📁 Project Structure

```
statista_quality_app/
│
├── app.py                  ← Main Streamlit application
├── quality_checks.py       ← Core quality check functions (reusable)
├── requirements.txt        ← Python dependencies
├── README.md               ← This file
├── run_app.bat             ← Windows one-click launcher
├── run_app.sh              ← Mac/Linux one-click launcher
└── sample_data/
    └── CaseStudy_Quality_sample25_1.xlsx  ← Sample input file
```

---

## 📥 Input
Any Excel file (.xlsx) with these columns:
- `companynameofficial`
- `REVENUE`
- `unit_REVENUE`
- `fiscalperiodend`
- `industrycode`
- `timevalue`
- `providerkey`

## 📤 Output
Excel file with 3 sheets:
- **Full Dataset** — all records with quality flags
- **Issues Only** — only flagged records
- **Quality Summary** — summary table for Power BI

---

## 🔧 Reuse For Any Dataset
This tool works with ANY financial dataset — not just Statista.
Just upload your Excel file and it runs automatically.

---

## 📊 Connect to Power BI
1. Run the app and download the flagged Excel output
2. Open Power BI Desktop
3. Get Data → Excel → select the downloaded file
4. Connect to Full Dataset, Issues Only, Quality Summary sheets
5. Build your dashboard

---

## ❓ Troubleshooting

| Problem | Solution |
|---|---|
| "streamlit not found" | Run `pip install streamlit` |
| "No module named pandas" | Run `pip install -r requirements.txt` |
| App doesn't open | Go to http://localhost:8501 manually |
| Port already in use | Run `streamlit run app.py --server.port 8502` |
