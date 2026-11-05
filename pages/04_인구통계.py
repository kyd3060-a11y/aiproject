
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import os

# --------------------------------------------------
# 1. 페이지 설정
# --------------------------------------------------

st.set_page_config(
    page_title="서울시 연령별 인구 분석",
    page_icon="📊",
    layout="wide"
)

# --------------------------------------------------
# 2. 화면 디자인
# --------------------------------------------------

st.markdown("""
<style>
    .main-title {
        font-size: 32px;
        font-weight: bold;
        color: #D6A900;
        text-align: center;
        margin-bottom: 10px;
    }

    .sub-title {
        font-size: 16px;
        color: #777777;
        text-align: center;
        margin-bottom: 30px;
    }

    div[data-testid="stMetric"] {
        background-color: #FFF9DF;
        border: 1px solid #F2D66D;
        padding: 15px;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="main-title">🏙️ 서울시 연령별 인구 분석</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">자치구 · 성별 · 연도별 인구 통계 분석</div>',
    unsafe_allow_html=True
)

# --------------------------------------------------
# 3. CSV 데이터 불러오기
# --------------------------------------------------

@st.cache_data
def load_data():

    file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "population.csv"
    )

    # CSV 인코딩 처리
    encodings = ["cp949", "euc-kr", "utf-8-sig", "utf-8"]

    df = None

    for encoding in encodings:
        try:
            df = pd.read_csv(
                file_path,
                encoding=encoding
            )
            break
        except UnicodeDecodeError:
            continue

    if df is None:
        raise ValueError("CSV 파일의 인코딩을 확인할 수 없습니다.")

    # 숫자 데이터 쉼표 제거 및 숫자 변환
    for col in df.columns[1:]:
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(",", "", regex=False),
            errors="coerce"
        )

    # 행정구역 이름 추출
    df["지역명"] = (
        df["행정구역"]
        .astype(str)
        .str.extract(r"^\s*(.*?)\s*\(")[0]
    )

    return df


try:
    df = load_data()

except FileNotFoundError:
    st.error(
        "population.csv 파일을 찾을 수 없습니다. "
        "app.py와 CSV 파일의 위치를 확인해주세요."
    )
    st.stop()

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()


# --------------------------------------------------
# 4. 데이터에서 연도 자동 추출
# --------------------------------------------------

years = sorted(
    {
        int(match.group(1))
        for col in df.columns
        if (match := re.match(r"^(\d{4})년_", col))
    }
)

if not years:
    st.error("CSV에서 연도 정보를 찾을 수 없습니다.")
    st.stop()

# --------------------------------------------------
# 5. 선택 메뉴
# --------------------------------------------------

st.markdown("### 🔎 분석 조건 선택")

col1, col2, col3 = st.columns(3)

with col1:
    districts = sorted(
        df["지역명"].dropna().unique().tolist()
    )

    selected_district = st.selectbox(
        "📍 행정구 선택",
        districts,
        index=districts.index("강남구")
        if "강남구" in districts else 0
    )

with col2:
    selected_gender = st.selectbox(
        "👥 성별 선택",
        ["전체", "남성", "여성"]
    )

with col3:
    selected_year = st.selectbox(
        "📅 연도 선택",
        years,
        index=len(years) - 1,
        format_func=lambda x: f"{x}년"
    )

# --------------------------------------------------
# 6. 선택 조건에 맞는 데이터 가져오기
# --------------------------------------------------

gender_code = {
    "전체": "",
    "남성": "남_",
    "여성": "여_"
}

prefix = (
    f"{selected_year}년_"
    f"{gender_code[selected_gender]}거주자_"
)

age_columns = [
    f"{prefix}0~9세",
    f"{prefix}10~19세",
    f"{prefix}20~29세",
    f"{prefix}30~39세",
    f"{prefix}40~49세",
    f"{prefix}50~59세",
    f"{prefix}60~69세",
    f"{prefix}70~79세",
    f"{prefix}80~89세",
    f"{prefix}90~99세",
    f"{prefix}100세 이상"
]

age_labels = [
    "0~9세",
    "10~19세",
    "20~29세",
    "30~39세",
    "40~49세",
    "50~59세",
    "60~69세",
    "70~79세",
    "80~89세",
    "90~99세",
    "100세 이상"
]

# 실제 CSV 열 확인
missing_columns = [
    col for col in age_columns
    if col not in df.columns
]

if missing_columns:
    st.error(
        "선택한 조건에 맞는 연령별 데이터가 없습니다."
    )
    st.stop()

selected_data = df[
    df["지역명"] == selected_district
]

if selected_data.empty:
    st.error("해당 지역의 데이터를 찾을 수 없습니다.")
    st.stop()

selected_data = selected_data.iloc[0]

population = [
    int(selected_data[col])
    if pd.notna(selected_data[col])
    else 0
    for col in age_columns
]

# --------------------------------------------------
# 7. 전체 인구 계산
# --------------------------------------------------

total_population = sum(population)

max_population = max(population)

# --------------------------------------------------
# 8. 주요 정보 표시
# --------------------------------------------------

st.markdown("---")

st.markdown("### 📌 선택한 지역의 인구 현황")

metric1, metric2, metric3 = st.columns(3)

with metric1:
    st.metric(
        "선택 지역",
        selected_district
    )

with metric2:
    st.metric(
        "전체 인구",
        f"{total_population:,}명"
    )

with metric3:
    st.metric(
        "인구가 가장 많은 연령대",
        age_labels[population.index(max_population)]
    )

# --------------------------------------------------
# 9. 꺾은선 그래프 만들기
# --------------------------------------------------

st.markdown("---")

st.markdown("### 📈 연령대별 인구 꺾은선 그래프")

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=age_labels,
        y=population,
        mode="lines+markers",
        name="인구수",

        line=dict(
            color="#FFD700",
            width=4
        ),

        marker=dict(
            color="#FFD700",
            size=10,
            line=dict(
                color="#D6A900",
                width=1.5
            )
        ),

        fill="tozeroy",
        fillcolor="rgba(255, 215, 0, 0.10)",

        customdata=[
            [f"{v:,}명"] for v in population
        ],

        hovertemplate=(
            "<b>%{x}</b><br>"
            "인구수: %{customdata[0]}"
            "<extra></extra>"
        )
    )
)

# --------------------------------------------------
# 10. 그래프 디자인 및 눈금 설정
# --------------------------------------------------

# 세로축 최대값을 100,000명 단위로 올림
y_max = (
    ((max_population // 100000) + 1) * 100000
)

fig.update_layout(
    title=dict(
        text=(
            f"{selected_year}년 {selected_district} "
            f"{selected_gender} 연령별 인구"
        ),
        x=0.5,
        xanchor="center",
        font=dict(
            family="NanumGothic, sans-serif",
            size=21,
            color="#333333"
        )
    ),

    xaxis=dict(
        title="나이",
        type="category",
        categoryorder="array",
        categoryarray=age_labels,
        showgrid=True,
        gridcolor="#E5E5E5",
        gridwidth=1,
        tickangle=0,
        tickfont=dict(
            family="NanumGothic, sans-serif",
            size=11
        ),
        title_font=dict(
            family="NanumGothic, sans-serif"
        )
    ),

    yaxis=dict(
        title="인구수 (명)",
        range=[0, y_max],
        dtick=100000,
        tickformat=",d",
        showgrid=True,
        gridcolor="#D9D9D9",
        gridwidth=1,
        zeroline=True,
        zerolinecolor="#AAAAAA",
        tickfont=dict(
            family="NanumGothic, sans-serif"
        ),
        title_font=dict(
            family="NanumGothic, sans-serif"
        )
    ),

    font=dict(
        family="NanumGothic, sans-serif",
        size=13,
        color="#333333"
    ),

    plot_bgcolor="white",
    paper_bgcolor="white",

    hovermode="x unified",

    height=550,

    margin=dict(
        l=40,
        r=30,
        t=80,
        b=60
    ),

    showlegend=False
)

# 그래프 출력
st.plotly_chart(
    fig,
    use_container_width=True
)

# --------------------------------------------------
# 11. 연령별 상세 데이터
# --------------------------------------------------

with st.expander("📋 연령대별 인구 상세 데이터 보기"):

    result_df = pd.DataFrame({
        "연령대": age_labels,
        "인구수": population
    })

    st.dataframe(
        result_df,
        use_container_width=True,
        hide_index=True
    )

# --------------------------------------------------
# 12. 안내 문구
# --------------------------------------------------

st.markdown("---")

st.caption(
    "📊 자료: 업로드된 서울시 주민등록 인구 통계 CSV"
)

st.caption(
    "※ 현재 CSV에는 2025년 데이터만 포함되어 있습니다."
)

# --------------------------------------------------
# 11. 연령대별 인구가 가장 많은 자치구 TOP 10
# --------------------------------------------------

st.markdown("---")

st.markdown("### 🏆 연령대별 인구가 가장 많은 자치구")

st.write(
    "원하는 연령대를 선택하면 서울시 25개 자치구 중 "
    "해당 연령의 인구가 많은 지역을 순서대로 보여줍니다."
)

# 연령대 선택
rank_age = st.selectbox(
    "🎂 비교할 연령대 선택",
    age_labels,
    index=0,
    key="rank_age"
)

# 선택한 연령대에 해당하는 CSV 열 이름 만들기
rank_column = (
    f"{selected_year}년_"
    f"{gender_code[selected_gender]}"
    f"거주자_{rank_age}"
)

if rank_column not in df.columns:
    st.error("선택한 연령대의 데이터를 찾을 수 없습니다.")

else:

    # 서울특별시 전체 행 제외하고 자치구만 추출
    rank_df = df[
        df["지역명"].notna()
    ].copy()

    # 선택한 연령대 인구 데이터 가져오기
    rank_df["인구수"] = pd.to_numeric(
        rank_df[rank_column],
        errors="coerce"
    )

    # 인구수가 많은 순서대로 정렬
    rank_df = rank_df.sort_values(
        by="인구수",
        ascending=False
    )

    # 상위 10개 자치구
    top10 = rank_df.head(10).copy()

    # 1위 자치구 정보
    if not top10.empty:

        first_district = top10.iloc[0]["지역명"]
        first_population = int(top10.iloc[0]["인구수"])

        st.success(
            f"🥇 {rank_age} {selected_gender} 인구가 "
            f"가장 많은 지역은 {first_district}입니다! "
            f"({first_population:,}명)"
        )

        # 상위 10개 막대그래프
        fig_rank = go.Figure()

        fig_rank.add_trace(
            go.Bar(
                x=top10["인구수"],
                y=top10["지역명"],
                orientation="h",

                marker=dict(
                    color="#FFD700",
                    line=dict(
                        color="#D6A900",
                        width=1
                    )
                ),

                text=[
                    f"{int(v):,}명"
                    for v in top10["인구수"]
                ],

                textposition="outside",

                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "인구수: %{x:,}명"
                    "<extra></extra>"
                )
            )
        )

        fig_rank.update_layout(
            title=dict(
                text=(
                    f"{selected_year}년 "
                    f"{rank_age} "
                    f"{selected_gender} 인구 TOP 10"
                ),
                x=0.5,
                xanchor="center",
                font=dict(
                    family="NanumGothic, sans-serif",
                    size=20
                )
            ),

            xaxis=dict(
                title="인구수 (명)",
                showgrid=True,
                gridcolor="#DDDDDD",
                dtick=100000,
                tickformat=",d"
            ),

            yaxis=dict(
                title="행정구",
                autorange="reversed",
                showgrid=False,
                categoryorder="array",
                categoryarray=top10["지역명"].tolist()
            ),

            font=dict(
                family="NanumGothic, sans-serif",
                size=13
            ),

            plot_bgcolor="white",
            paper_bgcolor="white",

            height=500,

            margin=dict(
                l=70,
                r=100,
                t=80,
                b=60
            ),

            showlegend=False
        )

        st.plotly_chart(
            fig_rank,
            use_container_width=True
        )

        # 상위 10개 데이터 표
        with st.expander("📋 자치구별 인구 순위 상세 보기"):

            display_df = top10[
                ["지역명", "인구수"]
            ].copy()

            display_df.insert(
                0,
                "순위",
                range(1, len(display_df) + 1)
            )

            display_df.columns = [
                "순위",
                "행정구",
                "인구수"
            ]

            display_df["인구수"] = (
                display_df["인구수"]
                .map(lambda x: f"{int(x):,}명")
            )

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
