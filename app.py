from pathlib import Path
import math

import altair as alt
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="可转债数据库",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE = Path(__file__).parent
BLUE = "#1F5AA6"
NAVY = "#102B56"
SKY = "#7EA3D4"
ORANGE = "#E99A2F"
RED = "#C94B55"
PAPER = "#F4F7FB"

# The orange curve is the independent lower-right value boundary.  It is not
# derived from, or enclosed by, the three black valuation structure lines.
VALUE_CURVE = [
    (-3.4, 0.0), (-2.5, 1.0), (-1.5, 2.0), (-0.5, 4.0),
    (0.3, 8.0), (0.9, 15.0), (1.5, 25.0), (2.1, 38.0),
]


def value_curve_limit(values: pd.Series) -> pd.Series:
    """Return the piecewise-linear premium ceiling of the orange curve."""
    limits = pd.Series(float("nan"), index=values.index, dtype="float64")
    for (x0, y0), (x1, y1) in zip(VALUE_CURVE[:-1], VALUE_CURVE[1:]):
        segment = values.between(x0, x1)
        limits.loc[segment] = y0 + (values.loc[segment] - x0) * (y1 - y0) / (x1 - x0)
    return limits

st.markdown(
    """
    <style>
    :root { --navy:#102B56; --blue:#1F5AA6; --sky:#7EA3D4; --orange:#E99A2F; --paper:#F4F7FB; --ink:#10233F; }
    @font-face { font-family:"HTSC Type"; src:local("Arial"); unicode-range:U+0000-024F, U+2000-206F; }
    @font-face { font-family:"HTSC Type"; src:local("SimHei"), local("Microsoft YaHei"), local("黑体"); unicode-range:U+3000-303F, U+3400-4DBF, U+4E00-9FFF, U+F900-FAFF, U+FF00-FFEF; }
    html, body, [class*="st-"], [data-testid="stAppViewContainer"],
    [data-testid="stSidebar"], [data-testid="stDataFrame"] * {
        font-family:"HTSC Type", Arial, SimHei, "Microsoft YaHei", sans-serif !important;
    }
    [data-testid="stIconMaterial"], .material-symbols-rounded, [class*="material-symbols"] {
        font-family:"Material Symbols Rounded" !important;
        font-weight:normal !important; font-style:normal !important;
    }
    [data-testid="stAppViewContainer"] {
        background:
          linear-gradient(rgba(31,90,166,.035) 1px, transparent 1px),
          linear-gradient(90deg, rgba(31,90,166,.035) 1px, transparent 1px),
          radial-gradient(circle at 86% 8%, rgba(126,163,212,.18), transparent 30%), #F4F7FB;
        background-size: 28px 28px, 28px 28px, auto;
    }
    [data-testid="stHeader"] { background:rgba(244,247,251,.78); backdrop-filter:blur(10px); }
    [data-testid="stSidebar"] { background:linear-gradient(165deg,#102B56 0%,#173B73 100%); border-right:1px solid rgba(255,255,255,.12); }
    [data-testid="stSidebar"] * { color:#F8FBFF; }
    /* Sidebar controls remain white, but entered values must read as black. */
    [data-testid="stSidebar"] input {
        background:#FFFFFF !important; border-color:#FFFFFF !important;
        color:#10233F !important; caret-color:#10233F !important;
    }
    [data-testid="stSidebar"] input::placeholder { color:#7A8BA4 !important; opacity:1; }
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background:#FFFFFF !important; border-color:#FFFFFF !important; color:#10233F !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] * { color:#10233F !important; }
    [data-testid="stSidebar"] hr { border-color:rgba(255,255,255,.15); }
    [data-testid="stSidebar"] .stButton button { width:100%; background:transparent; border:1px solid rgba(255,255,255,.25); color:white; }
    [data-testid="stSidebar"] .stButton button:hover { border-color:#E99A2F; color:#FFD18B; }
    .block-container { max-width:1540px; padding-top:1.1rem; padding-bottom:4rem; }
    .brand-lockup { padding:8px 0 20px; border-bottom:1px solid rgba(255,255,255,.17); margin-bottom:18px; }
    .brand-lockup b { font-size:25px; letter-spacing:.08em; }
    .brand-lockup span { display:block; margin-top:6px; font-family:Arial,sans-serif; font-size:10px; letter-spacing:.22em; opacity:.6; }
    .top-ticker { display:flex; align-items:center; gap:25px; padding:12px 18px; background:#102B56; color:white; border-left:4px solid #E99A2F; box-shadow:0 12px 32px rgba(16,43,86,.16); overflow:auto; white-space:nowrap; }
    .top-ticker span { color:rgba(255,255,255,.68); font-size:13px; }
    .top-ticker b { color:white; font:700 14px Arial,sans-serif; margin-left:7px; }
    .top-ticker i { width:1px; height:16px; background:rgba(255,255,255,.18); }
    .top-ticker em { color:#FFD18B; font:normal 11px Arial,sans-serif; margin-left:4px; }
    .hero { position:relative; margin:22px 0 18px; padding:42px 46px 36px; background:linear-gradient(120deg,#fff 0%,#EEF3FA 78%); border:1px solid #D8E2F0; box-shadow:0 18px 50px rgba(24,61,110,.08); overflow:hidden; }
    .hero:after { content:""; position:absolute; width:300px; height:300px; right:-80px; top:-150px; border:52px solid rgba(31,90,166,.08); border-radius:50%; }
    .eyebrow { color:#E28519; font:11px Arial,sans-serif; letter-spacing:.18em; }
    .hero h1 { margin:15px 0 10px; font-family:"HTSC Type",SimHei,sans-serif !important; font-size:50px; font-weight:400; line-height:1; color:#10233F; letter-spacing:.08em; }
    .hero p { margin:0; color:#647A99; font-size:15px; }
    .hero .date { position:absolute; right:44px; bottom:34px; color:#1F5AA6; font:700 18px Arial,sans-serif; z-index:2; }
    .chapter-nav { position:sticky; top:3.55rem; z-index:20; display:flex; align-items:stretch; margin:0 0 18px; background:rgba(255,255,255,.96); border:1px solid #D8E2F0; box-shadow:0 10px 25px rgba(24,61,110,.08); overflow-x:auto; }
    .chapter-nav a { flex:1 0 auto; min-width:140px; padding:13px 18px 11px; color:#6D7F99; font-size:13px; text-decoration:none; border-right:1px solid #E1E8F1; transition:background .16s,color .16s; }
    .chapter-nav a:last-child { border-right:0; }
    .chapter-nav a b { display:block; margin-bottom:4px; color:#1F5AA6; font:700 10px Arial,sans-serif; letter-spacing:.12em; }
    .chapter-nav a:hover { background:#102B56; color:white; }
    .chapter-nav a:hover b { color:#FFD18B; }
    .section-anchor { position:relative; top:-5.9rem; visibility:hidden; }
    .section-head { display:flex; justify-content:space-between; align-items:end; margin:42px 0 14px; padding-bottom:13px; border-bottom:1px solid #CBD9EB; }
    .section-head small { color:#E28519; font:10px Arial,sans-serif; letter-spacing:.18em; }
    .section-head h2 { margin:5px 0 0; color:#10233F; font-size:28px; }
    .section-head span { color:#7085A3; font-size:13px; }
    .metric-card { min-height:126px; padding:20px 20px 15px; background:rgba(255,255,255,.9); border:1px solid #D8E2F0; border-top:3px solid #1F5AA6; box-shadow:0 10px 28px rgba(24,61,110,.06); }
    .metric-card.warm { border-top-color:#E99A2F; }
    .metric-card span { color:#7185A0; font-size:12px; }
    .metric-card b { display:block; margin-top:19px; color:#102B56; font:700 29px Arial,sans-serif; letter-spacing:-.03em; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .metric-card small { color:#8191A8; font:11px Arial,sans-serif; }
    .weekly { padding:27px 30px; background:#102B56; color:white; border-left:5px solid #E99A2F; box-shadow:0 15px 35px rgba(16,43,86,.16); }
    .weekly h3 { margin:0 0 13px; font-family:"HTSC Type",SimHei,sans-serif !important; font-size:23px; font-weight:400; color:white; }
    .weekly p { margin:0; color:rgba(255,255,255,.77); line-height:1.95; font-size:15px; }
    .filter-summary { padding:17px 20px; background:#E8EEF7; border:1px solid #D2DEED; color:#4C6485; margin:4px 0 13px; }
    .filter-summary b { color:#102B56; font:700 18px Arial,sans-serif; margin:0 4px; }
    .filter-summary span { margin-right:24px; }
    .industry-grid [data-testid="stButton"] button { width:100%; min-height:68px; justify-content:flex-start; text-align:left; background:#315F9F; color:white; border:0; border-radius:4px; font-size:14px; box-shadow:none; }
    .industry-grid [data-testid="stButton"] button:hover { background:#214D8C; color:white; transform:translateY(-2px); }
    div[data-testid="stDataFrame"] { border:1px solid #D5E0EE; box-shadow:0 12px 30px rgba(24,61,110,.06); }
    .stDownloadButton button, div.stButton > button[kind="primary"] { background:#1F5AA6; color:white; border-color:#1F5AA6; border-radius:3px; }
    .stDownloadButton button:hover, div.stButton > button[kind="primary"]:hover { background:#163F76; border-color:#163F76; color:white; }
    .section-head h2, .industry-grid button, [data-testid="stDataFrame"] * { font-family:"HTSC Type",Arial,SimHei,sans-serif !important; }
    [data-testid="stMetricValue"], [data-testid="stMetricDelta"], .num, .stDataFrame { font-family:Arial,sans-serif !important; }
    div[data-baseweb="tab-list"] { gap:8px; }
    button[data-baseweb="tab"] { background:#E8EEF7; padding:9px 18px; }
    button[data-baseweb="tab"][aria-selected="true"] { background:#1F5AA6; color:white; }
    footer { visibility:hidden; }
    @media (max-width:760px) {
      .block-container { width:100%; padding:0.65rem 0.8rem 3rem !important; }
      .hero { margin:13px 0 12px; padding:27px 20px 24px; }
      .hero:after { width:190px; height:190px; right:-80px; top:-105px; border-width:34px; }
      .hero h1 { margin-top:11px; font-size:34px; line-height:1.15; letter-spacing:.04em; }
      .hero p { max-width:84%; font-size:13px; line-height:1.65; }
      .hero .date { position:static; display:block; margin-top:17px; font-size:14px; }
      .top-ticker { gap:12px; margin:0 -0.8rem; padding:10px 14px; border-left:0; font-size:12px; }
      .top-ticker span { font-size:11px; } .top-ticker b { font-size:12px; }
      .chapter-nav { top:2.9rem; margin:0 -0.2rem 13px; box-shadow:0 7px 18px rgba(24,61,110,.08); scrollbar-width:none; }
      .chapter-nav::-webkit-scrollbar { display:none; }
      .chapter-nav a { min-width:112px; padding:9px 11px; font-size:12px; }
      .chapter-nav a b { font-size:9px; }
      .section-head { margin:28px 0 11px; padding-bottom:10px; align-items:flex-start; }
      .section-head h2 { font-size:23px; } .section-head span { display:none; }
      [data-testid="stHorizontalBlock"] { flex-wrap:wrap !important; gap:.65rem !important; }
      [data-testid="column"] { flex:1 1 calc(50% - .4rem) !important; width:calc(50% - .4rem) !important; min-width:0 !important; }
      .metric-card { min-height:104px; padding:15px 14px 12px; }
      .metric-card b { margin-top:13px; font-size:24px; }
      .weekly { padding:21px 18px; border-left-width:4px; }
      .weekly h3 { font-size:19px; line-height:1.55; }
      .weekly p { font-size:13px; line-height:1.85; }
      .filter-summary { padding:13px 14px; }
      .filter-summary span { display:block; margin:4px 0; }
      [data-baseweb="radio"] { margin-right:8px !important; }
      [role="radiogroup"] { display:flex !important; flex-wrap:wrap !important; gap:5px 8px !important; }
      .stDownloadButton button, div.stButton > button { min-height:42px; width:100%; }
      .industry-grid [data-testid="stButton"] button { min-height:58px; padding:8px 10px; font-size:12px; }
      div[data-testid="stDataFrame"] { overflow-x:auto; box-shadow:none; }
      [data-testid="stVegaLiteChart"] { overflow-x:auto; overscroll-behavior-x:contain; }
      [data-testid="stToolbar"] { display:none !important; }
      button[data-baseweb="tab"] { padding:8px 11px; font-size:12px; }
    }
    @media (max-width:430px) {
      .hero h1 { font-size:30px; }
      .metric-card b { font-size:21px; }
      .section-head h2 { font-size:21px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    bonds = pd.read_csv(BASE / "data" / "bonds.csv")
    market = pd.read_csv(BASE / "data" / "market_history.csv", parse_dates=["date"])
    supply = pd.read_csv(BASE / "data" / "supply_history.csv", parse_dates=["date"])
    return bonds, market, supply


def fmt(value, digits=2):
    if pd.isna(value):
        return "—"
    return f"{value:,.{digits}f}"


def metric_card(label, value, unit="", warm=False):
    st.markdown(
        f'<div class="metric-card{" warm" if warm else ""}"><span>{label}</span>'
        f'<b>{value}</b><small>{unit}</small></div>',
        unsafe_allow_html=True,
    )


def section_head(index, title, note=""):
    anchor = index.split()[0]
    st.markdown(
        f'<div id="section-{anchor}" class="section-anchor"></div>'
        f'<div class="section-head"><div><small>{index}</small><h2>{title}</h2></div><span>{note}</span></div>',
        unsafe_allow_html=True,
    )


def choose_industry(name):
    st.session_state["industry_filter"] = [name]
    st.session_state["pool_mode"] = "全市场"


def reset_filters():
    st.session_state["industry_filter"] = []
    st.session_state["pool_mode"] = "全市场"
    st.session_state["numeric_filter_enabled"] = True
    for key in ["price_min", "price_max", "premium_min", "premium_max", "ytm_min", "ytm_max", "balance_min", "balance_max"]:
        st.session_state.pop(key, None)


bonds, market, supply = load_data()
try:
    user_agent = str(st.context.headers.get("User-Agent", "")).lower()
except Exception:
    user_agent = ""
is_mobile = any(token in user_agent for token in ["iphone", "android", "mobile", "ipod"])
latest = market.sort_values("date").iloc[-1]
latest_supply = supply.sort_values("date").iloc[-1]
year_end = supply[supply["date"] <= pd.Timestamp("2025-12-31")].sort_values("date").iloc[-1]
ytd_balance_change = latest_supply["balance"] - year_end["balance"]

if "industry_filter" not in st.session_state:
    st.session_state["industry_filter"] = []
if "pool_mode" not in st.session_state:
    st.session_state["pool_mode"] = "全市场"
if "numeric_filter_enabled" not in st.session_state:
    st.session_state["numeric_filter_enabled"] = True

with st.sidebar:
    st.markdown('<div class="brand-lockup"><b>华泰证券</b><span>HUATAI SECURITIES</span></div>', unsafe_allow_html=True)
    st.markdown("### 个券筛选")
    st.button("清空筛选 · 查看全市场", on_click=reset_filters, width="stretch")
    query = st.text_input("名称 / 代码 / 正股", placeholder="输入关键词")
    industries = sorted(bonds["industry"].dropna().astype(str).unique())
    selected_industries = st.multiselect("行业", industries, key="industry_filter")
    ratings = sorted(bonds["rating"].dropna().astype(str).unique())
    selected_ratings = st.multiselect("评级", ratings)
    st.markdown("---")
    numeric_filter_enabled = st.checkbox("启用数值区间筛选", key="numeric_filter_enabled")
    price_min = price_max = premium_min = premium_max = ytm_min = ytm_max = balance_min = balance_max = None
    if numeric_filter_enabled:
        st.caption("范围可直接输入，不设上限或下限；留空即不限制。")
        left, right = st.columns(2)
        with left:
            price_min = st.number_input("转债价格 ≥", value=None, step=1.0, key="price_min", placeholder="不限制")
            premium_min = st.number_input("转股溢价率 ≥", value=None, step=1.0, key="premium_min", placeholder="不限制")
            ytm_min = st.number_input("YTM ≥", value=None, step=1.0, key="ytm_min", placeholder="不限制")
            balance_min = st.number_input("剩余余额 ≥", value=None, step=1.0, key="balance_min", placeholder="不限制")
        with right:
            price_max = st.number_input("转债价格 ≤", value=None, step=1.0, key="price_max", placeholder="不限制")
            premium_max = st.number_input("转股溢价率 ≤", value=None, step=1.0, key="premium_max", placeholder="不限制")
            ytm_max = st.number_input("YTM ≤", value=None, step=1.0, key="ytm_max", placeholder="不限制")
            balance_max = st.number_input("剩余余额 ≤", value=None, step=1.0, key="balance_max", placeholder="不限制")
    st.caption("数据更新至 2026-07-31")

st.markdown(
    f"""
    <div class="top-ticker">
      <span>价格中位数 <b>{fmt(latest['price_median'])}</b></span><i></i>
      <span>全市场成交 <b>{fmt(latest['turnover_total'])}亿</b></span><i></i>
      <span>平价溢价率 <b>{fmt(latest['premium_median'])}%</b></span><i></i>
      <span>市场余额 <b>{fmt(latest_supply['balance'])}亿</b></span><i></i>
      <span>数据日期 <em>2026.07.31</em></span>
    </div>
    <div class="hero">
      <div class="eyebrow">华泰固收 / CONVERTIBLE BOND RESEARCH</div>
      <h1>可转债数据库</h1>
      <p>市场数据、估值结构、个券筛选与供给变化</p>
      <span class="date">2026 / 07 / 31</span>
    </div>
    <nav class="chapter-nav" aria-label="页面章节导航">
      <a href="#section-01"><b>01 / MARKET</b>市场总览</a>
      <a href="#section-02"><b>02 / VALUATION</b>估值分布</a>
      <a href="#section-03"><b>03 / WEEKLY VIEW</b>本周观点</a>
      <a href="#section-04"><b>04 / BOND UNIVERSE</b>个券机会池</a>
      <a href="#section-05"><b>05 / STRUCTURE</b>行业分布</a>
      <a href="#section-06"><b>06 / RATING</b>评级矩阵</a>
      <a href="#section-07"><b>07 / SUPPLY</b>存量与供给</a>
    </nav>
    """,
    unsafe_allow_html=True,
)

section_head("01 / MARKET", "市场总览", "核心指标均来自所提供数据库")
metric_cols = st.columns(6)
metrics = [
    ("市场只数", fmt(latest_supply["count"], 0), "只", False),
    ("价格中位数", fmt(latest["price_median"]), "元", False),
    ("平价中位数", fmt(latest["parity_median"]), "元", False),
    ("转股溢价率", fmt(latest["premium_median"]), "%", True),
    ("YTM中位数", fmt(latest["ytm_median"]), "%", False),
    ("隐含波动率", fmt(latest["implied_vol"]), "%", True),
]
for col, item in zip(metric_cols, metrics):
    with col:
        metric_card(*item)

trend_metric_col, trend_range_col = st.columns([1.15, 1])
with trend_metric_col:
    trend_metric = st.radio(
        "走势指标",
        ["价格中位数", "转股溢价率", "全市场成交额", "YTM中位数"],
        horizontal=True,
        label_visibility="collapsed",
    )
with trend_range_col:
    trend_range = st.radio(
        "时间范围",
        ["近三个月", "近半年", "近一年", "全部历史"],
        index=2,
        horizontal=True,
        label_visibility="collapsed",
    )
metric_map = {
    "价格中位数": ("price_median", "元"),
    "转股溢价率": ("premium_median", "%"),
    "全市场成交额": ("turnover_total", "亿元"),
    "YTM中位数": ("ytm_median", "%"),
}
metric_col, metric_unit = metric_map[trend_metric]
trend_points = {"近三个月": 65, "近半年": 130, "近一年": 260}
trend = market.sort_values("date")
if trend_range in trend_points:
    trend = trend.tail(trend_points[trend_range])
axis_format = "%Y-%m" if len(trend) > 130 else "%m/%d"
line = (
    alt.Chart(trend)
    .mark_area(line={"color": BLUE, "strokeWidth": 2.4}, color=SKY, opacity=0.18)
    .encode(
        x=alt.X("date:T", title=None, axis=alt.Axis(format=axis_format, labelColor="#6E819D")),
        y=alt.Y(f"{metric_col}:Q", title=f"{trend_metric}（{metric_unit}）", scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip("date:T", title="日期", format="%Y-%m-%d"), alt.Tooltip(f"{metric_col}:Q", title=trend_metric, format=",.2f")],
    )
    .properties(height=285)
)
st.altair_chart(line, width="stretch")

base_filtered = bonds.copy()
if query:
    mask = pd.Series(False, index=base_filtered.index)
    for col in ["name", "code", "industry", "stock_code"]:
        mask |= base_filtered[col].fillna("").astype(str).str.contains(query, case=False, regex=False)
    base_filtered = base_filtered[mask]
if selected_industries:
    base_filtered = base_filtered[base_filtered["industry"].isin(selected_industries)]
if selected_ratings:
    base_filtered = base_filtered[base_filtered["rating"].isin(selected_ratings)]
if numeric_filter_enabled:
    for column, lower, upper in [
        ("price", price_min, price_max), ("premium", premium_min, premium_max),
        ("ytm", ytm_min, ytm_max), ("balance", balance_min, balance_max),
    ]:
        if lower is not None:
            base_filtered = base_filtered[base_filtered[column] >= lower]
        if upper is not None:
            base_filtered = base_filtered[base_filtered[column] <= upper]

section_head("02 / VALUATION MAP", "估值分布", "YTM × 平价溢价率；颜色代表评级，气泡大小代表剩余余额")
valid_scatter = base_filtered.dropna(subset=["ytm", "premium", "balance", "remaining"]).copy()
if len(valid_scatter):
    # Fixed main view: broad enough to retain the useful valuation structure.
    x_low, x_high, y_low, y_high = -10, 2.2, 0, 180
    plot_scatter = valid_scatter[
        valid_scatter["ytm"].between(x_low, x_high)
        & valid_scatter["premium"].between(y_low, y_high)
    ].copy()

    plot_scatter["bond_label"] = plot_scatter.apply(
        lambda row: f"{row['name']}，{row['remaining']:.1f}年", axis=1
    )
    black_axis = dict(
        grid=True, gridDash=[6, 5], gridColor="#B9C1CD", tickCount=8,
        domainColor="#111111", domainWidth=1.4, tickColor="#111111", tickWidth=1.2,
        labelColor="#111111", titleColor="#111111",
    )
    axis_x = alt.X("ytm:Q", title="YTM（%）", scale=alt.Scale(domain=[x_low, x_high]), axis=alt.Axis(**black_axis))
    axis_y = alt.Y("premium:Q", title="平价溢价率（%）", scale=alt.Scale(domain=[y_low, y_high]), axis=alt.Axis(**black_axis))
    size_legend = None if is_mobile else alt.Legend(
        orient="bottom", direction="horizontal", columns=5,
        symbolFillColor="#7EA3D4", symbolStrokeColor="#263952",
        symbolStrokeWidth=.7, symbolOpacity=.9,
    )
    bubble_size_range = [45, 900] if is_mobile else [70, 1600]
    scatter = (
        alt.Chart(plot_scatter)
        .mark_circle(opacity=.9, stroke="#263952", strokeWidth=.65)
        .encode(
            x=axis_x,
            y=axis_y,
            size=alt.Size(
                "balance:Q",
                title="剩余余额（亿元）",
                scale=alt.Scale(range=bubble_size_range),
                legend=size_legend,
            ),
            color=alt.Color(
                "rating:N",
                title="评级",
                scale=alt.Scale(
                    domain=["AAA", "AA+", "AA", "AA-", "A+", "A"],
                    range=["#102B56", "#1F5AA6", "#5F88C2", "#A7BEDC", "#E8B05A", "#C96A4A"],
                ),
                legend=alt.Legend(
                    orient="bottom", direction="horizontal", columns=3 if is_mobile else 6,
                    symbolStrokeColor="#263952", symbolStrokeWidth=.7, symbolOpacity=.9,
                ),
            ),
            tooltip=[
                alt.Tooltip("name:N", title="转债"), alt.Tooltip("code:N", title="代码"), alt.Tooltip("industry:N", title="行业"), alt.Tooltip("rating:N", title="评级"),
                alt.Tooltip("ytm:Q", title="YTM", format=".2f"), alt.Tooltip("premium:Q", title="平价溢价率", format=".2f"),
                alt.Tooltip("balance:Q", title="余额（亿元）", format=".2f"), alt.Tooltip("remaining:Q", title="剩余期限（年）", format=".1f"),
            ],
        )
    )
    value_ceiling = value_curve_limit(plot_scatter["ytm"])
    in_high_value_region = (
        plot_scatter["ytm"].between(VALUE_CURVE[0][0], VALUE_CURVE[-1][0])
        & plot_scatter["premium"].ge(0)
        & plot_scatter["premium"].le(value_ceiling)
    )
    # Keep the two right-side watch zones fully readable: the elevated-premium
    # corner and the lower-right value corner.  The rest stays selectively
    # labelled by issue size so the map remains legible.
    in_right_upper_watch = (
        plot_scatter["ytm"].between(-0.8, 2.2)
        & plot_scatter["premium"].between(105, 180)
    )
    in_right_lower_watch = (
        plot_scatter["ytm"].between(-0.8, 2.2)
        & plot_scatter["premium"].between(0, 22)
    )
    label_source = plot_scatter[
        (plot_scatter["balance"] >= 10)
        | in_high_value_region
        | in_right_upper_watch
        | in_right_lower_watch
    ].copy()
    labels = (
        alt.Chart(label_source)
        .mark_text(
            align="left", dx=7, dy=-6,
            fontSize=7 if is_mobile else 9,
            color="#172235", opacity=.92,
        )
        .encode(x=axis_x, y=axis_y, text="bond_label:N")
    )
    # Fixed structural guides: bottom anchor, top anchor and right anchor.
    # They describe valuation structure only and do not define a selection area.
    upper_left = pd.DataFrame({"ytm": [-4.0, -2.0], "premium": [0, 180]})
    upper_right = pd.DataFrame({"ytm": [-2.0, 2.2], "premium": [180, 42]})
    lower_right = pd.DataFrame({"ytm": [-4.0, 2.2], "premium": [0, 42]})
    payoff_curve = pd.DataFrame(VALUE_CURVE, columns=["ytm", "premium"])
    value_note = pd.DataFrame({"ytm": [.75], "premium": [2.5], "text": ["高性价比区域"]})
    chart = (
        scatter
        + alt.Chart(upper_left).mark_line(color="#111111", strokeDash=[9, 5], strokeWidth=2.5).encode(x=axis_x, y=axis_y)
        + alt.Chart(upper_right).mark_line(color="#111111", strokeDash=[9, 5], strokeWidth=2.5).encode(x=axis_x, y=axis_y)
        + alt.Chart(lower_right).mark_line(color="#111111", strokeDash=[9, 5], strokeWidth=2.5).encode(x=axis_x, y=axis_y)
        + alt.Chart(payoff_curve).mark_line(color="#F2A900", strokeWidth=3.8, interpolate="monotone").encode(x=axis_x, y=axis_y)
        + alt.Chart(value_note).mark_text(fontSize=16, color="#102B56", angle=340).encode(x=axis_x, y=axis_y, text="text:N")
        + labels
    ).properties(height=520 if is_mobile else 620).configure_view(stroke="#D7DCE5")
    st.altair_chart(chart, width="stretch")
else:
    st.info("当前筛选条件下没有可绘制的个券。")

section_head("03 / WEEKLY VIEW", "本周观点")
st.markdown(
    """
    <div class="weekly">
      <h3>转债建议：仓位无需调整，重视结构分化</h3>
      <p>上周我们建议不再降低仓位，市场如期修复，符合预期。但略超预期的是，转债结构分化进一步加剧。逻辑层面虽能部分解释这一现象，但从定量视角看估值分化已过于极致。我们认为双高品种的风险正在持续积聚，短期强势表现的背后是估值的进一步抬升，定价已趋于非理性。低价品种的短期滞涨或与ETF小幅流出有关，反而提供了较好的介入窗口。我们建议投资者短期无需过度调整转债仓位，核心是规避结构风险、向性价比更优的方向倾斜。低溢价银行、红利品种均是当前较好的参与标的，短期配置价值或优于纯债。此外，下半年仍需规避条款风险。</p>
    </div>
    """,
    unsafe_allow_html=True,
)

section_head("04 / BOND UNIVERSE", "个券机会池", "筛选、排序与明细联动")
pool_mode = st.radio(
    "机会池",
    ["全市场", "高性价比", "成交活跃", "低溢价", "正YTM", "双高品种"],
    horizontal=True,
    key="pool_mode",
    label_visibility="collapsed",
)

filtered = base_filtered.copy()
if pool_mode == "高性价比":
    value_ceiling = value_curve_limit(filtered["ytm"])
    filtered = filtered[
        filtered["ytm"].between(VALUE_CURVE[0][0], VALUE_CURVE[-1][0])
        & filtered["premium"].ge(0)
        & filtered["premium"].le(value_ceiling)
    ]
elif pool_mode == "成交活跃":
    filtered = filtered[filtered["turnover"] >= filtered["turnover"].quantile(.75)]
elif pool_mode == "低溢价":
    filtered = filtered[filtered["premium"] < 15]
elif pool_mode == "正YTM":
    filtered = filtered[filtered["ytm"] >= 0]
elif pool_mode == "双高品种":
    filtered = filtered[(filtered["price"] >= 140) & (filtered["premium"] >= 50)]

sort_options = {
    "成交额": "turnover", "YTM": "ytm", "转股溢价率": "premium", "价格": "price",
    "平价": "parity", "纯债溢价率": "floor_premium", "剩余余额": "balance", "剩余期限": "remaining",
}
sort_col, order_col, download_col = st.columns([1.2, .8, 1])
with sort_col:
    sort_label = st.selectbox("排序指标", list(sort_options), index=0)
with order_col:
    sort_order = st.selectbox("排序方向", ["从高到低", "从低到高"])
with download_col:
    st.write("")
    st.write("")
    st.download_button(
        "下载当前筛选结果",
        filtered.to_csv(index=False, encoding="utf-8-sig"),
        file_name="可转债筛选结果.csv",
        mime="text/csv",
        width="stretch",
    )

filtered = filtered.sort_values(sort_options[sort_label], ascending=sort_order == "从低到高", na_position="last")
summary_cols = st.columns(5)
summary_values = [
    ("筛选结果", len(filtered), "只"),
    ("价格中位数", filtered["price"].median(), "元"),
    ("溢价率中位数", filtered["premium"].median(), "%"),
    ("YTM中位数", filtered["ytm"].median(), "%"),
    ("成交额合计", filtered["turnover"].sum() / 100, "亿元"),
]
for col, (label, value, unit) in zip(summary_cols, summary_values):
    with col:
        metric_card(label, fmt(value, 0 if label == "筛选结果" else 2), unit)

table = filtered.rename(
    columns={
        "name": "转债名称", "code": "转债代码", "industry": "行业", "price": "价格",
        "change": "转债涨跌", "stock_change": "正股涨跌", "turnover": "成交额(百万元)",
        "parity": "平价", "premium": "转股溢价率", "ytm": "YTM", "floor_premium": "纯债溢价率",
        "remaining": "剩余期限", "balance": "剩余余额(亿元)", "rating": "评级", "list_date": "上市日期",
    }
)[[
    "转债名称", "转债代码", "行业", "价格", "转债涨跌", "正股涨跌", "成交额(百万元)",
    "平价", "转股溢价率", "YTM", "纯债溢价率", "剩余期限", "剩余余额(亿元)", "评级", "上市日期",
]]
st.dataframe(
    table,
    width="stretch",
    height=650,
    hide_index=True,
    column_config={
        "价格": st.column_config.NumberColumn(format="%.3f"),
        "转债涨跌": st.column_config.NumberColumn(format="%+.2f%%"),
        "正股涨跌": st.column_config.NumberColumn(format="%+.2f%%"),
        "成交额(百万元)": st.column_config.NumberColumn(format="%.2f"),
        "平价": st.column_config.NumberColumn(format="%.2f"),
        "转股溢价率": st.column_config.NumberColumn(format="%.2f%%"),
        "YTM": st.column_config.NumberColumn(format="%.2f%%"),
        "纯债溢价率": st.column_config.NumberColumn(format="%.2f%%"),
        "剩余期限": st.column_config.NumberColumn(format="%.2f年"),
        "剩余余额(亿元)": st.column_config.NumberColumn(format="%.2f"),
    },
)
st.caption("表格可再次点击任意数值列标题排序；当前显示全部筛选结果。")

section_head("05 / MARKET STRUCTURE", "全市场行业分布", "点击行业卡片可回到机会池筛选")
industry_counts = bonds["industry"].fillna("未分类").value_counts().rename_axis("行业").reset_index(name="只数")
industry_chart = (
    alt.Chart(industry_counts.sort_values("只数"))
    .mark_bar(color=BLUE, cornerRadiusEnd=3)
    .encode(
        x=alt.X("只数:Q", title="个券数量"),
        y=alt.Y("行业:N", sort="-x", title=None),
        tooltip=["行业:N", "只数:Q"],
    )
    .properties(height=620)
)
st.altair_chart(industry_chart, width="stretch")

st.markdown('<div class="industry-grid">', unsafe_allow_html=True)
industry_columns = 2 if is_mobile else 6
for start in range(0, len(industry_counts), industry_columns):
    cols = st.columns(industry_columns)
    for col, row in zip(cols, industry_counts.iloc[start : start + industry_columns].itertuples(index=False)):
        with col:
            st.button(f"{row.行业}　{row.只数}只", key=f"industry_{row.行业}", on_click=choose_industry, args=(row.行业,))
st.markdown("</div>", unsafe_allow_html=True)

section_head("06 / RATING MATRIX", "评级与价格矩阵", "统一蓝色深浅表示数量")
heat = bonds[["rating", "price"]].copy()
heat["评级"] = heat["rating"].where(heat["rating"].isin(["AAA", "AA+", "AA", "AA-", "A+", "A"]), "A及以下")
heat["价格区间"] = pd.cut(heat["price"], [-float("inf"), 115, 140, float("inf")], labels=["低价 <115", "中价 115–140", "高价 >140"])
heat = heat.groupby(["评级", "价格区间"], observed=False).size().reset_index(name="只数")
heatmap = (
    alt.Chart(heat)
    .mark_rect(cornerRadius=4)
    .encode(
        x=alt.X(
            "价格区间:N",
            sort=["低价 <115", "中价 115–140", "高价 >140"],
            title=None,
            axis=alt.Axis(labelAngle=0, labelPadding=12),
        ),
        y=alt.Y("评级:N", sort=["AAA", "AA+", "AA", "AA-", "A+", "A", "A及以下"], title=None),
        color=alt.Color("只数:Q", scale=alt.Scale(range=["#E8EEF7", "#1F5AA6"]), legend=None),
        tooltip=["评级:N", "价格区间:N", "只数:Q"],
    )
    .properties(height=310)
)
labels = heatmap.mark_text(font="Arial", fontSize=16).encode(text="只数:Q", color=alt.condition(alt.datum.只数 > 10, alt.value("white"), alt.value(NAVY)))
st.altair_chart(heatmap + labels, width="stretch")

section_head("07 / SUPPLY", "存量与供给", "余额变化采用年末存量对比口径")
supply_cols = st.columns([1, 1, 1, 2.2])
with supply_cols[0]:
    metric_card("最新余额", fmt(latest_supply["balance"]), "亿元")
with supply_cols[1]:
    metric_card("市场只数", fmt(latest_supply["count"], 0), "只")
with supply_cols[2]:
    metric_card("年内余额变化", fmt(ytd_balance_change), "亿元", True)
with supply_cols[3]:
    recent_supply = supply.sort_values("date").tail(20)
    supply_chart = (
        alt.Chart(recent_supply)
        .mark_line(color=BLUE, point=alt.OverlayMarkDef(color=ORANGE, size=55), strokeWidth=2.4)
        .encode(
            x=alt.X("date:T", title=None, axis=alt.Axis(format="%m/%d")),
            y=alt.Y("balance:Q", title="余额（亿元）", scale=alt.Scale(zero=False)),
            tooltip=[alt.Tooltip("date:T", title="日期", format="%Y-%m-%d"), alt.Tooltip("balance:Q", title="余额", format=",.2f"), alt.Tooltip("count:Q", title="只数")],
        )
        .properties(height=190)
    )
    st.altair_chart(supply_chart, width="stretch")

st.markdown("---")
st.markdown("**华泰固收 · 可转债数据库**　　<span class='num'>DATA AS OF 2026.07.31</span>", unsafe_allow_html=True)
