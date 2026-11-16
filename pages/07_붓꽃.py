
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from pathlib import Path
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, cross_val_score

# ---------------------------------
# 1. 페이지 설정
# ---------------------------------
st.set_page_config(
    page_title="붓꽃 품종 예측 AI",
    page_icon="🌸",
    layout="wide"
)

st.title("🌸 AI 붓꽃 품종 예측 프로그램")
st.write(
    "꽃잎의 길이와 너비를 입력하면 "
    "인공지능이 붓꽃의 품종을 예측해 줍니다."
)

st.divider()

# ---------------------------------
# 2. CSV 파일 불러오기
# ---------------------------------
@st.cache_data
def load_data():

    # 현재 파일 위치와 상위 폴더에서 CSV 찾기
    base = Path(__file__).resolve().parent

    paths = [
        base / "iris.csv",
        base.parent / "iris.csv",
        Path.cwd() / "iris.csv",
        Path.cwd().parent / "iris.csv"
    ]

    file_path = next(
        (p for p in paths if p.exists()),
        None
    )

    if file_path is None:
        raise FileNotFoundError(
            "iris.csv 파일을 찾을 수 없습니다."
        )

    # 한글 CSV 인코딩 처리
    for encoding in ["cp949", "utf-8-sig", "utf-8"]:
        try:
            return pd.read_csv(
                file_path,
                encoding=encoding
            )
        except UnicodeDecodeError:
            continue

    raise ValueError("CSV 파일의 인코딩을 확인해 주세요.")


try:
    df = load_data()

except Exception as e:
    st.error(f"데이터 파일 오류: {e}")
    st.info(
        "iris.csv 파일을 프로젝트 최상위 폴더에 넣어 주세요."
    )
    st.stop()


# 필요한 열 확인
required_columns = [
    "꽃잎 길이",
    "꽃잎 너비",
    "품종"
]

if not all(col in df.columns for col in required_columns):
    st.error("CSV 파일의 열 이름이 올바르지 않습니다.")
    st.stop()

# 필요한 데이터만 사용
df = df[required_columns].copy()

df["꽃잎 길이"] = pd.to_numeric(
    df["꽃잎 길이"], errors="coerce"
)

df["꽃잎 너비"] = pd.to_numeric(
    df["꽃잎 너비"], errors="coerce"
)

df = df.dropna()

if df.empty:
    st.error("분석할 데이터가 없습니다.")
    st.stop()

# ---------------------------------
# 3. 학습 데이터와 정답 데이터 설정
# ---------------------------------
X = df[["꽃잎 길이", "꽃잎 너비"]]
y = df["품종"]

# ---------------------------------
# 4. SVM 분류 모델 생성
# ---------------------------------
model = Pipeline([
    ("scaler", StandardScaler()),
    ("svm", SVC(
        kernel="rbf",
        C=1.0,
        gamma="scale"
    ))
])

# 5겹 교차 검증
cv = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42
)

scores = cross_val_score(
    model,
    X,
    y,
    cv=cv,
    scoring="accuracy"
)

# 전체 데이터로 최종 모델 학습
model.fit(X, y)

# ---------------------------------
# 5. 모델 정보 표시
# ---------------------------------
st.subheader("🤖 AI 모델 정보")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("학습 데이터", f"{len(df)}개")

with col2:
    st.metric("품종 종류", f"{y.nunique()}종")

with col3:
    st.metric(
        "5겹 교차 검증 정확도",
        f"{scores.mean() * 100:.2f}%"
    )

st.caption(
    "교차 검증 정확도는 데이터를 5개로 나누어 "
    "반복 평가한 평균 결과입니다."
)

st.divider()

# ---------------------------------
# 6. 사용자 입력
# ---------------------------------
st.subheader("🌱 붓꽃 정보 입력")

st.write(
    "꽃잎의 길이와 너비를 선택해 주세요. "
    "단위는 cm입니다."
)

min_length = float(df["꽃잎 길이"].min())
max_length = float(df["꽃잎 길이"].max())

min_width = float(df["꽃잎 너비"].min())
max_width = float(df["꽃잎 너비"].max())

col1, col2 = st.columns(2)

with col1:
    petal_length = st.slider(
        "🌼 꽃잎 길이 (cm)",
        min_value=min_length,
        max_value=max_length,
        value=4.3,
        step=0.1
    )

with col2:
    petal_width = st.slider(
        "🌼 꽃잎 너비 (cm)",
        min_value=min_width,
        max_value=max_width,
        value=1.3,
        step=0.1
    )

st.caption(
    f"꽃잎 길이: {min_length:.1f} ~ {max_length:.1f}cm"
)

st.caption(
    f"꽃잎 너비: {min_width:.1f} ~ {max_width:.1f}cm"
)

# ---------------------------------
# 7. 품종 예측
# ---------------------------------
input_data = pd.DataFrame(
    [[petal_length, petal_width]],
    columns=["꽃잎 길이", "꽃잎 너비"]
)

prediction = model.predict(input_data)[0]

# 품종 한글 이름
species_korean = {
    "Iris-setosa": "세토사 (Setosa)",
    "Iris-versicolor": "버시컬러 (Versicolor)",
    "Iris-virginica": "버지니카 (Virginica)"
}

st.divider()

st.subheader("🔍 AI 예측 결과")

st.success(
    f"예측된 붓꽃 품종은 "
    f"**{species_korean.get(prediction, prediction)}** 입니다! 🌸"
)

st.write(f"꽃잎 길이: {petal_length:.1f} cm")
st.write(f"꽃잎 너비: {petal_width:.1f} cm")

# ---------------------------------
# 8. 그래프 만들기
# ---------------------------------
st.divider()

st.subheader("📊 꽃잎 크기 그래프")

st.write(
    "가로축은 꽃잎 길이, 세로축은 꽃잎 너비입니다."
)

fig = go.Figure()

# 기존 데이터의 품종별 분포
colors = {
    "Iris-setosa": "#4C9BE8",
    "Iris-versicolor": "#31A879",
    "Iris-virginica": "#D77AC5"
}

for species in sorted(df["품종"].unique()):

    subset = df[df["품종"] == species]

    fig.add_trace(
        go.Scatter(
            x=subset["꽃잎 길이"],
            y=subset["꽃잎 너비"],
            mode="markers",
            name=species_korean.get(species, species),
            marker=dict(
                size=8,
                color=colors.get(species, "#888888"),
                opacity=0.65
            ),
            hovertemplate=(
                "꽃잎 길이: %{x:.1f}cm<br>"
                "꽃잎 너비: %{y:.1f}cm"
                "<extra></extra>"
            )
        )
    )

# 사용자가 입력한 값: 노란색 별
fig.add_trace(
    go.Scatter(
        x=[petal_length],
        y=[petal_width],
        mode="markers",
        name="내가 입력한 값 ⭐",
        marker=dict(
            symbol="star",
            size=24,
            color="yellow",
            line=dict(
                color="black",
                width=1.5
            )
        ),
        hovertemplate=(
            "내가 입력한 값<br>"
            "꽃잎 길이: %{x:.1f}cm<br>"
            "꽃잎 너비: %{y:.1f}cm"
            "<extra></extra>"
        )
    )
)

fig.update_layout(
    xaxis_title="꽃잎 길이 (cm)",
    yaxis_title="꽃잎 너비 (cm)",
    template="plotly_white",
    height=550,
    legend_title="붓꽃 품종",
    xaxis=dict(
        range=[min_length - 0.2, max_length + 0.2],
        dtick=1
    ),
    yaxis=dict(
        range=[min_width - 0.1, max_width + 0.1],
        dtick=0.5
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.info(
    "⭐ 노란색 별은 사용자가 입력한 꽃잎의 크기를 나타냅니다. "
    "다른 점들은 기존 붓꽃 데이터의 측정값입니다."
)

# ---------------------------------
# 9. 데이터 정보
# ---------------------------------
with st.expander("📚 학습에 사용된 데이터 확인"):

    st.write("전체 데이터")
    st.dataframe(df, use_container_width=True)

    st.write("품종별 데이터 개수")
    st.bar_chart(df["품종"].value_counts())

st.caption(
    "Iris 데이터셋을 활용한 머신러닝 품종 분류 프로그램"
)
