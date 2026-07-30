"""
=============================================================
quality_checks.py
=============================================================
Reusable data quality check functions.
Can be imported into any Python script or notebook.

Usage:
    from quality_checks import run_all_checks
    df_flagged = run_all_checks(df)
=============================================================
"""

import io
import numpy as np
import pandas as pd

# ── CONFIG ──────────────────────────────────────────────────
REQUIRED_FIELDS      = [
    "companynameofficial", "REVENUE",
    "unit_REVENUE", "fiscalperiodend", "industrycode"
]
REVENUE_OUTLIER_STD  = 3      # flag if > 3 std devs from mean
YOY_CHANGE_THRESHOLD = 2.0    # flag if YoY change > 200%


# ══════════════════════════════════════════════════════════════
# DIMENSION 1 — COMPLETENESS
# ══════════════════════════════════════════════════════════════
def check_completeness(df: pd.DataFrame) -> pd.DataFrame:
    """
    Check for missing values in required fields.

    Args:
        df: Input DataFrame

    Returns:
        DataFrame with two new columns:
            flag_completeness        (bool)
            flag_completeness_detail (str)
    """
    def _missing_fields(row):
        return [f for f in REQUIRED_FIELDS
                if f in row.index and pd.isna(row[f])]

    df = df.copy()
    df["_missing"] = df.apply(_missing_fields, axis=1)
    df["flag_completeness"] = df["_missing"].apply(lambda x: len(x) > 0)
    df["flag_completeness_detail"] = df["_missing"].apply(
        lambda x: "Missing: " + ", ".join(x) if x else "OK"
    )
    df.drop(columns=["_missing"], inplace=True)
    return df


# ══════════════════════════════════════════════════════════════
# DIMENSION 2 — CONSISTENCY
# ══════════════════════════════════════════════════════════════
def check_consistency(df: pd.DataFrame) -> pd.DataFrame:
    """
    Check for internal contradictions in the data.

    Args:
        df: Input DataFrame

    Returns:
        DataFrame with two new columns:
            flag_consistency        (bool)
            flag_consistency_detail (str)
    """
    df = df.copy()

    # Rule 1: Revenue/unit mismatch
    rev_no_unit = df["REVENUE"].notna() & df["unit_REVENUE"].isna()
    unit_no_rev = df["unit_REVENUE"].notna() & df["REVENUE"].isna()

    # Rule 2: Inconsistent fiscal period format per company
    def _is_long_format(val):
        return isinstance(val, pd.Timestamp) or (
            isinstance(val, str) and len(val) > 7
        )

    df["_fp_long"] = df["fiscalperiodend"].apply(_is_long_format)
    mixed_companies = (
        df.groupby("providerkey")["_fp_long"]
        .nunique()
        .pipe(lambda s: s[s > 1].index)
    )
    fp_mismatch = df["providerkey"].isin(mixed_companies)

    def _detail(row):
        parts = []
        if row["_rev_no_unit"]:  parts.append("Revenue present but unit missing")
        if row["_unit_no_rev"]:  parts.append("Unit present but revenue missing")
        if row["_fp_mismatch"]:  parts.append("Inconsistent fiscal period format")
        return "; ".join(parts) if parts else "OK"

    df["_rev_no_unit"] = rev_no_unit
    df["_unit_no_rev"] = unit_no_rev
    df["_fp_mismatch"] = fp_mismatch

    df["flag_consistency"]        = rev_no_unit | unit_no_rev | fp_mismatch
    df["flag_consistency_detail"] = df.apply(_detail, axis=1)
    df.drop(columns=["_rev_no_unit","_unit_no_rev","_fp_mismatch","_fp_long"],
            inplace=True)
    return df


# ══════════════════════════════════════════════════════════════
# DIMENSION 3 — VALIDITY
# ══════════════════════════════════════════════════════════════
def check_validity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Check for implausible values.

    Args:
        df: Input DataFrame

    Returns:
        DataFrame with two new columns:
            flag_validity        (bool)
            flag_validity_detail (str)
    """
    df = df.copy()

    # Rule 1: Negative revenue
    negative_rev = df["REVENUE"] < 0

    # Rule 2: Statistical outlier within currency group
    df["_zscore"] = df.groupby("unit_REVENUE")["REVENUE"].transform(
        lambda x: (x - x.mean()) / x.std() if x.std() > 0 else 0
    )
    is_outlier = df["_zscore"].abs() > REVENUE_OUTLIER_STD

    # Rule 3: Extreme year-on-year change
    df_sorted = df.sort_values(["providerkey", "timevalue"])
    df["_yoy"] = df_sorted.groupby("providerkey")["REVENUE"].pct_change()
    extreme_yoy = df["_yoy"].abs() > YOY_CHANGE_THRESHOLD

    def _detail(row):
        parts = []
        if row["_neg"]:
            parts.append(f"Negative revenue ({row['REVENUE']:,.0f})")
        if row["_out"] and not pd.isna(row["_zscore"]):
            parts.append(f"Statistical outlier (z-score={row['_zscore']:.1f})")
        if row["_yoy2"] and not pd.isna(row["_yoy"]):
            parts.append(f"Extreme YoY change ({row['_yoy']*100:.0f}%)")
        return "; ".join(parts) if parts else "OK"

    df["_neg"]  = negative_rev
    df["_out"]  = is_outlier
    df["_yoy2"] = extreme_yoy

    df["flag_validity"]        = negative_rev | is_outlier | extreme_yoy
    df["flag_validity_detail"] = df.apply(_detail, axis=1)
    df.drop(columns=["_neg","_out","_yoy2","_zscore","_yoy"], inplace=True)
    return df


# ══════════════════════════════════════════════════════════════
# OVERALL FLAG
# ══════════════════════════════════════════════════════════════
def add_overall_flag(df: pd.DataFrame) -> pd.DataFrame:
    """
    Combine all dimension flags into a single overall flag.

    Args:
        df: DataFrame with all three dimension flags

    Returns:
        DataFrame with flag_any_issue and quality_status columns
    """
    df = df.copy()
    flags = ["flag_completeness", "flag_consistency", "flag_validity"]
    df["flag_any_issue"] = df[flags].any(axis=1)

    def _status(row):
        issues = []
        if row["flag_completeness"]: issues.append("Completeness")
        if row["flag_consistency"]:  issues.append("Consistency")
        if row["flag_validity"]:     issues.append("Validity")
        return "Pass" if not issues else "Issue: " + " | ".join(issues)

    df["quality_status"] = df.apply(_status, axis=1)
    return df


# ══════════════════════════════════════════════════════════════
# MAIN PIPELINE — run all checks in sequence
# ══════════════════════════════════════════════════════════════
def run_all_checks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run all quality checks in sequence.

    Args:
        df: Raw input DataFrame

    Returns:
        Fully flagged DataFrame with all quality columns added

    Example:
        df = pd.read_excel("mydata.xlsx")
        df_flagged = run_all_checks(df)
    """
    df = check_completeness(df)
    df = check_consistency(df)
    df = check_validity(df)
    df = add_overall_flag(df)
    return df


# ══════════════════════════════════════════════════════════════
# EXPORT HELPER
# ══════════════════════════════════════════════════════════════
def export_to_excel(df: pd.DataFrame,
                    filepath: str = None) -> bytes:
    """
    Export flagged DataFrame to Excel with 3 sheets.

    Args:
        df:       Flagged DataFrame (output of run_all_checks)
        filepath: Optional path to save file locally

    Returns:
        Excel file as bytes (for download buttons etc.)
    """
    original_cols = [
        "timevalue", "providerkey", "companynameofficial",
        "fiscalperiodend", "operationstatustype", "ipostatustype",
        "geonameen", "industrycode", "REVENUE", "unit_REVENUE"
    ]
    quality_cols = [
        "flag_any_issue", "quality_status",
        "flag_completeness", "flag_completeness_detail",
        "flag_consistency", "flag_consistency_detail",
        "flag_validity",    "flag_validity_detail",
    ]

    existing = [c for c in original_cols if c in df.columns]
    df_out   = df[existing + quality_cols].copy()

    # Summary table
    total = len(df)
    summary = pd.DataFrame({
        "Dimension":       ["Completeness","Consistency","Validity","Any Issue"],
        "Records_Flagged": [
            int(df["flag_completeness"].sum()),
            int(df["flag_consistency"].sum()),
            int(df["flag_validity"].sum()),
            int(df["flag_any_issue"].sum()),
        ],
        "Total_Records":   [total] * 4,
    })
    summary["Issue_Rate_%"] = (
        summary["Records_Flagged"] / summary["Total_Records"] * 100
    ).round(1)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_out.to_excel(writer, sheet_name="Full Dataset", index=False)
        df_out[df_out["flag_any_issue"]].to_excel(
            writer, sheet_name="Issues Only", index=False)
        summary.to_excel(writer, sheet_name="Quality Summary", index=False)

    excel_bytes = buffer.getvalue()

    if filepath:
        with open(filepath, "wb") as f:
            f.write(excel_bytes)
        print(f"Saved to {filepath}")

    return excel_bytes


# ══════════════════════════════════════════════════════════════
# STANDALONE SCRIPT MODE
# Run directly: python quality_checks.py
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys

    input_file = sys.argv[1] if len(sys.argv) > 1 \
        else "CaseStudy_Quality_sample25_1.xlsx"

    print(f"\n🔍 Running quality checks on: {input_file}")
    df_raw = pd.read_excel(input_file)
    print(f"   Loaded {len(df_raw):,} rows")

    df_flagged = run_all_checks(df_raw)

    output_file = f"flagged_{input_file}"
    export_to_excel(df_flagged, filepath=output_file)

    total   = len(df_flagged)
    flagged = int(df_flagged["flag_any_issue"].sum())
    print(f"\n{'='*50}")
    print(f"  Total records : {total:,}")
    print(f"  Flagged       : {flagged:,} ({flagged/total:.1%})")
    print(f"  Clean         : {total-flagged:,}")
    print(f"  Output saved  : {output_file}")
    print(f"{'='*50}\n")
