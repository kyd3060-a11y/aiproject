
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path

# ==========================================
# 1. 페이지 설정
# ==========================================

st.set_page_config(
    page_title="서울 월별 평균기온 예측",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 서울 월별 평균기온 예측")
st.write(
    "과거 서울의 월별 평균기온 데이터를 분석하고 "
    "선형회귀 알고리즘으로 미래 기온을 예측합니다."
)

# ==========================================
# 2. CSV 파일 경로 설정
# ==========================================

# 현재 파일은 pages 폴더에 있으므로
# parent를 사용하여 상위 폴더로 이동

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

possible_paths = [
    PROJECT_DIR / "temperature.csv",
    PROJECT_DIR / "temperature(1).csv"
]

csv_path = next(
    (path for path in possible_paths if path.exists()),
    None
)

if csv_path is None:
    st.error(
        "temperature.csv 파일을 찾을 수 없습니다.\n\n"
        "CSV 파일이 pages 폴더의 상위 폴더에 있는지 확인해주세요."
    )
    st.stop()

# ==========================================
# 3. 데이터 불러오기 및 정리
# ==========================================

@st.cache_data
def load_data(file_path):

    try:
        df = pd.read_csv(file_path, encoding="cp949")
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding="utf-8-sig")

    # 필요한 열 확인
    required_columns = ["일시", "평균기온(℃)"]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"'{col}' 열이 CSV에 없습니다.")

    # 월 이름을 숫자로 변환
    month_dict = {
        "Jan": 1, "Feb": 2, "Mar": 3,
        "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9,
        "Oct": 10, "Nov": 11, "Dec": 12
    }

    date_parts = (
        df["일시"]
        .astype(str)
        .str.strip()
        .str.split("-")
    )

    month_text = date_parts.str[0]
    year_text = pd.to_numeric(
        date_parts.str[1],
        errors="coerce"
    )

    df["월"] = month_text.map(month_dict)

    # CSV의 날짜 형식은 Oct-07 형태
    # 07~99는 1907~1999년
    # 00~26은 2000~2026년으로 변환
    df["연도"] = np.where(
        year_text >= 90,
        1900 + year_text,
        2000 + year_text
    )

    df["평균기온(℃)"] = pd.to_numeric(
        df["평균기온(℃)"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["연도", "월", "평균기온(℃)"]
    )

    df["연도"] = df["연도"].astype(int)
    df["월"] = df["월"].astype(int)

    return df.sort_values(["연도", "월"])


try:
    df = load_data(str(csv_path))

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# ==========================================
# 4. 데이터 정보 표시
# ==========================================

st.success("✅ 기온 데이터 불러오기가 완료되었습니다!")

info1, info2, info3 = st.columns(3)

with info1:
    st.metric("전체 데이터", f"{len(df):,}개")

with info2:
    st.metric("시작 연도", f"{df['연도'].min()}년")

with info3:
    st.metric("마지막 연도", f"{df['연도'].max()}년")

st.divider()

# ==========================================
# 5. 사용자 입력
# ==========================================

st.subheader("📌 예측 조건 선택")

col1, col2 = st.columns(2)

month_names = [
    "1월", "2월", "3월", "4월",
    "5월", "6월", "7월", "8월",
    "9월", "10월", "11월", "12월"
]

with col1:
    selected_month_name = st.selectbox(
        "예측하고 싶은 월을 선택하세요.",
        month_names
    )

    selected_month = month_names.index(
        selected_month_name
    ) + 1

with col2:
    prediction_year = st.number_input(
        "예측하고 싶은 연도를 입력하세요.",
        min_value=int(df["연도"].max()) + 1,
        max_value=2100,
        value=int(df["연도"].max()) + 1,
        step=1
    )

# ==========================================
# 6. 선택한 월의 데이터 추출
# ==========================================

month_df = df[
    df["월"] == selected_month
].copy()

month_df = month_df.sort_values("연도")

if len(month_df) < 2:
    st.error("선택한 월의 데이터가 부족합니다.")
    st.stop()

# ==========================================
# 7. 선형회귀 알고리즘 계산
# ==========================================

# X = 연도
# Y = 평균기온

x = month_df["연도"].to_numpy(dtype=float)
y = month_df["평균기온(℃)"].to_numpy(dtype=float)

# 선형회귀 직선 계산
# Y = aX + b

a, b = np.polyfit(x, y, 1)

# 미래 평균기온 예측
predicted_temp = a * prediction_year + b

# 과거 데이터에 대한 회귀 예측값
predicted_values = a * x + b

# 결정계수 R² 계산
ss_res = np.sum((y - predicted_values) ** 2)
ss_tot = np.sum((y - np.mean(y)) ** 2)

r_squared = (
    1 - ss_res / ss_tot
    if ss_tot != 0 else 0
)

# ==========================================
# 8. 예측 결과 표시
# ==========================================

st.divider()
st.subheader("🔮 평균기온 예측 결과")

result1, result2, result3 = st.columns(3)

with result1:
    st.metric(
        "예측 연도",
        f"{prediction_year}년 {selected_month}월"
    )

with result2:
    st.metric(
        "예측 평균기온",
        f"{predicted_temp:.2f} ℃"
    )

with result3:
    st.metric(
        "결정계수 R²",
        f"{r_squared:.4f}"
    )

# ==========================================
# 9. 그래프 생성
# ==========================================

fig = go.Figure()

# 실제 평균기온
fig.add_trace(
    go.Scatter(
        x=x,
        y=y,
        mode="lines+markers",
        name="실제 평균기온",
        line=dict(
            color="#2878D0",
            width=2
        ),
        marker=dict(size=6),
        hovertemplate=
        "%{x}년<br>실제 기온: %{y:.2f}℃<extra></extra>"
    )
)

# 선형회귀 직선
line_x = np.linspace(
    min(x.min(), prediction_year),
    max(x.max(), prediction_year),
    300
)

line_y = a * line_x + b

fig.add_trace(
    go.Scatter(
        x=line_x,
        y=line_y,
        mode="lines",
        name="선형회귀 추세선",
        line=dict(
            color="red",
            width=3,
            dash="dash"
        ),
        hovertemplate=
        "연도: %{x:.1f}<br>회귀값: %{y:.2f}℃<extra></extra>"
    )
)

# 예측 평균기온
fig.add_trace(
    go.Scatter(
        x=[prediction_year],
        y=[predicted_temp],
        mode="markers+text",
        name="예측 평균기온",
        marker=dict(
            color="orange",
            size=17,
            symbol="star",
            line=dict(
                color="black",
                width=1
            )
        ),
        text=[f"{predicted_temp:.2f}℃"],
        textposition="top center",
        hovertemplate=
        "%{x}년 예측 기온: %{y:.2f}℃<extra></extra>"
    )
)

# 그래프 꾸미기
fig.update_layout(
    title=f"{selected_month}월 연도별 평균기온 및 미래 예측",
    xaxis_title="연도",
    yaxis_title="평균기온 (℃)",
    template="plotly_white",
    height=600,
    hovermode="x unified",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5
    ),
    xaxis=dict(
        showgrid=True,
        dtick=10
    ),
    yaxis=dict(
        showgrid=True
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ==========================================
# 10. 원본 데이터 확인
# ==========================================

with st.expander("📊 선택한 월의 전체 데이터 확인하기"):

    display_df = month_df[
        ["연도", "월", "평균기온(℃)"]
    ].copy()

    display_df.columns = [
        "연도",
        "월",
        "평균기온(℃)"
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

# ==========================================
# 11. 선형회귀 알고리즘 설명
# ==========================================

st.divider()

st.subheader("🧠 선형회귀 알고리즘이란?")

st.write("""
선형회귀는 과거 데이터를 분석하여 변수 사이의 관계를
하나의 직선으로 나타내고, 그 직선을 이용해 미래의 값을
예측하는 머신러닝 알고리즘입니다.

이 프로그램에서는 연도를 독립변수(X)로 사용하고,
월별 평균기온을 종속변수(Y)로 사용합니다.

과거 여러 해의 같은 월 기온을 분석하여
실제 데이터와 가장 가까운 직선을 계산합니다.
""")

st.latex(r"Y = aX + b")

st.markdown("""
**수식의 의미**

- X : 연도
- Y : 예측 평균기온
- a : 기울기 (연도에 따른 기온 변화 정도)
- b : Y절편

선형회귀는 실제 데이터와 직선 사이의 오차 제곱의 합이
가장 작아지도록 직선을 결정합니다.

이 방법을 **최소제곱법**이라고 합니다.
""")

# ==========================================
# 12. 이번 분석의 회귀식
# ==========================================

st.subheader("📈 이번 분석에 적용된 회귀식")

st.latex(
    rf"Y = {a:.4f}X + ({b:.4f})"
)

st.write(f"**기울기:** {a:.4f}")

st.write(f"**결정계수 R²:** {r_squared:.4f}")

st.write(
    f"**{prediction_year}년 {selected_month}월 예측기온:** "
    f"{predicted_temp:.2f}℃"
)

if a > 0:
    st.info(
        f"기울기가 양수({a:.4f})이므로 "
        f"과거 데이터에서는 장기적인 기온 상승 경향이 나타납니다."
    )
elif a < 0:
    st.info(
        f"기울기가 음수({a:.4f})이므로 "
        f"과거 데이터에서는 장기적인 기온 하락 경향이 나타납니다."
    )
else:
    st.info("기울기가 0에 가까워 뚜렷한 변화 경향이 없습니다.")

# ==========================================
# 13. 그래프 읽는 방법
# ==========================================

st.subheader("📖 그래프 읽는 방법")

st.markdown("""
🔵 **파란색 선과 점**

실제로 관측된 과거의 월별 평균기온입니다.

🔴 **빨간색 점선**

선형회귀 알고리즘이 과거 기온 데이터를 분석하여
계산한 가장 적합한 직선입니다.

🟠 **주황색 별**

회귀선을 연장하여 계산한 미래의 예측 평균기온입니다.
""")

# ==========================================
# 14. 주의사항
# ==========================================

st.warning("""
**예측 결과를 해석할 때 주의할 점**

선형회귀는 과거 데이터의 변화 경향을 바탕으로
미래의 평균기온을 예측합니다.

하지만 실제 기온은 기후변화, 이상기후, 자연적인 변동 등
다양한 요인의 영향을 받습니다.

따라서 이 결과는 통계적인 추세를 이용한 예상값이며,
실제 기상예보와는 차이가 있을 수 있습니다.
특히 과거 관측 기간에서 멀리 떨어진 연도일수록
예측의 불확실성이 커질 수 있습니다.
""")
