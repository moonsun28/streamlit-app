"""
CoSense — 코리빙 임대 입지 분석 플랫폼
Streamlit Community Cloud 배포용
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import snowflake.connector
import re

# ── 브랜드 컬러 ────────────────────────────────────────────────────
SF_BLUE       = "#29B5E8"
SF_DARK_BLUE  = "#11567F"
SF_NAVY       = "#0D2137"
SF_LIGHT_BLUE = "#E3F4FC"
SF_GRAY       = "#F5F7FA"
SF_SUCCESS    = "#2ECC71"
SF_WARNING    = "#F39C12"
SF_DANGER     = "#E74C3C"

# ── 페이지 설정 ────────────────────────────────────────────────────
st.set_page_config(
    page_title="CoSense | 코리빙 입지 분석",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  .main .block-container {{ padding-top: 1.5rem; padding-bottom: 1rem; max-width: 1200px; }}
  [data-testid="stSidebar"] {{ background: linear-gradient(180deg, {SF_NAVY} 0%, {SF_DARK_BLUE} 100%); }}
  [data-testid="stSidebar"] * {{ color: #FFFFFF !important; }}
  [data-testid="stSidebar"] .stSelectbox label,
  [data-testid="stSidebar"] .stSlider label {{ color: #A8D8F0 !important; font-size: 0.82rem; letter-spacing: 0.04em; text-transform: uppercase; }}
  [data-testid="stSidebar"] [data-baseweb="select"] > div {{ background: rgba(255,255,255,0.12) !important; border: 1px solid rgba(255,255,255,0.25) !important; border-radius: 8px; }}
  [data-testid="stSidebar"] .stSlider [data-testid="stTickBar"] span {{ color: #A8D8F0 !important; }}
  .cosense-header {{
    background: linear-gradient(135deg, {SF_NAVY} 0%, {SF_DARK_BLUE} 60%, {SF_BLUE} 100%);
    border-radius: 12px; padding: 1.2rem 1.8rem; margin-bottom: 1.2rem;
    display: flex; align-items: center; justify-content: space-between;
  }}
  .cosense-header h1 {{ color: #FFFFFF; font-size: 1.6rem; font-weight: 700; margin: 0; letter-spacing: -0.02em; }}
  .cosense-header p  {{ color: #A8D8F0; font-size: 0.88rem; margin: 0.2rem 0 0; }}
  .cosense-badge {{
    background: rgba(41,181,232,0.25); border: 1px solid {SF_BLUE};
    border-radius: 20px; padding: 0.3rem 0.9rem;
    color: {SF_BLUE}; font-size: 0.78rem; font-weight: 600;
  }}
  .kpi-card {{
    background: #FFFFFF; border: 1px solid #E2EBF4; border-radius: 12px;
    padding: 1.1rem 1.2rem; box-shadow: 0 2px 8px rgba(17,86,127,0.08); height: 100%;
  }}
  .kpi-label {{ color: #6B7F96; font-size: 0.78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.4rem; }}
  .kpi-value {{ color: {SF_NAVY}; font-size: 1.7rem; font-weight: 800; line-height: 1.1; }}
  .kpi-sub   {{ color: #8FA3B8; font-size: 0.78rem; margin-top: 0.3rem; }}
  .kpi-icon  {{ font-size: 1.4rem; float: right; margin-top: -0.2rem; }}
  .kpi-card.highlight {{ border-top: 3px solid {SF_BLUE}; }}
  .kpi-card.success   {{ border-top: 3px solid {SF_SUCCESS}; }}
  .section-title {{
    color: {SF_DARK_BLUE}; font-size: 0.95rem; font-weight: 700;
    border-left: 4px solid {SF_BLUE}; padding-left: 0.7rem;
    margin: 1.2rem 0 0.7rem; text-transform: uppercase; letter-spacing: 0.04em;
  }}
  .insight-box {{
    background: linear-gradient(135deg, {SF_LIGHT_BLUE} 0%, #FFFFFF 100%);
    border: 1px solid {SF_BLUE}; border-radius: 12px; padding: 1.3rem 1.6rem;
  }}
  .insight-text {{ color: {SF_NAVY}; font-size: 0.94rem; line-height: 1.7; }}
  .powered-by {{ margin-top: 0.8rem; text-align: right; color: {SF_DARK_BLUE}; font-size: 0.75rem; font-weight: 600; opacity: 0.7; }}
  hr.section-divider {{ border: none; border-top: 1px solid #E2EBF4; margin: 1rem 0; }}
</style>
""", unsafe_allow_html=True)

# ── Snowflake 연결 ────────────────────────────────────────────────
@st.cache_resource
def get_connection():
    import base64
    from cryptography.hazmat.primitives import serialization
    private_key_pem = base64.b64decode(st.secrets["snowflake"]["private_key_base64"])
    private_key = serialization.load_pem_private_key(private_key_pem, password=None)
    return snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        account=st.secrets["snowflake"]["account"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"],
        role=st.secrets["snowflake"]["role"],
        private_key=private_key.private_bytes(
            serialization.Encoding.DER,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()
        )
    )
def run_query(query):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetch_pandas_all()

# ── 데이터 로드 ───────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def load_result():
    return run_query("""
        SELECT GU, DONG, TOTAL_SCORE, FINAL_GRADE, GROWTH_GRADE,
               SCORE_INCOME, SCORE_FLOATING, SCORE_CONSUMPTION,
               LOCATION_DEMAND_SCORE, SCORE_AFFORDABILITY,
               VISITING_6M_GROWTH, INCOME_6M_GROWTH, SALES_6M_GROWTH,
               TOTAL_DEMAND_POOL, AVG_RENT_CAPACITY, TOP_RENT_BAND,
               RECOMMENDED_RENT, SUPPLY_DENSITY, COMPETITOR_CNT,
               AVG_OCCUPANCY_RATE, DEMAND_FORECAST_1M, DEMAND_FORECAST_6M,
               FORECAST_TREND, FORECAST_METHOD, AI_INSIGHT, INSIGHT_METHOD
        FROM COSENSE_DB.ANALYTICS.COSENSE_RESULT
        ORDER BY TOTAL_SCORE DESC
    """)

@st.cache_data(ttl=1800, show_spinner=False)
def load_rent_demand():
    return run_query("""
        SELECT GU, DONG, RENT_BAND,
               SUM(DEMAND_POOL) AS DEMAND_POOL,
               AVG(AVG_RENT_CAPACITY) AS AVG_RENT_CAPACITY
        FROM COSENSE_DB.ANALYTICS.RENT_DEMAND_POOL
        WHERE BASE_YM = (SELECT MAX(BASE_YM) FROM COSENSE_DB.ANALYTICS.RENT_DEMAND_POOL)
        GROUP BY GU, DONG, RENT_BAND
        ORDER BY GU, DONG, RENT_BAND
    """)

@st.cache_data(ttl=1800, show_spinner=False)
def load_forecast():
    return run_query("""
        SELECT GU, DONG, FORECAST_YM,
               FORECAST_SCORE, LOWER_BOUND, UPPER_BOUND, METHOD
        FROM COSENSE_DB.ML.DEMAND_FORECAST
        ORDER BY GU, DONG, FORECAST_YM
    """)

@st.cache_data(ttl=1800, show_spinner=False)
def load_demand_signal():
    return run_query("""
        SELECT GU, DONG, BASE_YM, DEMAND_SCORE
        FROM COSENSE_DB.ANALYTICS.DEMAND_SIGNAL
        ORDER BY GU, DONG, BASE_YM
    """)

with st.spinner("데이터 로딩 중..."):
    df_result   = load_result()
    df_rent     = load_rent_demand()
    df_forecast = load_forecast()
    df_signal   = load_demand_signal()

# ── 사이드바 ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0 1.5rem;">
      <div style="font-size:2.2rem;">🏢</div>
      <div style="font-size:1.3rem; font-weight:800; color:#FFFFFF; letter-spacing:-0.02em;">CoSense</div>
      <div style="font-size:0.75rem; color:#A8D8F0; margin-top:0.2rem;">코리빙 입지 분석 플랫폼</div>
    </div>
    <hr style="border:none; border-top:1px solid rgba(255,255,255,0.15); margin-bottom:1.5rem;">
    """, unsafe_allow_html=True)

    gu_list = sorted(df_result["GU"].unique().tolist())
    sel_gu = st.selectbox("자치구", gu_list, index=0)

    dong_list = sorted(df_result[df_result["GU"] == sel_gu]["DONG"].unique().tolist())
    sel_dong = st.selectbox("행정동", dong_list, index=0)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    rent_min, rent_max = st.slider(
        "타겟 임대료 구간 (만원)",
        min_value=60, max_value=300, value=(75, 150), step=10,
        format="%d만원"
    )

    st.markdown("<hr style='border:none; border-top:1px solid rgba(255,255,255,0.15); margin:1.5rem 0 1rem'>", unsafe_allow_html=True)

    st.markdown("<div style='font-size:0.78rem; color:#A8D8F0; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:0.5rem;'>전체 입지 순위 TOP 5</div>", unsafe_allow_html=True)
    top5 = df_result.head(5)[["GU","DONG","TOTAL_SCORE","FINAL_GRADE"]].reset_index(drop=True)
    for _, row in top5.iterrows():
        grade_color = {"S":"#FFD700","A":SF_BLUE,"B":SF_SUCCESS,"C":"#95A5A6"}.get(str(row["FINAL_GRADE"]), "#ccc")
        is_selected = (row["GU"] == sel_gu and row["DONG"] == sel_dong)
        bg = "rgba(41,181,232,0.18)" if is_selected else "transparent"
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center;
                    padding:0.3rem 0.5rem; border-radius:6px; background:{bg}; margin-bottom:2px;">
          <span style="font-size:0.82rem; color:#FFFFFF;">{row['GU'][:3]} {row['DONG']}</span>
          <span style="font-size:0.82rem; font-weight:700; color:{SF_BLUE};">{row['TOTAL_SCORE']}점</span>
          <span style="font-size:0.75rem; background:{grade_color}; color:{'#000' if row['FINAL_GRADE']=='S' else '#fff'};
                       padding:1px 7px; border-radius:10px; font-weight:700;">{row['FINAL_GRADE']}</span>
        </div>
        """, unsafe_allow_html=True)

# ── 필터 & 헬퍼 ──────────────────────────────────────────────────
row_sel = df_result[(df_result["GU"] == sel_gu) & (df_result["DONG"] == sel_dong)]

def rent_range_to_bands(rmin, rmax):
    band_map = [
        ("①45만이하",    0,   45),
        ("②45~60만",    45,   60),
        ("③60~75만",    60,   75),
        ("④75~90만",    75,   90),
        ("⑤90~120만",   90,  120),
        ("⑥120~150만", 120,  150),
        ("⑦150~200만", 150,  200),
        ("⑧200~300만", 200,  300),
        ("⑨300만이상",  300, 9999),
    ]
    return [name for name, lo, hi in band_map if rmax > lo and rmin < hi]

active_bands = rent_range_to_bands(rent_min, rent_max)

# ── 메인 헤더 ─────────────────────────────────────────────────────
if not row_sel.empty:
    r = row_sel.iloc[0]
    grade = str(r["FINAL_GRADE"])
    grade_color = {"S":"#FFD700","A":SF_BLUE,"B":SF_SUCCESS,"C":"#95A5A6"}.get(grade, "#ccc")
    grade_text_color = "#000" if grade == "S" else "#fff"

    st.markdown(f"""
    <div class="cosense-header">
      <div>
        <h1>🏢 {sel_gu} {sel_dong}</h1>
        <p>코리빙 임대 입지 종합 분석 리포트 &nbsp;·&nbsp; 데이터 기준: 2024년</p>
      </div>
      <div style="display:flex; gap:0.6rem; align-items:center;">
        <span style="background:{grade_color}; color:{grade_text_color};
                     padding:0.4rem 1.1rem; border-radius:20px; font-size:0.95rem; font-weight:800;">
          {grade}등급
        </span>
        <span class="cosense-badge">입지점수 {r['TOTAL_SCORE']}점</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="cosense-header">
      <div>
        <h1>🏢 {sel_gu} {sel_dong}</h1>
        <p>데이터를 불러오는 중입니다...</p>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.warning("해당 동의 분석 데이터가 없습니다. 다른 동을 선택해 주세요.")
    st.stop()

# ── KPI 카드 ──────────────────────────────────────────────────────
st.markdown('<div class="section-title">핵심 지표</div>', unsafe_allow_html=True)

recommended_rent = r["RECOMMENDED_RENT"]
rent_display = f"{int(recommended_rent/10000):,}만원" if pd.notna(recommended_rent) and recommended_rent > 0 else "N/A"

df_rent_sel = df_rent[(df_rent["GU"] == sel_gu) & (df_rent["DONG"] == sel_dong)]
df_rent_active = df_rent_sel[df_rent_sel["RENT_BAND"].isin(active_bands)]
active_demand_pool = int(df_rent_active["DEMAND_POOL"].sum()) if not df_rent_active.empty else 0

demand_score = r["LOCATION_DEMAND_SCORE"]
demand_score_display = f"{demand_score:.1f}" if pd.notna(demand_score) else "N/A"

supply_density = str(r["SUPPLY_DENSITY"]) if pd.notna(r["SUPPLY_DENSITY"]) else "N/A"
density_color_map = {"미개척": SF_SUCCESS, "희소": SF_BLUE, "보통": SF_WARNING, "과밀": SF_DANGER}
density_color = density_color_map.get(supply_density, "#95A5A6")
density_icon  = {"미개척":"🟢","희소":"🔵","보통":"🟡","과밀":"🔴"}.get(supply_density, "⚪")

kpi_cols = st.columns(4, gap="small")

with kpi_cols[0]:
    st.markdown(f"""
    <div class="kpi-card highlight">
      <div class="kpi-label">추천 월임대료 <span class="kpi-icon">💰</span></div>
      <div class="kpi-value" style="color:{SF_DARK_BLUE};">{rent_display}</div>
      <div class="kpi-sub">전세가율 기반 월세 추산</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[1]:
    st.markdown(f"""
    <div class="kpi-card success">
      <div class="kpi-label">잠재 수요풀 <span class="kpi-icon">👥</span></div>
      <div class="kpi-value" style="color:{SF_SUCCESS};">{active_demand_pool:,}명</div>
      <div class="kpi-sub">{rent_min}~{rent_max}만원 구간</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[2]:
    score_val = float(demand_score) if pd.notna(demand_score) else 0
    score_color = SF_SUCCESS if score_val >= 70 else (SF_BLUE if score_val >= 50 else SF_WARNING)
    st.markdown(f"""
    <div class="kpi-card" style="border-top:3px solid {score_color};">
      <div class="kpi-label">수요 신호 스코어 <span class="kpi-icon">📊</span></div>
      <div class="kpi-value" style="color:{score_color};">{demand_score_display}</div>
      <div class="kpi-sub">0~100점 정규화</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[3]:
    competitor_cnt = int(r["COMPETITOR_CNT"]) if pd.notna(r["COMPETITOR_CNT"]) else 0
    st.markdown(f"""
    <div class="kpi-card" style="border-top:3px solid {density_color};">
      <div class="kpi-label">경쟁 공급 밀도 <span class="kpi-icon">{density_icon}</span></div>
      <div class="kpi-value" style="color:{density_color};">{supply_density}</div>
      <div class="kpi-sub">경쟁사 {competitor_cnt}개소</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

# ── 수요 분석 차트 ────────────────────────────────────────────────
st.markdown('<div class="section-title">수요 분석</div>', unsafe_allow_html=True)
chart_l, chart_r = st.columns([1, 1], gap="medium")

with chart_l:
    st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{SF_DARK_BLUE}; margin-bottom:0.5rem;'>💰 임대료 구간별 잠재 수요풀</div>", unsafe_allow_html=True)

    RENT_BAND_ORDER = ["①45만이하","②45~60만","③60~75만","④75~90만",
                       "⑤90~120만","⑥120~150만","⑦150~200만","⑧200~300만","⑨300만이상"]
    RENT_BAND_LABEL = ["~45만","45~60만","60~75만","75~90만",
                       "90~120만","120~150만","150~200만","200~300만","300만~"]

    if not df_rent_sel.empty:
        band_agg = df_rent_sel.groupby("RENT_BAND")["DEMAND_POOL"].sum().reset_index()
        band_df = pd.DataFrame({"RENT_BAND": RENT_BAND_ORDER, "LABEL": RENT_BAND_LABEL})
        band_df = band_df.merge(band_agg, on="RENT_BAND", how="left").fillna(0)
        band_df["DEMAND_POOL"] = band_df["DEMAND_POOL"].astype(int)
        band_df["SELECTED"] = band_df["RENT_BAND"].isin(active_bands)

        colors  = [SF_BLUE if s else "#C8DFF0" for s in band_df["SELECTED"]]
        opacity = [1.0 if s else 0.5 for s in band_df["SELECTED"]]

        fig_bar = go.Figure()
        for i, row_b in band_df.iterrows():
            fig_bar.add_trace(go.Bar(
                x=[row_b["LABEL"]], y=[row_b["DEMAND_POOL"]],
                marker_color=colors[i], opacity=opacity[i],
                showlegend=False,
                text=[f"{row_b['DEMAND_POOL']:,}명"], textposition="outside",
                textfont=dict(size=11, color=SF_NAVY),
            ))

        fig_bar.update_layout(
            height=280, margin=dict(l=10, r=10, t=20, b=30),
            paper_bgcolor="white", plot_bgcolor="white",
            xaxis=dict(title=None, tickfont=dict(size=11, color=SF_NAVY), showgrid=False),
            yaxis=dict(title="수요풀 (명)", tickfont=dict(size=10, color="#8FA3B8"),
                       gridcolor="#EFF4F9", tickformat=","),
            bargap=0.35,
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("임대료 수요풀 데이터가 없습니다.")

with chart_r:
    forecast_method = str(r["FORECAST_METHOD"]) if r["FORECAST_METHOD"] else "MA_TREND"
    method_label = "Cortex ML Forecast" if forecast_method == "CORTEX" else "이동평균 트렌드 예측"
    st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{SF_DARK_BLUE}; margin-bottom:0.5rem;'>📈 수요 신호 6개월 예측 <span style='font-size:0.72rem; color:#8FA3B8;'>({method_label})</span></div>", unsafe_allow_html=True)

    df_hist = df_signal[(df_signal["GU"] == sel_gu) & (df_signal["DONG"] == sel_dong)].copy()
    df_fore = df_forecast[(df_forecast["GU"] == sel_gu) & (df_forecast["DONG"] == sel_dong)].copy()

    fig_line = go.Figure()

    if not df_hist.empty:
        df_hist = df_hist.sort_values("BASE_YM").tail(12)
        df_hist["YM_LABEL"] = df_hist["BASE_YM"].astype(str).str[:4] + "." + df_hist["BASE_YM"].astype(str).str[4:]
        fig_line.add_trace(go.Scatter(
            x=df_hist["YM_LABEL"], y=df_hist["DEMAND_SCORE"],
            mode="lines+markers", name="실적 (과거 12개월)",
            line=dict(color=SF_DARK_BLUE, width=2.5),
            marker=dict(size=5, color=SF_DARK_BLUE),
        ))

    if not df_fore.empty:
        df_fore = df_fore.sort_values("FORECAST_YM")
        df_fore["YM_LABEL"] = df_fore["FORECAST_YM"].astype(str).str[:4] + "." + df_fore["FORECAST_YM"].astype(str).str[4:]
        lower_vals = df_fore["LOWER_BOUND"].clip(lower=0)
        upper_vals = df_fore["UPPER_BOUND"].clip(upper=100)

        fig_line.add_trace(go.Scatter(
            x=pd.concat([df_fore["YM_LABEL"], df_fore["YM_LABEL"].iloc[::-1]]),
            y=pd.concat([upper_vals, lower_vals.iloc[::-1]]),
            fill="toself", fillcolor="rgba(41,181,232,0.12)",
            line=dict(color="rgba(41,181,232,0)"),
            showlegend=False, hoverinfo="skip",
        ))
        fig_line.add_trace(go.Scatter(
            x=df_fore["YM_LABEL"], y=df_fore["FORECAST_SCORE"],
            mode="lines+markers", name="예측 (6개월)",
            line=dict(color=SF_BLUE, width=2.5, dash="dot"),
            marker=dict(size=7, color=SF_BLUE, symbol="diamond"),
        ))

        first_fore = df_fore["YM_LABEL"].iloc[0]
        fig_line.add_vline(x=first_fore, line_dash="dash", line_color="#C8DFF0", line_width=1.5)
        fig_line.add_annotation(x=first_fore, y=105, text="▶ 예측 시작",
            showarrow=False, font=dict(size=9, color=SF_BLUE))

    fig_line.update_layout(
        height=280, margin=dict(l=10, r=10, t=20, b=30),
        paper_bgcolor="white", plot_bgcolor="white",
        xaxis=dict(title=None, tickfont=dict(size=10, color="#8FA3B8"), showgrid=False, tickangle=-30),
        yaxis=dict(title="수요 스코어", range=[0, 110],
                   tickfont=dict(size=10, color="#8FA3B8"), gridcolor="#EFF4F9"),
        legend=dict(font=dict(size=10), x=0.01, y=0.99,
                    bgcolor="rgba(255,255,255,0.8)", bordercolor="#E2EBF4", borderwidth=1),
    )
    st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})

# ── 입지 세부 분석 ────────────────────────────────────────────────
st.markdown('<div class="section-title">입지 세부 분석</div>', unsafe_allow_html=True)
radar_col, growth_col = st.columns([1, 1], gap="medium")

with radar_col:
    st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{SF_DARK_BLUE}; margin-bottom:0.5rem;'>🎯 입지 점수 구성</div>", unsafe_allow_html=True)

    categories = ["소득수준", "유동인구", "소비력", "임대수요", "임차부담"]
    score_vals = [
        float(r["SCORE_INCOME"])          if pd.notna(r["SCORE_INCOME"])          else 0,
        float(r["SCORE_FLOATING"])        if pd.notna(r["SCORE_FLOATING"])        else 0,
        float(r["SCORE_CONSUMPTION"])     if pd.notna(r["SCORE_CONSUMPTION"])     else 0,
        float(r["LOCATION_DEMAND_SCORE"]) if pd.notna(r["LOCATION_DEMAND_SCORE"]) else 0,
        float(r["SCORE_AFFORDABILITY"])   if pd.notna(r["SCORE_AFFORDABILITY"])   else 0,
    ]
    score_vals_closed = score_vals + [score_vals[0]]
    categories_closed = categories + [categories[0]]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=score_vals_closed, theta=categories_closed,
        fill="toself", fillcolor="rgba(41,181,232,0.18)",
        line=dict(color=SF_BLUE, width=2.5),
        marker=dict(size=7, color=SF_BLUE),
    ))
    fig_radar.update_layout(
        height=260, margin=dict(l=30, r=30, t=20, b=20),
        paper_bgcolor="white",
        polar=dict(
            bgcolor=SF_GRAY,
            radialaxis=dict(visible=True, range=[0,100],
                            tickfont=dict(size=9, color="#8FA3B8"), gridcolor="#E2EBF4"),
            angularaxis=dict(tickfont=dict(size=11, color=SF_NAVY)),
        ),
        showlegend=False,
    )
    st.plotly_chart(fig_radar, use_container_width=True, config={"displayModeBar": False})

with growth_col:
    st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{SF_DARK_BLUE}; margin-bottom:0.5rem;'>📉 6개월 성장률 지표</div>", unsafe_allow_html=True)

    growth_metrics = {
        "유동인구": float(r["VISITING_6M_GROWTH"]) if pd.notna(r["VISITING_6M_GROWTH"]) else 0,
        "소득수준":  float(r["INCOME_6M_GROWTH"])   if pd.notna(r["INCOME_6M_GROWTH"])   else 0,
        "소비지출":  float(r["SALES_6M_GROWTH"])    if pd.notna(r["SALES_6M_GROWTH"])    else 0,
    }
    g_colors = [SF_SUCCESS if v >= 0 else SF_DANGER for v in growth_metrics.values()]

    fig_growth = go.Figure(go.Bar(
        x=list(growth_metrics.keys()), y=list(growth_metrics.values()),
        marker_color=g_colors,
        text=[f"{v:+.1f}%" for v in growth_metrics.values()],
        textposition="outside", textfont=dict(size=13, color=SF_NAVY), width=0.45,
    ))
    fig_growth.add_hline(y=0, line_color="#C8DFF0", line_width=1.5)
    fig_growth.update_layout(
        height=260, margin=dict(l=10, r=10, t=20, b=30),
        paper_bgcolor="white", plot_bgcolor="white",
        xaxis=dict(tickfont=dict(size=12, color=SF_NAVY), showgrid=False),
        yaxis=dict(title="성장률 (%)", tickfont=dict(size=10, color="#8FA3B8"),
                   gridcolor="#EFF4F9", ticksuffix="%"),
        showlegend=False,
    )
    st.plotly_chart(fig_growth, use_container_width=True, config={"displayModeBar": False})

# ── AI 인사이트 ────────────────────────────────────────────────────
st.markdown('<div class="section-title">AI 인사이트</div>', unsafe_allow_html=True)

ai_insight = str(r["AI_INSIGHT"]) if pd.notna(r["AI_INSIGHT"]) else ""
insight_method = str(r["INSIGHT_METHOD"]) if pd.notna(r["INSIGHT_METHOD"]) else "RULE_BASED"
powered_label = "Powered by Snowflake Cortex" if insight_method == "CORTEX_COMPLETE" else "Powered by CoSense Rules Engine"
powered_icon  = "❄️" if insight_method == "CORTEX_COMPLETE" else "🔧"

if ai_insight:
    cleaned = re.sub(r"\d+\.\s*", "", ai_insight).strip()
    sentences = [s.strip() for s in re.split(r"(?<=[。.!?])\s*", cleaned) if len(s.strip()) > 10]
    if len(sentences) == 0:
        sentences = [ai_insight]

    formatted_insight = "<br><br>".join(
        f"<span style='color:{SF_DARK_BLUE}; font-weight:600;'>{'①②③'[min(i,2)]} </span>{s}"
        for i, s in enumerate(sentences[:3])
    )
    st.markdown(f"""
    <div class="insight-box">
      <div class="insight-text">{formatted_insight}</div>
      <div class="powered-by">{powered_icon} {powered_label} &nbsp;|&nbsp; {sel_gu} {sel_dong} 분석 완료</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("AI 인사이트를 불러올 수 없습니다.")

# ── 푸터 ──────────────────────────────────────────────────────────
st.markdown(f"""
<hr class="section-divider" style="margin-top:1.5rem;">
<div style="display:flex; justify-content:space-between; align-items:center; padding:0.4rem 0;">
  <span style="font-size:0.75rem; color:#8FA3B8;">
    ❄️ CoSense Platform &nbsp;·&nbsp; Built on Snowflake &nbsp;·&nbsp; © 2025 CoSense Team
  </span>
  <span style="font-size:0.75rem; color:#8FA3B8;">
    데이터: GranData · DataKnows · SKT Analytics &nbsp;·&nbsp; Powered by Snowflake Cortex
  </span>
</div>
""", unsafe_allow_html=True)
