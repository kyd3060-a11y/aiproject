
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# =====================================
# 1. 페이지 설정
# =====================================
st.set_page_config(
    page_title="세계 MBTI 탐험",
    page_icon="🌍",
    layout="wide"
)

# =====================================
# 2. 제목 및 소개
# =====================================
st.title("🌍 세계 MBTI 탐험")
st.subheader("국가별 MBTI 비율 알아보기 🧩")

st.write(
    "158개 국가의 MBTI 분포를 그래프로 확인해 보세요!"
)

st.divider()

# =====================================
# 3. CSV 파일 경로 설정
# =====================================
# 현재 파일은 pages 폴더 안에 있으므로
# parent.parent를 사용하여 상위 폴더로 이동

BASE_DIR = Path(__file__).resolve().parent.parent

CSV_PATH = BASE_DIR / "countriesMBTI_16types.csv"

# =====================================
# 4. CSV 데이터 불러오기
# =====================================
@st.cache_data
def load_data():

    if not CSV_PATH.exists():

        st.error("❌ CSV 파일을 찾을 수 없습니다.")

        st.write("현재 페이지 위치:")
        st.code(str(Path(__file__).resolve()))

        st.write("CSV를 찾는 경로:")
        st.code(str(CSV_PATH))

        st.write("상위 폴더의 파일 목록:")

        st.code(
            "\n".join(
                file.name for file in BASE_DIR.iterdir()
            )
        )

        st.warning(
            "countriesMBTI_16types.csv 파일이 "
            "app.py와 같은 상위 폴더에 있는지 확인해 주세요."
        )

        st.stop()

    try:
        data = pd.read_csv(
            CSV_PATH,
            encoding="utf-8-sig"
        )

    except UnicodeDecodeError:
        data = pd.read_csv(
            CSV_PATH,
            encoding="cp949"
        )

    return data


df = load_data()

# =====================================
# 5. 데이터 확인
# =====================================
if "Country" not in df.columns:
    st.error("CSV 파일에 Country 열이 없습니다.")
    st.stop()

mbti_types = [
    col for col in df.columns
    if col != "Country"
]

if len(mbti_types) != 16:
    st.error("MBTI 데이터가 16개가 아닙니다.")
    st.stop()

for mbti in mbti_types:
    df[mbti] = pd.to_numeric(
        df[mbti],
        errors="coerce"
    )

countries = sorted(
    df["Country"].dropna().astype(str).unique()
)

if len(countries) == 0:
    st.error("국가 데이터가 없습니다.")
    st.stop()

# =====================================
# 6. 국가 선택
# =====================================
st.markdown("### 🗺️ 국가 선택")

default_index = (
    countries.index("South Korea")
    if "South Korea" in countries
    else 0
)

selected_country = st.selectbox(
    "분석하고 싶은 국가를 선택하세요!",
    countries,
    index=default_index
)

# 선택한 국가 데이터
country_data = df[
    df["Country"].astype(str) == selected_country
].iloc[0]

# =====================================
# 7. MBTI 비율 계산
# =====================================
chart_data = pd.DataFrame({
    "MBTI": mbti_types,
    "비율": [
        country_data[mbti] * 100
        for mbti in mbti_types
    ]
})

chart_data = chart_data.dropna(
    subset=["비율"]
)

# 높은 비율부터 정렬
chart_data = chart_data.sort_values(
    by="비율",
    ascending=False
).reset_index(drop=True)

# =====================================
# 8. 그래프 색상 설정
# =====================================
def hex_to_rgb(color):

    color = color.lstrip("#")

    return tuple(
        int(color[i:i+2], 16)
        for i in (0, 2, 4)
    )


def rgb_to_hex(rgb):

    return "#{:02X}{:02X}{:02X}".format(
        *rgb
    )


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

        colors.append(
            rgb_to_hex(rgb)
        )

    return colors


# 1위는 빨간색
# 나머지는 파란색 그라데이션
colors = (
    ["#EF4444"] +
    blue_gradient(len(chart_data) - 1)
)

# =====================================
# 9. 1위 MBTI 분석
# =====================================
top_mbti = chart_data.iloc[0]

st.divider()

st.markdown("### 🏆 국가별 MBTI 분석 결과")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "🌍 선택 국가",
        selected_country
    )

with col2:
    st.metric(
        "🥇 비율 1위 MBTI",
        top_mbti["MBTI"]
    )

with col3:
    st.metric(
        "📊 최고 비율",
        f'{top_mbti["비율"]:.2f}%'
    )

# =====================================
# 10. MBTI 막대그래프
# =====================================
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

        hovertemplate=(
            "<b>%{y}</b><br>"
            "비율: %{x:.2f}%"
            "<extra></extra>"
        )
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

# =====================================
# 11. MBTI 순위표
# =====================================
st.divider()

st.markdown("### 🥇 MBTI 순위표")

ranking = chart_data.copy()

ranking.insert(
    0,
    "순위",
    [
        f"{i}위"
        for i in range(1, len(ranking) + 1)
    ]
)

ranking["비율"] = ranking["비율"].map(
    lambda x: f"{x:.2f}%"
)

st.dataframe(
    ranking,
    use_container_width=True,
    hide_index=True
)

# =====================================
# 12. 데이터 정보
# =====================================
st.divider()

st.markdown("### 📌 데이터 정보")

info1, info2 = st.columns(2)

info1.metric(
    "🌎 분석 국가 수",
    f"{len(countries)}개"
)

info2.metric(
    "🧩 MBTI 유형 수",
    f"{len(mbti_types)}개"
)

# =====================================
# 13. 하단 안내
# =====================================
st.divider()

st.caption(
    "🌍 World MBTI Explorer"
)

st.caption(
    "※ 제공된 CSV 데이터 기준이며, "
    "실제 국가 전체 인구의 공식 통계와 다를 수 있습니다."
)
