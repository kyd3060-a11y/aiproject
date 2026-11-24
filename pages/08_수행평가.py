
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# --------------------------------
# 1. 페이지 설정
# --------------------------------
st.set_page_config(
    page_title="나라별 디저트 식감",
    page_icon="🍰",
    layout="wide"
)

st.title("🍰 나라별 디저트 식감")
st.write("원하는 식감을 선택하고 나라별 디저트 데이터를 비교해 보세요.")

# --------------------------------
# 2. CSV 파일 불러오기
# --------------------------------
@st.cache_data
def load_data():
    file_path = Path(__file__).resolve().parent / "globl.csv"

    if not file_path.exists():
        raise FileNotFoundError(
            "globl.csv 파일을 app.py와 같은 폴더에 넣어주세요."
        )

    encodings = ["cp949", "utf-8-sig", "utf-8"]

    for encoding in encodings:
        try:
            data = pd.read_csv(file_path, encoding=encoding)
            return data
        except UnicodeDecodeError:
            continue

    raise ValueError("CSV 파일의 인코딩을 확인해 주세요.")

try:
    df = load_data()
except Exception as e:
    st.error(f"데이터 파일을 불러오지 못했습니다: {e}")
    st.stop()

# --------------------------------
# 3. 데이터 정리
# --------------------------------
required_columns = ["음식 이름", "국가", "설명"]

if not all(col in df.columns for col in required_columns):
    st.error("CSV 파일의 열 이름을 확인해 주세요.")
    st.stop()

df = df.dropna(subset=required_columns).copy()

# 첨부 데이터에서 확인된 디저트
dessert_names = [
    "타이야키",
    "퍼널 케이크",
    "로티 사이마이"
]

dessert_df = df[
    df["음식 이름"].isin(dessert_names)
].copy()

# --------------------------------
# 4. 식감 분류
# --------------------------------
def classify_texture(row):
    name = str(row["음식 이름"])
    description = str(row["설명"])

    if name == "퍼널 케이크" or "바삭" in description:
        return "바삭함"

    elif name == "타이야키":
        if "부드럽" in description or "폭신" in description:
            return "부드러움"
        return "기타"

    elif name == "로티 사이마이":
        return "다양한 식감"

    elif "촉촉" in description:
        return "촉촉함"

    elif "쫀득" in description:
        return "쫀득함"

    return "기타"

dessert_df["식감"] = dessert_df.apply(
    classify_texture,
    axis=1
)

# --------------------------------
# 5. 식감 선택
# --------------------------------
st.divider()

st.subheader("🔍 원하는 디저트 식감을 선택하세요.")

textures = [
    "바삭함",
    "부드러움",
    "다양한 식감"
]

selected_texture = st.selectbox(
    "디저트 식감",
    textures
)

# --------------------------------
# 6. 선택한 식감 데이터 분석
# --------------------------------
selected_df = dessert_df[
    dessert_df["식감"] == selected_texture
].copy()

if selected_df.empty:
    st.warning("선택한 식감에 해당하는 데이터가 없습니다.")
    st.stop()

# 나라별 등장 건수
country_counts = (
    selected_df.groupby("국가")
    .size()
    .reset_index(name="데이터 건수")
)

# 전체 데이터 중 나라별 비중
total = country_counts["데이터 건수"].sum()

country_counts["선호도"] = (
    country_counts["데이터 건수"] / total * 100
).round(1)

# 선호도 순으로 정렬
country_counts = country_counts.sort_values(
    "선호도",
    ascending=False
).reset_index(drop=True)

# 가장 높은 나라
max_index = country_counts["선호도"].idxmax()
max_country = country_counts.loc[max_index, "국가"]
max_value = country_counts.loc[max_index, "선호도"]

# --------------------------------
# 7. 꺾은선 그래프
# --------------------------------
st.subheader("📈 나라별 디저트 식감 분석")

fig = go.Figure()

# 나라 사이의 선 연결
for i in range(len(country_counts) - 1):

    x_values = country_counts["국가"].iloc[i:i+2]
    y_values = country_counts["선호도"].iloc[i:i+2]

    # 최고 선호도 나라에 연결된 선은 빨간색
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

# 데이터 점
marker_colors = [
    "red" if i == max_index else "royalblue"
    for i in range(len(country_counts))
]

fig.add_trace(
    go.Scatter(
        x=country_counts["국가"],
        y=country_counts["선호도"],
        mode="markers+text",
        marker=dict(
            size=13,
            color=marker_colors
        ),
        text=country_counts["선호도"].astype(str) + "%",
        textposition="top center",
        name="선호도",
        hovertemplate=(
            "나라: %{x}<br>"
            "선호도: %{y}%<extra></extra>"
        )
    )
)

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
    height=550,
    hovermode="x unified"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# --------------------------------
# 8. 분석 결과
# --------------------------------
st.divider()

st.subheader("🏆 분석 결과")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "가장 높은 데이터 비중을 가진 나라",
        max_country
    )

with col2:
    st.metric(
        "가장 높은 비중",
        f"{max_value}%"
    )

st.success(
    f"'{selected_texture}' 식감의 디저트 데이터에서 "
    f"{max_country}의 비중이 가장 높습니다."
)

# --------------------------------
# 9. 데이터 표
# --------------------------------
with st.expander("📊 나라별 데이터 자세히 보기"):

    st.dataframe(
        country_counts,
        use_container_width=True,
        hide_index=True
    )

# --------------------------------
# 10. 디저트 정보
# --------------------------------
with st.expander("🍮 해당 식감의 디저트 확인하기"):

    st.dataframe(
        selected_df[
            ["음식 이름", "국가", "설명"]
        ].drop_duplicates(),
        use_container_width=True,
        hide_index=True
    )

# --------------------------------
# 11. 데이터 출처 안내
# --------------------------------
st.caption(
    "데이터 출처: 사용자가 제공한 globl.csv"
)

st.caption(
    "※ 선호도는 실제 소비자 설문조사 점수가 아니라 "
    "선택한 식감의 디저트 데이터 중 국가별 등장 비율입니다."
)

