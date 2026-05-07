"""
India Medical College Dashboard — Streamlit + CSV
Data: NMC, NIRF 2025, MCC | Updated April 2026
Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="India Medical Colleges",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&family=Space+Grotesk:wght@700;900&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1,h2,h3 { font-family: 'Space Grotesk', sans-serif; }

[data-testid="metric-container"] {
    background: linear-gradient(135deg,#0f1629,#0d1a3a);
    border:1px solid #1e2d4a; border-radius:14px; padding:16px 20px;
}
[data-testid="stMetricValue"]  { color:#00d4ff; font-weight:900; font-size:1.9rem; }
[data-testid="stMetricLabel"]  { color:#e8f4fd; font-weight:600; }
[data-testid="stSidebar"]      { background:#0f1629; border-right:1px solid #1e2d4a; }
.stTabs [data-baseweb="tab"]   { color:#6b8fa8; font-weight:600; }
.stTabs [aria-selected="true"] { color:#00d4ff !important; border-bottom-color:#00d4ff !important; }
</style>
""", unsafe_allow_html=True)

COLORS = {
    "Central Govt": "#00d4ff",
    "State Govt":   "#00ff9d",
    "Private/Deemed":"#ff6b35",
    "ESIC":         "#ffd700",
}

# ── Load CSVs ─────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent

@st.cache_data
def load_colleges():
    df = pd.read_csv(BASE / "medical_colleges_india.csv")
    df["fee_lakh"] = (df["annual_fee_inr"] / 100000).round(2)
    df["age"]      = 2025 - df["established_year"]
    df["college_type_short"] = df["college_type"].map({
        "Central Govt":   "Central Govt",
        "State Govt":     "State Govt",
        "Private/Deemed": "Private/Deemed",
    }).fillna(df["college_type"])
    return df

@st.cache_data
def load_growth():
    return pd.read_csv(BASE / "seat_growth.csv")

@st.cache_data
def load_states():
    df = pd.read_csv(BASE / "state_summary.csv")
    df["total_colleges"]  = df["govt_colleges"] + df["private_colleges"]
    df["govt_pct"]        = (df["govt_colleges"] / df["total_colleges"] * 100).round(1)
    df["private_pct"]     = (df["private_colleges"] / df["total_colleges"] * 100).round(1)
    return df

colleges_df = load_colleges()
growth_df   = load_growth()
states_df   = load_states()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏥 Medical College\nDashboard India")
    st.caption("Open Data · NMC · NIRF 2025 · MCC")
    st.markdown("---")

    st.markdown("### 🔍 Filters")
    regions   = st.multiselect("Region", sorted(colleges_df["region"].unique()),
                                default=sorted(colleges_df["region"].unique()))
    col_types = st.multiselect("College Type", sorted(colleges_df["college_type"].unique()),
                                default=sorted(colleges_df["college_type"].unique()))
    min_seats = st.slider("Min MBBS Seats", 0, 300, 0, 25)
    nirf_only = st.checkbox("NIRF Ranked only", value=False)

    st.markdown("---")
    st.markdown("### 📂 CSV Files Used")
    st.code("medical_colleges_india.csv\nseat_growth.csv\nstate_summary.csv", language="")
    st.caption(f"**{len(colleges_df)}** colleges loaded")
    st.markdown("---")
    st.caption("Sources: NMC • MCC • NIRF 2025 • data.gov.in")

# ── Apply filters ─────────────────────────────────────────────────────────────
mask = (
    colleges_df["region"].isin(regions) &
    colleges_df["college_type"].isin(col_types) &
    (colleges_df["mbbs_seats"] >= min_seats)
)
if nirf_only:
    mask &= colleges_df["nirf_rank_2025"] > 0
filtered = colleges_df[mask].copy()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🏥 India Medical College Open Data Dashboard")
st.caption(f"Showing **{len(filtered)}** of **{len(colleges_df)}** colleges based on filters · Data: NMC 2024-25")
st.divider()

# ── KPI row ───────────────────────────────────────────────────────────────────
k1,k2,k3,k4,k5,k6 = st.columns(6)
k1.metric("Total Colleges",    f"{len(filtered):,}")
k2.metric("Total MBBS Seats",  f"{filtered['mbbs_seats'].sum():,}")
k3.metric("Hospital Beds",     f"{filtered['hospital_beds'].sum():,}")
k4.metric("PG Seats",          f"{filtered['pg_seats'].sum():,}")
k5.metric("Avg Annual Fee",    f"₹{filtered['annual_fee_inr'].mean():,.0f}")
k6.metric("Oldest College",    str(int(filtered['established_year'].min())))
st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
t1, t2, t3, t4, t5 = st.tabs([
    "📊 Overview", "🗺️ State Analysis", "🏫 College Explorer",
    "💰 Fees & Cutoffs", "📈 Trends"
])

# ════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ════════════════════════════════════════════════════════
with t1:
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Colleges by Type")
        type_counts = filtered["college_type"].value_counts().reset_index()
        type_counts.columns = ["Type","Count"]
        fig = px.pie(type_counts, values="Count", names="Type", hole=0.5,
                     color="Type",
                     color_discrete_map=COLORS)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#e8f4fd",
                          margin=dict(t=10,b=10))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("MBBS Seats by College Type")
        seats_type = filtered.groupby("college_type")["mbbs_seats"].sum().reset_index()
        seats_type.columns = ["Type","Seats"]
        fig2 = px.bar(seats_type.sort_values("Seats"), x="Seats", y="Type",
                      orientation="h", color="Type",
                      color_discrete_map=COLORS, text="Seats")
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="#e8f4fd", showlegend=False,
                           xaxis=dict(gridcolor="#1e2d4a",color="#6b8fa8"),
                           yaxis=dict(color="#6b8fa8"), margin=dict(t=10,b=10))
        fig2.update_traces(textposition="outside")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Top 15 States — Govt vs Private Colleges")
    top_states = states_df.nlargest(15,"total_colleges")
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(name="Govt", x=top_states["state"],
                          y=top_states["govt_colleges"],
                          marker_color="#00d4ff", text=top_states["govt_colleges"],
                          textposition="auto"))
    fig3.add_trace(go.Bar(name="Private/Deemed", x=top_states["state"],
                          y=top_states["private_colleges"],
                          marker_color="#ff6b35", text=top_states["private_colleges"],
                          textposition="auto"))
    fig3.update_layout(barmode="group",
                       paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       font_color="#e8f4fd", legend=dict(font_color="#6b8fa8"),
                       xaxis=dict(gridcolor="#1e2d4a",color="#6b8fa8",tickangle=-30),
                       yaxis=dict(gridcolor="#1e2d4a",color="#6b8fa8"),
                       margin=dict(t=10,b=80))
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Colleges Established Over Time")
    era = filtered.copy()
    era["decade"] = (era["established_year"] // 10 * 10).astype(str) + "s"
    era_grp = era.groupby(["decade","college_type"]).size().reset_index(name="Count")
    fig4 = px.bar(era_grp, x="decade", y="Count", color="college_type",
                  color_discrete_map=COLORS, barmode="stack",
                  labels={"decade":"Decade","Count":"Colleges Founded","college_type":"Type"})
    fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       font_color="#e8f4fd", legend=dict(font_color="#6b8fa8"),
                       xaxis=dict(gridcolor="#1e2d4a",color="#6b8fa8"),
                       yaxis=dict(gridcolor="#1e2d4a",color="#6b8fa8"),
                       margin=dict(t=10,b=10))
    st.plotly_chart(fig4, use_container_width=True)

# ════════════════════════════════════════════════════════
# TAB 2 — STATE ANALYSIS
# ════════════════════════════════════════════════════════
with t2:
    st.subheader("MBBS Seats by State (Treemap)")
    state_seats = filtered.groupby(["state","region","college_type"])["mbbs_seats"].sum().reset_index()
    fig_tree = px.treemap(state_seats, path=["region","state","college_type"],
                          values="mbbs_seats",
                          color="college_type", color_discrete_map=COLORS)
    fig_tree.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#e8f4fd",
                            margin=dict(t=10,b=10), height=420)
    st.plotly_chart(fig_tree, use_container_width=True)

    cl, cr = st.columns(2)

    with cl:
        st.subheader("Seats per State (Top 20)")
        st_seats = filtered.groupby("state")["mbbs_seats"].sum().reset_index()
        st_seats = st_seats.nlargest(20,"mbbs_seats")
        fig_h = px.bar(st_seats, x="mbbs_seats", y="state", orientation="h",
                       color="mbbs_seats", color_continuous_scale=["#0a2a4a","#00d4ff"],
                       text="mbbs_seats", labels={"mbbs_seats":"MBBS Seats","state":"State"})
        fig_h.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            font_color="#e8f4fd", showlegend=False,
                            coloraxis_showscale=False,
                            xaxis=dict(gridcolor="#1e2d4a",color="#6b8fa8"),
                            yaxis=dict(color="#6b8fa8"), margin=dict(t=10,b=10), height=520)
        fig_h.update_traces(textposition="outside")
        st.plotly_chart(fig_h, use_container_width=True)

    with cr:
        st.subheader("Govt vs Private Bubble Chart")
        fig_sc = px.scatter(states_df, x="govt_colleges", y="private_colleges",
                            size="total_seats", color="region",
                            hover_name="state", size_max=55,
                            labels={"govt_colleges":"Govt Colleges",
                                    "private_colleges":"Private Colleges"})
        fig_sc.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                             font_color="#e8f4fd", legend=dict(font_color="#6b8fa8"),
                             xaxis=dict(gridcolor="#1e2d4a",color="#6b8fa8"),
                             yaxis=dict(gridcolor="#1e2d4a",color="#6b8fa8"),
                             margin=dict(t=10,b=10), height=520)
        st.plotly_chart(fig_sc, use_container_width=True)

    st.subheader("📋 State Summary Table (from state_summary.csv)")
    st.dataframe(
        states_df[["state","region","govt_colleges","private_colleges",
                   "total_colleges","total_seats","govt_pct","new_colleges_2026"]]
        .rename(columns={"govt_pct":"Govt %","new_colleges_2026":"New 2026"})
        .sort_values("total_seats", ascending=False)
        .reset_index(drop=True),
        use_container_width=True, height=400
    )

# ════════════════════════════════════════════════════════
# TAB 3 — COLLEGE EXPLORER
# ════════════════════════════════════════════════════════
with t3:
    st.subheader("🔎 Search & Explore Colleges (medical_colleges_india.csv)")

    search = st.text_input("Search college name, state, or district", placeholder="e.g. AIIMS, Mumbai, Karnataka…")
    col_a, col_b = st.columns(2)
    with col_a:
        sort_col = st.selectbox("Sort by", ["nirf_rank_2025","mbbs_seats","established_year",
                                             "annual_fee_inr","hospital_beds","neet_cutoff_air_general"])
    with col_b:
        sort_asc = st.radio("Order", ["Ascending","Descending"], horizontal=True)

    explorer = filtered.copy()
    if search:
        q = search.lower()
        explorer = explorer[
            explorer["college_name"].str.lower().str.contains(q) |
            explorer["state"].str.lower().str.contains(q) |
            explorer["district"].str.lower().str.contains(q)
        ]

    explorer = explorer.sort_values(sort_col, ascending=(sort_asc=="Ascending"))

    st.caption(f"**{len(explorer)}** results")
    display_cols = ["college_name","state","region","college_type","management",
                    "mbbs_seats","nirf_rank_2025","established_year",
                    "annual_fee_inr","neet_cutoff_air_general","hospital_beds","pg_seats"]
    st.dataframe(explorer[display_cols].reset_index(drop=True),
                 use_container_width=True, height=450)

    # Scatter — seats vs beds
    st.subheader("MBBS Seats vs Hospital Beds")
    fig_sv = px.scatter(explorer, x="mbbs_seats", y="hospital_beds",
                        color="college_type", size="pg_seats",
                        hover_name="college_name",
                        color_discrete_map=COLORS, size_max=40,
                        labels={"mbbs_seats":"MBBS Seats","hospital_beds":"Hospital Beds"})
    fig_sv.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                         font_color="#e8f4fd", legend=dict(font_color="#6b8fa8"),
                         xaxis=dict(gridcolor="#1e2d4a",color="#6b8fa8"),
                         yaxis=dict(gridcolor="#1e2d4a",color="#6b8fa8"),
                         margin=dict(t=10,b=10))
    st.plotly_chart(fig_sv, use_container_width=True)

# ════════════════════════════════════════════════════════
# TAB 4 — FEES & CUTOFFS
# ════════════════════════════════════════════════════════
with t4:
    cl, cr = st.columns(2)

    with cl:
        st.subheader("Fee Distribution by College Type")
        fig_box = px.box(filtered[filtered["annual_fee_inr"]>0],
                         x="college_type", y="annual_fee_inr",
                         color="college_type", color_discrete_map=COLORS,
                         log_y=True,
                         labels={"annual_fee_inr":"Annual Fee (₹, log)","college_type":"Type"})
        fig_box.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font_color="#e8f4fd", showlegend=False,
                              xaxis=dict(color="#6b8fa8"),
                              yaxis=dict(gridcolor="#1e2d4a",color="#6b8fa8"),
                              margin=dict(t=10,b=10))
        st.plotly_chart(fig_box, use_container_width=True)

    with cr:
        st.subheader("NEET Cutoff AIR by College Type")
        neet = filtered[filtered["neet_cutoff_air_general"]>0]
        fig_violin = px.violin(neet, x="college_type", y="neet_cutoff_air_general",
                               color="college_type", color_discrete_map=COLORS,
                               box=True,
                               labels={"neet_cutoff_air_general":"NEET AIR Cutoff","college_type":"Type"})
        fig_violin.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                 font_color="#e8f4fd", showlegend=False,
                                 xaxis=dict(color="#6b8fa8"),
                                 yaxis=dict(gridcolor="#1e2d4a",color="#6b8fa8"),
                                 margin=dict(t=10,b=10))
        st.plotly_chart(fig_violin, use_container_width=True)

    st.subheader("Fee vs NEET Cutoff — Scatter")
    scatter_data = filtered[(filtered["annual_fee_inr"]>0) & (filtered["neet_cutoff_air_general"]>0)]
    fig_fv = px.scatter(scatter_data,
                        x="neet_cutoff_air_general", y="annual_fee_inr",
                        color="college_type", size="mbbs_seats",
                        hover_name="college_name", log_y=True,
                        color_discrete_map=COLORS, size_max=35,
                        labels={"neet_cutoff_air_general":"NEET AIR Cutoff (General)",
                                "annual_fee_inr":"Annual Fee ₹ (log scale)"})
    fig_fv.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                         font_color="#e8f4fd", legend=dict(font_color="#6b8fa8"),
                         xaxis=dict(gridcolor="#1e2d4a",color="#6b8fa8"),
                         yaxis=dict(gridcolor="#1e2d4a",color="#6b8fa8"),
                         margin=dict(t=10,b=10), height=420)
    st.plotly_chart(fig_fv, use_container_width=True)

    st.subheader("Fee Summary by College Type")
    fee_summary = (filtered[filtered["annual_fee_inr"]>0]
                   .groupby("college_type")["annual_fee_inr"]
                   .agg(["min","max","mean","median"])
                   .round(0).astype(int)
                   .reset_index())
    fee_summary.columns = ["College Type","Min Fee (₹)","Max Fee (₹)","Avg Fee (₹)","Median Fee (₹)"]
    st.dataframe(fee_summary, use_container_width=True, hide_index=True)

# ════════════════════════════════════════════════════════
# TAB 5 — TRENDS
# ════════════════════════════════════════════════════════
with t5:
    st.subheader("📈 MBBS Seats & Colleges Growth (seat_growth.csv)")
    fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
    fig_dual.add_trace(
        go.Scatter(x=growth_df["year"], y=growth_df["mbbs_seats"],
                   name="MBBS Seats", mode="lines+markers",
                   line=dict(color="#00d4ff", width=3),
                   marker=dict(size=8, color="#00d4ff")),
        secondary_y=False)
    fig_dual.add_trace(
        go.Bar(x=growth_df["year"], y=growth_df["colleges"],
               name="Total Colleges",
               marker_color="#ff6b3555",
               marker_line_color="#ff6b35", marker_line_width=1.5),
        secondary_y=True)
    fig_dual.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e8f4fd", legend=dict(font_color="#6b8fa8"),
        xaxis=dict(gridcolor="#1e2d4a", color="#6b8fa8"),
        yaxis=dict(gridcolor="#1e2d4a", color="#6b8fa8", title="MBBS Seats"),
        yaxis2=dict(color="#ff6b35", title="Colleges"),
        margin=dict(t=10,b=10), height=380)
    st.plotly_chart(fig_dual, use_container_width=True)

    cl, cr = st.columns(2)
    with cl:
        st.subheader("New Colleges Added per Year")
        fig_nc = px.bar(growth_df, x="year", y="new_colleges_added",
                        text="new_colleges_added",
                        color="new_colleges_added",
                        color_continuous_scale=["#0a2a4a","#ffd700"],
                        labels={"new_colleges_added":"New Colleges","year":"Year"})
        fig_nc.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                             font_color="#e8f4fd", coloraxis_showscale=False,
                             xaxis=dict(gridcolor="#1e2d4a",color="#6b8fa8"),
                             yaxis=dict(gridcolor="#1e2d4a",color="#6b8fa8"),
                             margin=dict(t=10,b=10))
        st.plotly_chart(fig_nc, use_container_width=True)

    with cr:
        st.subheader("New PG Seats Added per Year")
        fig_pg = px.area(growth_df, x="year", y="new_pg_seats_added",
                         color_discrete_sequence=["#00ff9d"],
                         labels={"new_pg_seats_added":"PG Seats Added","year":"Year"})
        fig_pg.update_traces(fillcolor="rgba(0,255,157,0.15)", line_color="#00ff9d")
        fig_pg.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                             font_color="#e8f4fd",
                             xaxis=dict(gridcolor="#1e2d4a",color="#6b8fa8"),
                             yaxis=dict(gridcolor="#1e2d4a",color="#6b8fa8"),
                             margin=dict(t=10,b=10))
        st.plotly_chart(fig_pg, use_container_width=True)

    st.subheader("📋 Raw Growth Data (seat_growth.csv)")
    st.dataframe(growth_df, use_container_width=True, hide_index=True)

    st.subheader("New Colleges Pipeline 2026 (state_summary.csv)")
    pipeline = states_df[states_df["new_colleges_2026"]>0].sort_values("new_colleges_2026", ascending=False)
    fig_pipe = px.bar(pipeline, x="new_colleges_2026", y="state", orientation="h",
                      color="new_colleges_2026",
                      color_continuous_scale=["#00d4ff","#ffd700","#ff6b35"],
                      text="new_colleges_2026",
                      labels={"new_colleges_2026":"New Colleges","state":"State"})
    fig_pipe.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="#e8f4fd", coloraxis_showscale=False,
                           xaxis=dict(gridcolor="#1e2d4a",color="#6b8fa8"),
                           yaxis=dict(color="#6b8fa8"),
                           margin=dict(t=10,b=10), height=500)
    fig_pipe.update_traces(textposition="outside")
    st.plotly_chart(fig_pipe, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("Data: NMC · MCC · NIRF 2025 · data.gov.in · For educational & research purposes only · April 2026")
