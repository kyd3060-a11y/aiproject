
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

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
    "세 가지 회귀 알고리즘을 이용하여 과거 기온을 분석하고 "
    "미래의 평균기온을 예측합니다."
)

# ==========================================
# 2. CSV 파일 경로 설정
# ==========================================

# 현재 파일은 pages 폴더에 있음
# CSV 파일은 상위 폴더에 있음

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
        "temperature.csv 파일을 찾을 수 없습니다. "
        "pages 폴더의 상위 폴더에 CSV 파일을 넣어주세요."
    )
    st.stop()

# ==========================================
# 3. CSV 데이터 불러오기
# ==========================================

@st.cache_data
def load_data(file_path):

    try:
        df = pd.read_csv(file_path, encoding="cp949")
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding="utf-8-sig")

    required_columns = ["일시", "평균기온(℃)"]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(
                f"CSV 파일에 {col} 열이 없습니다."
            )

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

    month_text = date_parts.str[0].str.title()

    year_text = pd.to_numeric(
        date_parts.str[1],
        errors="coerce"
    )

    df["월"] = month_text.map(month_dict)

    # 2자리 연도를 순서대로 실제 연도로 변환
    # 예: 07 -> 1907, 99 -> 1999,
    #     00 -> 2000, 26 -> 2026

    years = []
    century = 1900
    previous_year = None

    for yy in year_text:

        if pd.isna(yy):
            years.append(np.nan)
            continue

        yy = int(yy)

        if previous_year is not None and yy < previous_year:
            century += 100

        years.append(century + yy)
        previous_year = yy

    df["연도"] = years

    df["평균기온(℃)"] = pd.to_numeric(
        df["평균기온(℃)"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["연도", "월", "평균기온(℃)"]
    )

    df["연도"] = df["연도"].astype(int)
    df["월"] = df["월"].astype(int)

    return df.sort_values(
        ["연도", "월"]
    ).reset_index(drop=True)


try:
    df = load_data(str(csv_path))

except Exception as e:
    st.error(f"데이터 오류: {e}")
    st.stop()

if df.empty:
    st.error("분석할 수 있는 데이터가 없습니다.")
    st.stop()

# ==========================================
# 4. 데이터 정보
# ==========================================

st.success("✅ 기온 데이터 불러오기 완료!")

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
        "예측할 월을 선택하세요.",
        month_names
    )

    selected_month = (
        month_names.index(selected_month_name) + 1
    )

with col2:

    prediction_year = st.number_input(
        "예측할 연도를 입력하세요.",
        min_value=int(df["연도"].max()) + 1,
        max_value=2100,
        value=int(df["연도"].max()) + 1,
        step=1
    )

# ==========================================
# 6. 회귀 알고리즘 선택
# ==========================================

st.subheader("🤖 회귀 알고리즘 선택")

algorithm_options = [
    "선형회귀",
    "다항회귀",
    "랜덤 포레스트 회귀"
]

selected_algorithm = st.selectbox(
    "사용할 예측 알고리즘을 선택하세요.",
    algorithm_options
)

algorithm_descriptions = {
    "선형회귀": "직선을 이용해 기온의 장기적인 변화 추세를 예측합니다.",
    "다항회귀": "2차 곡선을 이용해 기온의 비선형적인 변화 추세를 예측합니다.",
    "랜덤 포레스트 회귀": "여러 의사결정나무의 예측 결과를 평균 내어 기온을 예측합니다."
}

st.info(
    algorithm_descriptions[selected_algorithm]
)

# ==========================================
# 7. 선택한 월의 데이터 추출
# ==========================================

month_df = df[
    df["월"] == selected_month
].copy()

month_df = month_df.sort_values("연도")

if len(month_df) < 3:
    st.error("예측에 필요한 데이터가 부족합니다.")
    st.stop()

x = month_df["연도"].to_numpy().reshape(-1, 1)

y = month_df["평균기온(℃)"].to_numpy()

# ==========================================
# 8. 세 가지 회귀 모델 생성
# ==========================================

models = {

    "선형회귀": LinearRegression(),

    "다항회귀": make_pipeline(
        PolynomialFeatures(degree=2),
        LinearRegression()
    ),

    "랜덤 포레스트 회귀": RandomForestRegressor(
        n_estimators=200,
        max_depth=5,
        min_samples_leaf=2,
        random_state=42
    )
}

# ==========================================
# 9. 모든 모델 학습 및 예측
# ==========================================

future_x = np.array(
    [[prediction_year]]
)

results = {}
model_scores = {}

for name, model in models.items():

    # 과거 데이터 학습
    model.fit(x, y)

    # 미래 기온 예측
    future_prediction = model.predict(
        future_x
    )[0]

    # 과거 데이터에 대한 예측
    fitted_values = model.predict(x)

    # 학습 데이터 결정계수
    score = r2_score(y, fitted_values)

    results[name] = {
        "model": model,
        "prediction": future_prediction,
        "fitted": fitted_values,
        "r2": score
    }

    model_scores[name] = score

# 선택한 모델 결과
selected_result = results[selected_algorithm]

predicted_temp = selected_result["prediction"]

# ==========================================
# 10. 선택한 알고리즘 예측 결과
# ==========================================

st.divider()

st.subheader("🔮 선택한 알고리즘의 예측 결과")

result1, result2, result3 = st.columns(3)

with result1:
    st.metric(
        "선택한 알고리즘",
        selected_algorithm
    )

with result2:
    st.metric(
        "예측 연도",
        f"{prediction_year}년 {selected_month}월"
    )

with result3:
    st.metric(
        "예측 평균기온",
        f"{predicted_temp:.2f} ℃"
    )

# ==========================================
# 11. 그래프 생성
# ==========================================

fig = go.Figure()

# 실제 관측 기온
fig.add_trace(
    go.Scatter(
        x=x.flatten(),
        y=y,
        mode="lines+markers",
        name="실제 평균기온",
        line=dict(
            color="#2878D0",
            width=2
        ),
        marker=dict(size=6)
    )
)

# 선택한 알고리즘의 추세선
line_x = np.linspace(
    x.min(),
    prediction_year,
    300
).reshape(-1, 1)

line_y = selected_result["model"].predict(
    line_x
)

fig.add_trace(
    go.Scatter(
        x=line_x.flatten(),
        y=line_y,
        mode="lines",
        name=f"{selected_algorithm} 추세선",
        line=dict(
            color="red",
            width=3,
            dash="dash"
        )
    )
)

# 미래 예측 지점
fig.add_trace(
    go.Scatter(
        x=[prediction_year],
        y=[predicted_temp],
        mode="markers+text",
        name="미래 예측기온",
        marker=dict(
            color="orange",
            size=18,
            symbol="star",
            line=dict(
                color="black",
                width=1
            )
        ),
        text=[f"{predicted_temp:.2f}℃"],
        textposition="top center"
    )
)

fig.update_layout(
    title=(
        f"{selected_month}월 평균기온 예측 "
        f"({selected_algorithm})"
    ),
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
# 12. 세 가지 알고리즘 예측값 비교
# ==========================================

st.divider()

st.subheader("📊 세 가지 알고리즘 예측 결과 비교")

st.write(
    f"동일한 {selected_month}월 과거 데이터를 사용하여 "
    f"{prediction_year}년의 평균기온을 각각 예측한 결과입니다."
)

comparison_data = []

for name, result in results.items():

    comparison_data.append({
        "회귀 알고리즘": name,
        "예측 평균기온(℃)": round(
            result["prediction"], 2
        ),
        "학습 데이터 R²": round(
            result["r2"], 4
        )
    })

comparison_df = pd.DataFrame(comparison_data)

st.dataframe(
    comparison_df,
    use_container_width=True,
    hide_index=True
)

# 비교 막대그래프
comparison_fig = go.Figure()

comparison_fig.add_trace(
    go.Bar(
        x=comparison_df["회귀 알고리즘"],
        y=comparison_df["예측 평균기온(℃)"],
        text=[
            f"{v:.2f}℃"
            for v in comparison_df["예측 평균기온(℃)"]
        ],
        textposition="outside",
        marker=dict(
            color=["#2878D0", "#E39B38", "#269653"]
        )
    )
)

comparison_fig.update_layout(
    title=f"{prediction_year}년 {selected_month}월 알고리즘별 예측기온 비교",
    xaxis_title="회귀 알고리즘",
    yaxis_title="예측 평균기온 (℃)",
    template="plotly_white",
    height=420,
    showlegend=False
)

st.plotly_chart(
    comparison_fig,
    use_container_width=True
)

# ==========================================
# 13. 알고리즘별 설명
# ==========================================

st.divider()

st.subheader("🧠 회귀 알고리즘 원리와 특징")

with st.expander("① 선형회귀 (Linear Regression)"):

    st.write("""
    선형회귀는 과거 데이터의 관계를 직선으로 나타내어
    미래의 값을 예측하는 알고리즘입니다.

    연도를 X, 평균기온을 Y로 설정하여
    두 변수 사이의 직선 관계를 학습합니다.
    """)

    st.latex(r"Y = aX + b")

    st.write("""
    **특징**

    - 직선 형태로 기온 변화 추세를 표현합니다.
    - 계산과 해석이 간단합니다.
    - 장기적인 상승 또는 하락 경향을 파악하기 좋습니다.
    """)

with st.expander("② 다항회귀 (Polynomial Regression)"):

    st.write("""
    다항회귀는 선형회귀를 확장한 방법으로,
    연도의 제곱과 같은 항을 추가하여 곡선 형태의
    데이터 변화도 학습할 수 있습니다.

    이 프로그램에서는 2차 다항회귀를 사용합니다.
    """)

    st.latex(r"Y = aX^2 + bX + c")

    st.write("""
    **특징**

    - 직선뿐 아니라 곡선 형태의 추세도 표현합니다.
    - 기온의 상승과 하락이 변하는 경향을 학습할 수 있습니다.
    - 차수가 높거나 데이터가 부족하면 과도하게 곡선을 만들 수 있습니다.
    """)

with st.expander("③ 랜덤 포레스트 회귀 (Random Forest Regression)"):

    st.write("""
    랜덤 포레스트 회귀는 여러 개의 의사결정나무를
    만들어 각각 예측한 결과를 평균 내는 알고리즘입니다.

    여러 나무의 결과를 결합하기 때문에
    복잡한 데이터의 관계를 학습할 수 있습니다.
    """)

    st.markdown("""
    **작동 과정**

    1. 과거 기온 데이터를 이용해 여러 의사결정나무를 만듭니다.
    2. 각각의 나무가 기온을 예측합니다.
    3. 각 나무의 예측값을 평균 내어 최종 결과를 계산합니다.
    """)

    st.latex(
        r"\hat{Y} = \frac{1}{N}\sum_{i=1}^{N}\hat{Y}_i"
    )

    st.write("""
    **특징**

    - 복잡하고 비선형적인 데이터 관계를 학습할 수 있습니다.
    - 여러 나무의 예측을 결합합니다.
    - 학습한 연도 범위를 벗어난 미래 예측에서는 새로운 추세를 외삽하지 못하는 한계가 있습니다.
    """)

# ==========================================
# 14. 결정계수 설명
# ==========================================

st.subheader("📐 결정계수(R²)란?")

st.write("""
결정계수는 회귀모델이 학습에 사용된 실제 데이터의
변화를 얼마나 설명하는지 나타내는 지표입니다.

일반적으로 1에 가까울수록 학습 데이터에 대한 설명력이 높습니다.
다만 학습 데이터의 R²만으로 미래 예측의 정확성을 판단할 수는 없습니다.
""")

st.write("**알고리즘별 학습 데이터 결정계수**")

for name, score in model_scores.items():

    st.write(f"**{name}: {score:.4f}**")

    st.progress(
        float(np.clip(score, 0, 1))
    )

# ==========================================
# 15. 그래프 읽는 방법
# ==========================================

st.divider()

st.subheader("📖 그래프 읽는 방법")

st.markdown("""
🔵 **파란색 선과 점**

실제로 관측된 과거 평균기온입니다.

🔴 **빨간색 점선**

사용자가 선택한 회귀 알고리즘이 계산한 추세선입니다.

🟠 **주황색 별**

선택한 알고리즘으로 계산한 미래 예측기온입니다.
""")

# ==========================================
# 16. 주의사항
# ==========================================

st.warning("""
**예측 결과 해석 시 주의사항**

세 가지 알고리즘은 데이터를 학습하는 방식이 서로 다르기 때문에
같은 조건에서도 예측기온이 다르게 나올 수 있습니다.

특히 랜덤 포레스트는 학습된 과거 기온의 범위를 벗어난
미래 연도를 예측할 때 기온의 상승이나 하락 추세를
그대로 연장하지 못할 수 있습니다.

또한 이 프로그램은 과거의 월별 평균기온만 사용하므로
기후변화, 이상기후, 해수면 온도 등의 다양한 요인을
모두 반영하는 실제 기상예보 프로그램은 아닙니다.

R²는 학습 데이터에 대한 설명력이며,
미래 예측의 정확도를 직접 보장하지 않습니다.
""")
