"""
=============================================================
Statista Case Study — Company Financial Data Quality Checks
=============================================================
Author  : Anjali Parihar
Purpose : Automated data quality checks across three dimensions:
          1. Completeness  — missing values in critical fields
          2. Consistency   — mismatched revenue/unit pairs,
                              fiscal period format issues
          3. Validity      — negative revenue, extreme YoY changes,
                              statistical outliers
Output  : Flagged Excel file ready for Power BI reporting

"""

"""
 Data Quality Audit Engine
=============================================================
Run with: streamlit run app.py
=============================================================
"""

import warnings
import pandas as pd
import streamlit as st
from quality_checks import run_all_checks, export_to_excel

warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="Data Quality Audit Engine",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
.main .block-container { padding-top: 2rem; max-width: 1200px; }
.hero-banner {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 16px; padding: 40px 50px; margin-bottom: 32px; position: relative; overflow: hidden;
}
.hero-title { font-size: 2.2rem; font-weight: 700; color: #ffffff; margin: 0 0 8px 0; }
.hero-subtitle { font-size: 1rem; color: rgba(255,255,255,0.65); margin: 0 0 20px 0; }
.hero-badge {
    display: inline-block; background: rgba(99,179,237,0.2); border: 1px solid rgba(99,179,237,0.4);
    color: #63b3ed; padding: 4px 14px; border-radius: 20px; font-size: 0.78rem; font-weight: 500; margin-right: 8px;
}
.dim-card {
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06); height: 100%;
}
.dim-icon { font-size: 2rem; margin-bottom: 12px; display: block; }
.dim-title { font-size: 1rem; font-weight: 600; color: #1a202c; margin: 0 0 6px 0; }
.dim-desc { font-size: 0.85rem; color: #718096; line-height: 1.5; margin: 0; }
.metric-card {
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;
    padding: 20px 24px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.metric-number { font-size: 2.4rem; font-weight: 700; line-height: 1; margin: 8px 0 4px 0; }
.metric-label { font-size: 0.8rem; font-weight: 500; color: #718096; text-transform: uppercase; letter-spacing: 0.05em; margin: 0; }
.metric-sub { font-size: 0.78rem; color: #a0aec0; margin: 4px 0 0 0; }
.metric-blue { color: #3182ce; } .metric-green { color: #38a169; }
.metric-red { color: #e53e3e; } .metric-purple { color: #805ad5; }
.result-card { border-radius: 12px; padding: 20px 24px; margin-bottom: 12px; }
.result-card.completeness { background: #fffbeb; border: 1px solid #f6e05e; border-left: 4px solid #d69e2e; }
.result-card.consistency { background: #ebf8ff; border: 1px solid #90cdf4; border-left: 4px solid #3182ce; }
.result-card.validity { background: #fff5f5; border: 1px solid #feb2b2; border-left: 4px solid #e53e3e; }
.result-count { font-size: 1.8rem; font-weight: 700; margin: 0; line-height: 1; }
.result-pct { font-size: 0.82rem; font-weight: 400; opacity: 0.75; }
.quality-bar-wrap { background: #edf2f7; border-radius: 8px; height: 10px; overflow: hidden; margin: 8px 0; }
.quality-bar-fill { height: 100%; border-radius: 8px; }
.section-header {
    font-size: 1.1rem; font-weight: 600; color: #2d3748;
    padding-bottom: 8px; border-bottom: 2px solid #e2e8f0; margin-bottom: 20px;
}
.step-wrap { display: flex; align-items: center; margin-bottom: 8px; }
.step-num {
    background: #3182ce; color: white; width: 22px; height: 22px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.72rem; font-weight: 700; margin-right: 10px; flex-shrink: 0;
}
.step-text { font-size: 0.85rem; color: #4a5568; }
.custom-footer {
    text-align: center; color: #a0aec0; font-size: 0.78rem;
    padding: 20px 0 0 0; border-top: 1px solid #e2e8f0; margin-top: 40px;
}
[data-testid="stFileUploader"] { border: 2px dashed #cbd5e0; border-radius: 12px; background: #f7fafc; }
.stButton > button { border-radius: 8px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Audit Engine")
    st.markdown("---")
    st.markdown("**How to use**")
    st.markdown("""
<div class="step-wrap"><div class="step-num">1</div><div class="step-text">Upload Excel file</div></div>
<div class="step-wrap"><div class="step-num">2</div><div class="step-text">Click Run Quality Checks</div></div>
<div class="step-wrap"><div class="step-num">3</div><div class="step-text">Review results by dimension</div></div>
<div class="step-wrap"><div class="step-num">4</div><div class="step-text">Download flagged Excel</div></div>
""", unsafe_allow_html=True)
    st.markdown("---")
    uploaded_file = st.file_uploader("Upload Excel File (.xlsx)", type=["xlsx","xls"])
    st.markdown("---")
    st.markdown("**⚙️ Thresholds**")
    outlier_std = st.slider("Outlier z-score threshold", 2, 5, 3)
    yoy_threshold = st.slider("YoY change threshold (%)", 50, 500, 200, 50) / 100
    show_raw = st.checkbox("Show raw data preview", value=True)
    st.markdown("---")
    st.markdown("""<div style='font-size:0.78rem;color:#718096;line-height:1.8;'>
<strong>Author:</strong> Anjali Parihar<br>
<strong>Case Study:</strong> Statista 2025<br>
<strong>Version:</strong> 2.0.0</div>""", unsafe_allow_html=True)

# ── HERO ─────────────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
    <p class="hero-title">🔍 Data Quality Audit Engine</p>
    <p class="hero-subtitle">Automated financial data validation across three quality dimensions — built for enterprise-scale datasets extracted from multiple sources.</p>
    <span class="hero-badge">✅ Completeness</span>
    <span class="hero-badge">🔄 Consistency</span>
    <span class="hero-badge">⚠️ Validity</span>
    <span class="hero-badge">📊 Power BI Ready</span>
</div>
""", unsafe_allow_html=True)

# ── NO FILE ───────────────────────────────────────────────────
if uploaded_file is None:
    st.markdown('<p class="section-header">What This Tool Checks</p>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    cards = [
        ("✅","Completeness","Detects missing values in critical fields — Revenue, Currency Unit, Company Name, Industry Code, and Fiscal Period."),
        ("🔄","Consistency","Identifies internal contradictions — revenue without a currency unit, and inconsistent fiscal period formats per company."),
        ("⚠️","Validity","Flags implausible values: negative revenue, statistical outliers beyond 3 standard deviations, and extreme year-on-year changes."),
    ]
    for col, (icon, title, desc) in zip([c1,c2,c3], cards):
        with col:
            st.markdown(f'<div class="dim-card"><span class="dim-icon">{icon}</span><p class="dim-title">{title}</p><p class="dim-desc">{desc}</p></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="section-header">What You Get</p>', unsafe_allow_html=True)
    g1,g2,g3,g4 = st.columns(4)
    gets = [("📋","Flagged Dataset","Every record labelled with exact issues"),("📊","Quality Summary","Dimension breakdown for Power BI"),("💾","Excel Export","3-sheet output: Full, Issues, Summary"),("🔁","Any Dataset","Works with any financial Excel file")]
    for col,(icon,title,desc) in zip([g1,g2,g3,g4],gets):
        with col:
            st.markdown(f'<div class="dim-card" style="text-align:center;"><span class="dim-icon">{icon}</span><p class="dim-title">{title}</p><p class="dim-desc">{desc}</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="custom-footer">Data Quality Audit Engine · Statista Case Study · Anjali Parihar · 2025</div>', unsafe_allow_html=True)

# ── FILE LOADED ───────────────────────────────────────────────
else:
    df_raw = pd.read_excel(uploaded_file)
    st.markdown(f"""<div style="background:#f0fff4;border:1px solid #9ae6b4;border-left:4px solid #38a169;border-radius:8px;padding:14px 20px;margin-bottom:20px;">
<strong style="color:#276749;">✅ File loaded successfully</strong>
<span style="color:#4a5568;font-size:0.9rem;margin-left:12px;">{uploaded_file.name} &nbsp;·&nbsp; {len(df_raw):,} rows &nbsp;·&nbsp; {len(df_raw.columns)} columns</span>
</div>""", unsafe_allow_html=True)

    if show_raw:
        with st.expander("👀 Raw Data Preview — first 5 rows"):
            st.dataframe(df_raw.head(5), use_container_width=True)

    col_btn, col_info = st.columns([1,3])
    with col_btn:
        run_clicked = st.button("🚀 Run Quality Checks", type="primary", use_container_width=True)
    with col_info:
        st.markdown('<div style="padding:10px 0;color:#718096;font-size:0.88rem;">Checks run across all three quality dimensions simultaneously. Results appear below instantly.</div>', unsafe_allow_html=True)

    if run_clicked:
        with st.spinner("🔍 Running quality checks..."):
            df_flagged = run_all_checks(df_raw)
            excel_bytes = export_to_excel(df_flagged)
            st.session_state["df"]    = df_flagged
            st.session_state["excel"] = excel_bytes
            st.session_state["fname"] = f"flagged_{uploaded_file.name}"
        st.success("✅ Quality checks complete!")

    if "df" in st.session_state:
        df = st.session_state["df"]
        total   = len(df)
        flagged = int(df["flag_any_issue"].sum())
        clean   = total - flagged
        rate    = flagged / total * 100
        score   = 100 - rate

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<p class="section-header">📊 Executive Summary</p>', unsafe_allow_html=True)

        k1,k2,k3,k4 = st.columns(4)
        with k1:
            st.markdown(f'<div class="metric-card"><p class="metric-label">Total Records</p><p class="metric-number metric-blue">{total:,}</p><p class="metric-sub">Dataset size</p></div>', unsafe_allow_html=True)
        with k2:
            st.markdown(f'<div class="metric-card"><p class="metric-label">Clean Records</p><p class="metric-number metric-green">{clean:,}</p><p class="metric-sub">{clean/total:.1%} pass rate</p></div>', unsafe_allow_html=True)
        with k3:
            st.markdown(f'<div class="metric-card"><p class="metric-label">Flagged Records</p><p class="metric-number metric-red">{flagged:,}</p><p class="metric-sub">{rate:.1f}% issue rate</p></div>', unsafe_allow_html=True)
        with k4:
            c = "metric-green" if score>=80 else "metric-red"
            st.markdown(f'<div class="metric-card"><p class="metric-label">Quality Score</p><p class="metric-number {c}">{score:.1f}%</p><p class="metric-sub">Target: ≥ 90%</p></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        bar_colour = "#38a169" if score>=80 else "#e53e3e"
        st.markdown(f"""<div style="margin-bottom:28px;">
<div style="display:flex;justify-content:space-between;font-size:0.82rem;color:#718096;margin-bottom:4px;"><span>Overall Data Quality Score</span><span><strong>{score:.1f}%</strong></span></div>
<div class="quality-bar-wrap"><div class="quality-bar-fill" style="width:{score}%;background:{bar_colour};"></div></div>
<div style="display:flex;justify-content:space-between;font-size:0.75rem;color:#a0aec0;margin-top:2px;"><span>0%</span><span>Target: 90%</span><span>100%</span></div>
</div>""", unsafe_allow_html=True)

        st.markdown('<p class="section-header">📌 Dimension Breakdown</p>', unsafe_allow_html=True)
        comp = int(df["flag_completeness"].sum())
        cons = int(df["flag_consistency"].sum())
        vali = int(df["flag_validity"].sum())

        d1,d2,d3 = st.columns(3)
        with d1:
            st.markdown(f'<div class="result-card completeness"><p style="font-weight:600;color:#744210;margin:0 0 4px 0;">✅ Completeness</p><p class="result-count" style="color:#d69e2e;">{comp:,} <span class="result-pct">records ({comp/total:.1%})</span></p><div class="quality-bar-wrap"><div class="quality-bar-fill" style="width:{comp/total*100:.1f}%;background:#d69e2e;"></div></div><p style="font-size:0.78rem;color:#744210;margin:6px 0 0 0;">Missing required fields</p></div>', unsafe_allow_html=True)
        with d2:
            st.markdown(f'<div class="result-card consistency"><p style="font-weight:600;color:#2b6cb0;margin:0 0 4px 0;">🔄 Consistency</p><p class="result-count" style="color:#3182ce;">{cons:,} <span class="result-pct">records ({cons/total:.1%})</span></p><div class="quality-bar-wrap"><div class="quality-bar-fill" style="width:{cons/total*100:.1f}%;background:#3182ce;"></div></div><p style="font-size:0.78rem;color:#2b6cb0;margin:6px 0 0 0;">Revenue or unit mismatches</p></div>', unsafe_allow_html=True)
        with d3:
            st.markdown(f'<div class="result-card validity"><p style="font-weight:600;color:#9b2c2c;margin:0 0 4px 0;">⚠️ Validity</p><p class="result-count" style="color:#e53e3e;">{vali:,} <span class="result-pct">records ({vali/total:.1%})</span></p><div class="quality-bar-wrap"><div class="quality-bar-fill" style="width:{vali/total*100:.1f}%;background:#e53e3e;"></div></div><p style="font-size:0.78rem;color:#9b2c2c;margin:6px 0 0 0;">Implausible values detected</p></div>', unsafe_allow_html=True)

        worst = "Completeness" if comp>=cons and comp>=vali else "Consistency" if cons>=vali else "Validity"
        st.markdown(f"""<div style="background:#faf5ff;border:1px solid #d6bcfa;border-left:4px solid #805ad5;border-radius:8px;padding:16px 20px;margin:20px 0;">
<strong style="color:#553c9a;">💡 Key Insight</strong>
<p style="color:#4a5568;font-size:0.9rem;margin:6px 0 0 0;"><strong>{worst}</strong> is the primary quality concern, affecting <strong>{max(comp,cons,vali):,} records ({max(comp,cons,vali)/total:.1%})</strong>. {flagged:,} of {total:,} total records require attention before this data is used for analysis.</p>
</div>""", unsafe_allow_html=True)

        st.markdown('<p class="section-header">🔍 Explore Results</p>', unsafe_allow_html=True)
        tab1,tab2,tab3,tab4 = st.tabs([f"📋 All ({total:,})",f"⚠️ Issues ({flagged:,})",f"✅ Completeness ({comp:,})",f"🔄 Consistency & Validity ({cons+vali:,})"])
        display_cols = ["companynameofficial","timevalue","REVENUE","unit_REVENUE","quality_status","flag_completeness_detail","flag_consistency_detail","flag_validity_detail"]
        existing_cols = [c for c in display_cols if c in df.columns]

        with tab1:
            st.caption(f"All {total:,} records with quality flags")
            st.dataframe(df[existing_cols], use_container_width=True, height=350)
        with tab2:
            issues_df = df[df["flag_any_issue"]==True][existing_cols]
            st.caption(f"{len(issues_df):,} records flagged for review")
            st.dataframe(issues_df, use_container_width=True, height=350)
        with tab3:
            comp_df = df[df["flag_completeness"]==True][existing_cols]
            st.caption(f"{len(comp_df):,} records missing required fields")
            st.dataframe(comp_df, use_container_width=True, height=350)
        with tab4:
            cv_df = df[(df["flag_consistency"]==True)|(df["flag_validity"]==True)][existing_cols]
            st.caption(f"{len(cv_df):,} consistency or validity issues")
            st.dataframe(cv_df, use_container_width=True, height=350)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<p class="section-header">💾 Download Results</p>', unsafe_allow_html=True)
        dl1,dl2 = st.columns([1,2])
        with dl1:
            st.download_button(label="📥 Download Flagged Excel (.xlsx)", data=st.session_state["excel"], file_name=st.session_state["fname"], mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary", use_container_width=True)
        with dl2:
            st.markdown('<div style="background:#ebf8ff;border:1px solid #90cdf4;border-radius:8px;padding:14px 18px;"><strong style="color:#2b6cb0;font-size:0.88rem;">📊 Power BI Integration</strong><p style="color:#4a5568;font-size:0.82rem;margin:4px 0 0 0;">Downloaded file contains 3 sheets: <strong>Full Dataset</strong> · <strong>Issues Only</strong> · <strong>Quality Summary</strong> — connect directly to Power BI.</p></div>', unsafe_allow_html=True)

        st.markdown('<div class="custom-footer">Data Quality Audit Engine · Statista Case Study · Anjali Parihar · 2025 · Built with Python · Pandas · Streamlit</div>', unsafe_allow_html=True)
