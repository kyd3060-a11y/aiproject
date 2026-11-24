
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# =====================================
# 1. 페이지 설정
# =====================================
st.set_page_config(
    page_title="나라별 디저트 식감",
    page_icon="🍰",
    layout="wide"
)

st.title("🍰 나라별 디저트 식감")
st.write("원하는 식감을 선택하고 나라별 디저트 데이터를 비교해 보세요!")

# =====================================
# 2. CSV 파일 경로 설정
# =====================================
# 현재 py 파일은 pages 폴더 안에 있고,
# CSV 파일은 상위 폴더에 있음
BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "globl.csv"


# =====================================
# 3. CSV 데이터 불러오기
# =====================================
@st.cache_data
def load_data(file_path):

    encodings = ["cp949", "utf-8-sig", "utf-8"]

    for encoding in encodings:
        try:
            data = pd.read_csv(
                file_path,
                encoding=encoding
            )
            return data

        except UnicodeDecodeError:
            continue

    raise ValueError("CSV 파일의 인코딩을 확인해 주세요.")


if not CSV_PATH.exists():
    st.error(
        f"CSV 파일을 찾을 수 없습니다.\n\n"
        f"찾는 경로: {CSV_PATH}"
    )
    st.stop()

try:
    df = load_data(str(CSV_PATH))

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()


# =====================================
# 4. 데이터 확인 및 정리
# =====================================
required_columns = ["음식 이름", "국가", "설명"]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    st.error(
        f"CSV에 필요한 열이 없습니다: {missing_columns}"
    )
    st.stop()

df = df.dropna(
    subset=["음식 이름", "국가"]
).copy()

# =====================================
# 5. 디저트 데이터 추출
# =====================================
# 첨부 CSV에서 확인한 디저트 음식
dessert_names = [
    "타이야키",
    "퍼널 케이크",
    "로티 사이마이"
]

dessert_df = df[
    df["음식 이름"].isin(dessert_names)
].copy()

if dessert_df.empty:
    st.warning("CSV 파일에서 디저트 데이터를 찾지 못했습니다.")
    st.stop()


# =====================================
# 6. 디저트 식감 분류
# =====================================
texture_mapping = {
    "타이야키": "부드러움",
    "퍼널 케이크": "바삭함",
    "로티 사이마이": "다양한 식감"
}

dessert_df["식감"] = dessert_df["음식 이름"].map(
    texture_mapping
)

# =====================================
# 7. 식감 선택
# =====================================
st.divider()

st.subheader("🔍 원하는 디저트 식감을 선택하세요.")

texture_options = [
    "바삭함",
    "부드러움",
    "다양한 식감"
]

selected_texture = st.selectbox(
    "디저트 식감 선택",
    texture_options
)

# =====================================
# 8. 선택한 식감 데이터 분석
# =====================================
selected_df = dessert_df[
    dessert_df["식감"] == selected_texture
].copy()

# 나라별 전체 디저트 데이터 개수
total_by_country = (
    dessert_df.groupby("국가")
    .size()
    .rename("전체 디저트 수")
)

# 나라별 선택 식감 데이터 개수
selected_by_country = (
    selected_df.groupby("국가")
    .size()
    .rename("선택 식감 수")
)

# 두 데이터 결합
result = pd.concat(
    [total_by_country, selected_by_country],
    axis=1
).fillna(0)

# 데이터 비중 계산
result["선호도"] = (
    result["선택 식감 수"]
    / result["전체 디저트 수"]
    * 100
).round(1)

result = result.reset_index()

# 높은 순으로 정렬
result = result.sort_values(
    "선호도",
    ascending=False
).reset_index(drop=True)

# 최고 선호도 나라
max_index = result["선호도"].idxmax()
max_country = result.loc[max_index, "국가"]
max_value = result.loc[max_index, "선호도"]

# =====================================
# 9. 꺾은선 그래프
# =====================================
st.divider()

st.subheader("📈 나라별 디저트 식감 분석")

fig = go.Figure()

# 나라별 선 연결
for i in range(len(result) - 1):

    x_values = result["국가"].iloc[i:i+2]
    y_values = result["선호도"].iloc[i:i+2]

    # 최고값 국가와 연결되는 선 빨간색
    if i == max_index or i + 1 == max_index:
        line_color = "red"
    else:
        line_color = "royalblue"

    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=y_values,
            mode="lines",
            line=dict(
                color=line_color,
                width=3
            ),
            showlegend=False,
            hoverinfo="skip"
        )
    )

# 데이터 점 표시
marker_colors = [
    "red" if i == max_index else "royalblue"
    for i in range(len(result))
]

fig.add_trace(
    go.Scatter(
        x=result["국가"],
        y=result["선호도"],
        mode="markers+text",
        marker=dict(
            size=13,
            color=marker_colors,
            line=dict(
                width=1,
                color="white"
            )
        ),
        text=result["선호도"].astype(str) + "%",
        textposition="top center",
        name="선호도",
        hovertemplate=(
            "나라: %{x}<br>"
            "선호도: %{y}%<extra></extra>"
        )
    )
)

# 그래프 설정
fig.update_layout(
    title=dict(
        text="나라별 디저트 식감",
        x=0.5,
        font=dict(size=25)
    ),
    xaxis_title="나라",
    yaxis_title="선호도 (%)",
    yaxis=dict(
        range=[0, 110],
        dtick=10,
        showgrid=True
    ),
    xaxis=dict(
        showgrid=True
    ),
    template="plotly_white",
    height=550
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =====================================
# 10. 분석 결과
# =====================================
st.divider()

st.subheader("🏆 분석 결과")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="가장 높은 비중을 가진 나라",
        value=max_country
    )

with col2:
    st.metric(
        label="가장 높은 비중",
        value=f"{max_value}%"
    )

st.success(
    f"'{selected_texture}' 식감의 디저트 데이터에서 "
    f"{max_country}의 비중이 가장 높습니다."
)

# =====================================
# 11. 나라별 데이터 표
# =====================================
with st.expander("📊 나라별 데이터 자세히 보기"):

    st.dataframe(
        result[
            ["국가", "전체 디저트 수",
             "선택 식감 수", "선호도"]
        ].rename(
            columns={"국가": "나라"}
        ),
        use_container_width=True,
        hide_index=True
    )

# =====================================
# 12. 디저트 상세 정보
# =====================================
with st.expander("🍮 선택한 식감의 디저트 확인하기"):

    st.dataframe(
        selected_df[
            ["음식 이름", "국가", "설명"]
        ].drop_duplicates(),
        use_container_width=True,
        hide_index=True
    )

# =====================================
# 13. 데이터 출처
# =====================================
st.caption("데이터 출처: 사용자가 제공한 globl.csv")

st.caption(
    "※ 선호도는 실제 소비자 설문 결과가 아닌 "
    "CSV에 포함된 디저트 데이터의 국가별 비중입니다."
)
