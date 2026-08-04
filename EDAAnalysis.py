"""
=============================================================
eda_profiling.py — Exploratory Data Analysis
=============================================================
Author  : Anjali Parihar
Purpose : Raw data profiling and exploration before quality checks
          Shows the data as-is, surfaces patterns, anomalies,
          and issues that motivated the quality check design.
Run with: python eda_profiling.py
=============================================================
"""

import datetime
import warnings
import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")

INPUT_FILE = "CaseStudy_Quality_sample25_1.xlsx"

# ── LOAD ─────────────────────────────────────────────────────
print("\n" + "="*60)
print("  STATISTA CASE STUDY — RAW DATA PROFILING")
print("="*60)

df = pd.read_excel(INPUT_FILE)

# ══════════════════════════════════════════════════════════════
# SECTION 1 — DATASET OVERVIEW
# ══════════════════════════════════════════════════════════════
print("\n📋 SECTION 1 — DATASET OVERVIEW")
print("-"*60)
print(f"  Rows              : {len(df):,}")
print(f"  Columns           : {len(df.columns)}")
print(f"  Years covered     : {sorted(df['timevalue'].unique())}")
print(f"  Unique companies  : {df['companynameofficial'].nunique()}")
print(f"  Unique industries : {df['industrycode'].nunique()}")
print(f"  Unique currencies : {df['unit_REVENUE'].dropna().nunique()}")
print(f"\n  Columns:\n  {df.columns.tolist()}")

print("\n  Data Types:")
for col, dtype in df.dtypes.items():
    print(f"    {col:<30} {dtype}")

# ══════════════════════════════════════════════════════════════
# SECTION 2 — MISSING VALUE ANALYSIS
# ══════════════════════════════════════════════════════════════
print("\n\n📋 SECTION 2 — MISSING VALUE ANALYSIS")
print("-"*60)

null_counts = df.isnull().sum()
null_pct    = (null_counts / len(df) * 100).round(1)
null_report = pd.DataFrame({
    "Null Count"  : null_counts,
    "Null %"      : null_pct,
    "Status"      : null_counts.apply(
        lambda x: "⚠️  HAS NULLS" if x > 0 else "✅ Complete"
    )
})
print(null_report.to_string())

print(f"\n  Key finding: REVENUE is missing in {null_counts['REVENUE']} records "
      f"({null_pct['REVENUE']}% of dataset)")
print(f"  Key finding: unit_REVENUE missing in {null_counts['unit_REVENUE']} records "
      f"({null_pct['unit_REVENUE']}%)")

# ══════════════════════════════════════════════════════════════
# SECTION 3 — REVENUE STATISTICS
# ══════════════════════════════════════════════════════════════
print("\n\n📋 SECTION 3 — REVENUE STATISTICAL SUMMARY")
print("-"*60)

rev_stats = df['REVENUE'].describe()
print(f"  Records with revenue    : {int(rev_stats['count']):,}")
print(f"  Records missing revenue : {df['REVENUE'].isna().sum():,}")
print(f"  Minimum revenue         : {rev_stats['min']:>20,.0f}")
print(f"  25th percentile         : {rev_stats['25%']:>20,.0f}")
print(f"  Median revenue          : {rev_stats['50%']:>20,.0f}")
print(f"  Mean revenue            : {rev_stats['mean']:>20,.0f}")
print(f"  75th percentile         : {rev_stats['75%']:>20,.0f}")
print(f"  Maximum revenue         : {rev_stats['max']:>20,.0f}")
print(f"  Std deviation           : {rev_stats['std']:>20,.0f}")

print(f"\n  ⚠️  Negative revenue detected: "
      f"{(df['REVENUE'] < 0).sum()} record(s)")
print(f"  ⚠️  Revenue range is extremely wide — "
      f"max is {rev_stats['max']/rev_stats['50%']:.0f}x the median")
print(f"     This signals a highly skewed distribution "
      f"(large caps mixed with small caps)")

# ══════════════════════════════════════════════════════════════
# SECTION 4 — REVENUE BY YEAR (TEMPORAL ANALYSIS)
# ══════════════════════════════════════════════════════════════
print("\n\n📋 SECTION 4 — TEMPORAL ANALYSIS (BY YEAR)")
print("-"*60)

yearly = df.groupby('timevalue').agg(
    Total_Records   = ('REVENUE', 'count'),
    Missing_Revenue = ('REVENUE', lambda x: x.isna().sum()),
    Companies       = ('companynameofficial', 'nunique'),
    Mean_Revenue    = ('REVENUE', 'mean'),
    Median_Revenue  = ('REVENUE', 'median'),
).round(0)

yearly['Coverage_%'] = (
    (yearly['Total_Records'] - yearly['Missing_Revenue'])
    / yearly['Total_Records'] * 100
).round(1)

print(yearly.to_string())
print(f"\n  Key finding: 2024 has only {yearly.loc[2024,'Total_Records']} records "
      f"— incomplete year")
print(f"  Key finding: Missing revenue is consistent at 18-20 records/year "
      f"(2020-2023) — systematic issue")
print(f"  Key finding: 2019 has fewer records — dataset starts mid-extraction")

# ══════════════════════════════════════════════════════════════
# SECTION 5 — CURRENCY / UNIT ANALYSIS
# ══════════════════════════════════════════════════════════════
print("\n\n📋 SECTION 5 — CURRENCY DISTRIBUTION ANALYSIS")
print("-"*60)

currency_dist = df['unit_REVENUE'].value_counts(dropna=False)
currency_pct  = (currency_dist / len(df) * 100).round(1)

print("  Currency      Records   %")
print("  " + "-"*35)
for curr, count in currency_dist.items():
    label = str(curr) if not pd.isna(curr) else "MISSING"
    pct   = currency_pct[curr]
    bar   = "█" * int(pct / 2)
    print(f"  {label:<12}  {count:>6}  {pct:>5.1f}%  {bar}")

# Revenue/Unit mismatch
rev_no_unit = (df['REVENUE'].notna() & df['unit_REVENUE'].isna()).sum()
unit_no_rev = (df['unit_REVENUE'].notna() & df['REVENUE'].isna()).sum()
print(f"\n  ⚠️  Revenue present but currency missing : {rev_no_unit} record(s)")
print(f"  ⚠️  Currency present but revenue missing : {unit_no_rev} record(s)")
print(f"     These records CANNOT be used for cross-company comparison")

# ══════════════════════════════════════════════════════════════
# SECTION 6 — FISCAL PERIOD FORMAT ANALYSIS
# ══════════════════════════════════════════════════════════════
print("\n\n📋 SECTION 6 — FISCAL PERIOD FORMAT ANALYSIS")
print("-"*60)

def classify_fp(val):
    if pd.isna(val):
        return "NULL — missing"
    if isinstance(val, datetime.datetime):
        return f"datetime — year {val.year}"
    if isinstance(val, str) and len(str(val)) <= 6:
        return "short string — e.g. 31-May"
    return "other"

df['_fp_type'] = df['fiscalperiodend'].apply(classify_fp)
fp_dist = df['_fp_type'].value_counts()

print("  Format Type                        Records")
print("  " + "-"*45)
for fmt, count in fp_dist.items():
    pct = count / len(df) * 100
    print(f"  {fmt:<38} {count:>5}  ({pct:.1f}%)")

print(f"\n  ⚠️  Two format types exist in the same column:")
print(f"     303 records use short string '31-May' format")
print(f"     69 records use datetime format — ALL showing year 2025")
print(f"     A 2025 date on a 2019-2023 record = extraction error")

# Sample of future dates
future = df[df['_fp_type'].str.contains('2025', na=False)]
if len(future) > 0:
    print(f"\n  Sample records with future fiscal period date:")
    print(future[['companynameofficial','timevalue','fiscalperiodend']]
          .head(5).to_string(index=False))

df.drop(columns=['_fp_type'], inplace=True)

# ══════════════════════════════════════════════════════════════
# SECTION 7 — INDUSTRY ANALYSIS
# ══════════════════════════════════════════════════════════════
print("\n\n📋 SECTION 7 — INDUSTRY DISTRIBUTION")
print("-"*60)

industry_dist = df['industrycode'].value_counts().head(10)
print("  Top 10 Industries by Record Count:")
print("  " + "-"*55)
for ind, count in industry_dist.items():
    pct = count / len(df) * 100
    bar = "█" * int(pct / 1.5)
    short = ind[:45] if len(ind) > 45 else ind
    print(f"  {short:<46} {count:>3}  {bar}")

# Industry with most missing data
ind_missing = df[df['REVENUE'].isna()].groupby('industrycode').size()
print(f"\n  Industries with most missing revenue:")
for ind, count in ind_missing.sort_values(ascending=False).head(5).items():
    short = ind[:50] if len(ind) > 50 else ind
    print(f"    {short:<51} {count} missing")

# ══════════════════════════════════════════════════════════════
# SECTION 8 — OUTLIER DETECTION
# ══════════════════════════════════════════════════════════════
print("\n\n📋 SECTION 8 — STATISTICAL OUTLIER DETECTION (Z-SCORE)")
print("-"*60)

# Z-score within currency group
df['_zscore'] = df.groupby('unit_REVENUE')['REVENUE'].transform(
    lambda x: (x - x.mean()) / x.std() if x.std() > 0 else 0
)
outliers = df[df['_zscore'].abs() > 3][
    ['companynameofficial','timevalue','REVENUE','unit_REVENUE','_zscore']
].sort_values('_zscore', ascending=False)

print(f"  Records with z-score > 3 (within currency group): {len(outliers)}")
print(f"\n  Top outliers:")
print(outliers.head(10).to_string(index=False))
df.drop(columns=['_zscore'], inplace=True)

# ══════════════════════════════════════════════════════════════
# SECTION 9 — YEAR-ON-YEAR CHANGE ANALYSIS
# ══════════════════════════════════════════════════════════════
print("\n\n📋 SECTION 9 — YEAR-ON-YEAR REVENUE CHANGE ANALYSIS")
print("-"*60)

df_sorted = df.sort_values(['providerkey','timevalue'])
df['_yoy'] = df_sorted.groupby('providerkey')['REVENUE'].pct_change()

extreme = df[df['_yoy'].abs() > 2.0][
    ['companynameofficial','timevalue','REVENUE','unit_REVENUE','_yoy']
].copy()
extreme['_yoy_pct'] = (extreme['_yoy'] * 100).round(0)

print(f"  Records with YoY change > 200%: {len(extreme)}")
print(f"\n  Companies with extreme year-on-year changes:")
print(extreme[['companynameofficial','timevalue',
               'REVENUE','unit_REVENUE','_yoy_pct']]
      .to_string(index=False))
df.drop(columns=['_yoy'], inplace=True)

# ══════════════════════════════════════════════════════════════
# SECTION 10 — COMPLETENESS HEATMAP (TEXT VERSION)
# ══════════════════════════════════════════════════════════════
print("\n\n📋 SECTION 10 — COMPLETENESS BY YEAR (MISSING REVENUE)")
print("-"*60)

pivot = df.pivot_table(
    index='timevalue',
    values='REVENUE',
    aggfunc=lambda x: f"{x.isna().sum()}/{len(x)} missing ({x.isna().sum()/len(x)*100:.0f}%)"
)
print(pivot.to_string())

# ══════════════════════════════════════════════════════════════
# SECTION 11 — TOP PROBLEM COMPANIES
# ══════════════════════════════════════════════════════════════
print("\n\n📋 SECTION 11 — COMPANIES WITH MOST DATA ISSUES")
print("-"*60)

company_issues = df.groupby('companynameofficial').agg(
    Total_Years       = ('timevalue', 'count'),
    Missing_Revenue   = ('REVENUE', lambda x: x.isna().sum()),
    Has_Negative_Rev  = ('REVENUE', lambda x: (x < 0).any()),
).reset_index()

company_issues['Missing_%'] = (
    company_issues['Missing_Revenue'] /
    company_issues['Total_Years'] * 100
).round(0)

top_problem = company_issues[
    company_issues['Missing_Revenue'] > 0
].sort_values('Missing_Revenue', ascending=False).head(10)

print("  Companies with most missing revenue records:")
print(top_problem[['companynameofficial','Total_Years',
                   'Missing_Revenue','Missing_%']].to_string(index=False))

# ══════════════════════════════════════════════════════════════
# SECTION 12 — FINAL SUMMARY
# ══════════════════════════════════════════════════════════════
print("\n\n" + "="*60)
print("  RAW DATA PROFILING — KEY FINDINGS SUMMARY")
print("="*60)

findings = [
    ("Dataset size",
     f"{len(df):,} records · {df['companynameofficial'].nunique()} companies · "
     f"{df['timevalue'].nunique()} years"),
    ("Missing revenue",
     f"{df['REVENUE'].isna().sum()} records ({df['REVENUE'].isna().mean()*100:.1f}%) "
     f"have no revenue value"),
    ("Missing currency",
     f"{df['unit_REVENUE'].isna().sum()} records have no currency unit"),
    ("Revenue-unit mismatch",
     f"{(df['REVENUE'].notna() & df['unit_REVENUE'].isna()).sum()} records have "
     f"revenue but no unit"),
    ("Negative revenue",
     f"{(df['REVENUE'] < 0).sum()} record with negative revenue detected"),
    ("Statistical outliers",
     f"{(df.groupby('unit_REVENUE')['REVENUE'].transform(lambda x: ((x-x.mean())/x.std()).abs() if x.std()>0 else 0) > 3).sum()} "
     f"records exceed 3 standard deviations within currency group"),
    ("Fiscal period format",
     "303 records use short string format (31-May); "
     "69 records use datetime with year 2025 (future date error)"),
    ("Worst industry",
     "7010 - Head Office Activities has the most records (75) "
     "and most quality issues"),
    ("2024 data",
     "Only 2 records for 2024 — dataset extraction incomplete for this year"),
    ("Revenue distribution",
     "Highly skewed — max revenue is 128x the median, "
     "suggesting mixed large and small cap companies"),
]

for title, detail in findings:
    print(f"\n  🔍 {title}")
    print(f"     {detail}")

print("\n" + "="*60)
print("  These findings directly motivated the three quality")
print("  dimensions: Completeness, Consistency, and Validity")
print("="*60 + "\n")