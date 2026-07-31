# Data Quality Audit Engine

**Author:** Anjali Parihar  
**Purpose:** Automated data quality checks for the data 
**Tech Stack:** Python · Pandas · Streamlit · OpenPyXL . PowerBI

---

## 📋 What This Does

Automatically checks company data across **3 quality dimensions:**

| Dimension | What It Checks |
|---|---|
| ✅ Completeness | Missing required fields  |
| 🔄 Consistency | Revenue/unit mismatches, fiscal period format issues |
| ⚠️ Validity | Negative revenue, statistical outliers, extreme YoY changes |

---

## 🚀 How To Run — Follow the steps below

### Step 1 — Install Python
Download Python 3.10+ from https://python.org/downloads
Make sure to tick "Add Python to PATH" during installation

### Step 2 — Install dependencies
Open Terminal (Mac/Linux) or Command Prompt (Windows) and run:
```
pip install -r requirements.txt
```

### Step 3 — Launch the app with teh following command
```
streamlit run app.py
```

The app opens automatically in your browser at http://localhost:8501

---

## 📁 Project Structure

```
## 📁 Repository Structure

```text
data-quality-pipeline/
│
├── Dataset/                                 # Raw input data directory
│   ├── CaseStudy_Quality_sample25_1.xlsx    # Original extraction file
│                         
├── Output/                                  # Pipeline output directory
│   ├── flagged_CaseStudy_Quality_sample25 1.xlsx # Processed Excel dataset with flags and the issues encountered
│   
│
├── PowerBI_File/                            # PowerBI Report with the issues encountered
│   └── QualityDimentionsOfCaseStudy.pbix
│
├── app.py                                   # Interactive Streamlit Web Application UI
├── quality_checks.py                        # Automated Quality Dimension Engine
├── requirements.txt                         # Project dependencies list
├── run_app.bat                              # 1-Click launcher script (Windows)
├── run_app.sh                               # 1-Click launcher script (macOS/Linux)
└── README.md                                # Executive project documentation
```

---



---

## 🔧 Reuse For Any Dataset
This tool works with any financial dataset with the features.
Just upload your Excel file and it runs the quality check automatically.

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
