
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# -------------------------------
# 1. 페이지 설정
# -------------------------------
st.set_page_config(
    page_title="세계 MBTI 탐험",
    page_icon="🌍",
    layout="wide"
)

# -------------------------------
# 2. 제목
# -------------------------------
st.title("🌍 세계 MBTI 탐험")
st.subheader("국가별 MBTI 비율 알아보기 🧩")
st.write("158개 국가의 MBTI 분포를 그래프로 확인해 보세요!")

st.divider()

# -------------------------------
# 3. CSV 파일 불러오기
# -------------------------------
@st.cache_data
def load_data():
    file_path = Path(__file__).parent / "countriesMBTI_16types.csv"

    try:
        data = pd.read_csv(file_path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        data = pd.read_csv(file_path, encoding="cp949")

    return data

try:
    df = load_data()
except FileNotFoundError:
    st.error("CSV 파일을 찾을 수 없습니다.")
    st.info("app.py와 CSV 파일을 같은 폴더에 넣어주세요.")
    st.stop()

# -------------------------------
# 4. MBTI 유형 확인
# -------------------------------
mbti_types = [
    col for col in df.columns
    if col != "Country"
]

countries = sorted(df["Country"].dropna().unique())

# -------------------------------
# 5. 국가 선택
# -------------------------------
st.markdown("### 🗺️ 국가 선택")

default_index = (
    countries.index("South Korea")
    if "South Korea" in countries else 0
)

selected_country = st.selectbox(
    "분석하고 싶은 국가를 선택하세요!",
    countries,
    index=default_index
)

# 선택한 국가 데이터
country_data = df[
    df["Country"] == selected_country
].iloc[0]

# -------------------------------
# 6. MBTI 비율 계산
# -------------------------------
chart_data = pd.DataFrame({
    "MBTI": mbti_types,
    "비율": [
        float(country_data[mbti]) * 100
        for mbti in mbti_types
    ]
})

# 높은 비율부터 정렬
chart_data = chart_data.sort_values(
    by="비율",
    ascending=False
).reset_index(drop=True)

# -------------------------------
# 7. 그래프 색상 설정
# -------------------------------

def hex_to_rgb(color):
    color = color.lstrip("#")
    return tuple(
        int(color[i:i+2], 16)
        for i in (0, 2, 4)
    )

def rgb_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(*rgb)

def blue_gradient(count):
    start = hex_to_rgb("#2563EB")
    end = hex_to_rgb("#DBEAFE")

    colors = []

    for i in range(count):
        ratio = i / max(count - 1, 1)

        rgb = tuple(
            round(
                start[j] +
                (end[j] - start[j]) * ratio
            )
            for j in range(3)
        )

        colors.append(rgb_to_hex(rgb))

    return colors

# 1위 빨간색, 나머지 파란색 그라데이션
colors = ["#EF4444"] + blue_gradient(
    len(chart_data) - 1
)

# -------------------------------
# 8. 1위 MBTI 정보
# -------------------------------
top_mbti = chart_data.iloc[0]

st.divider()
st.markdown("### 🏆 국가별 MBTI 분석 결과")

col1, col2, col3 = st.columns(3)

col1.metric(
    "🌍 선택 국가",
    selected_country
)

col2.metric(
    "🥇 비율 1위 MBTI",
    top_mbti["MBTI"]
)

col3.metric(
    "📊 최고 비율",
    f'{top_mbti["비율"]:.2f}%'
)

# -------------------------------
# 9. 막대그래프 만들기
# -------------------------------
st.divider()

st.markdown(
    f"### 📊 {selected_country}의 MBTI 비율"
)

fig = go.Figure()

fig.add_trace(
    go.Bar(
        x=chart_data["비율"],
        y=chart_data["MBTI"],
        orientation="h",

        marker=dict(
            color=colors
        ),

        text=[
            f"{value:.2f}%"
            for value in chart_data["비율"]
        ],

        textposition="outside",
        cliponaxis=False,

        hovertemplate=
        "<b>%{y}</b><br>" +
        "비율: %{x:.2f}%" +
        "<extra></extra>"
    )
)

fig.update_layout(
    height=650,

    xaxis=dict(
        title="MBTI 비율 (%)",
        showgrid=True,
        rangemode="tozero"
    ),

    yaxis=dict(
        title="MBTI 유형",
        autorange="reversed"
    ),

    showlegend=False,

    margin=dict(
        l=50,
        r=80,
        t=30,
        b=50
    ),

    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",

    font=dict(size=14)
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# -------------------------------
# 10. MBTI 순위표
# -------------------------------
st.divider()

st.markdown("### 🥇 MBTI 순위표")

ranking = chart_data.copy()

ranking.insert(
    0,
    "순위",
    [f"{i}위" for i in range(1, 17)]
)

ranking["비율"] = ranking["비율"].map(
    lambda x: f"{x:.2f}%"
)

st.dataframe(
    ranking,
    use_container_width=True,
    hide_index=True
)

# -------------------------------
# 11. 하단 안내
# -------------------------------
st.divider()

st.caption(
    "🌍 World MBTI Explorer"
)

st.caption(
    "※ 제공된 CSV 데이터 기준이며 "
    "실제 국가 전체 인구의 공식 통계와 다를 수 있습니다."
)
