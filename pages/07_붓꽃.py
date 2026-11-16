
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from pathlib import Path

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score


# =========================================
# 1. 페이지 설정
# =========================================

st.set_page_config(
    page_title="AI 붓꽃 품종 예측",
    page_icon="🌸",
    layout="wide"
)

st.title("🌸 AI 붓꽃 품종 예측 프로그램")

st.write(
    "꽃잎 또는 꽃받침의 길이와 너비를 입력하면 "
    "3가지 인공지능 알고리즘이 붓꽃 품종을 예측합니다."
)

st.divider()


# =========================================
# 2. CSV 데이터 불러오기
# =========================================

@st.cache_data
def load_data():

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

    for encoding in ["cp949", "utf-8-sig", "utf-8"]:

        try:
            return pd.read_csv(
                file_path,
                encoding=encoding
            )

        except UnicodeDecodeError:
            continue

    raise ValueError(
        "CSV 파일의 인코딩을 확인해 주세요."
    )


try:

    df = load_data()

except Exception as e:

    st.error(f"데이터 불러오기 오류: {e}")
    st.stop()


# =========================================
# 3. 데이터 확인 및 전처리
# =========================================

required_columns = [
    "꽃받침 길이",
    "꽃받침 너비",
    "꽃잎 길이",
    "꽃잎 너비",
    "품종"
]

if not all(
    col in df.columns for col in required_columns
):

    st.error(
        "CSV 파일의 열 이름이 올바르지 않습니다."
    )
    st.stop()


for col in required_columns[:4]:

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )


df = df.dropna(
    subset=required_columns
).copy()


if df.empty:

    st.error("분석할 데이터가 없습니다.")
    st.stop()


if df["품종"].nunique() < 2:

    st.error("분류할 품종이 2개 이상 필요합니다.")
    st.stop()


if df["품종"].value_counts().min() < 5:

    st.error(
        "5겹 교차 검증을 위해 각 품종에 최소 5개의 데이터가 필요합니다."
    )
    st.stop()


# 품종 한글 이름
species_korean = {
    "Iris-setosa": "세토사 (Setosa)",
    "Iris-versicolor": "버시컬러 (Versicolor)",
    "Iris-virginica": "버지니카 (Virginica)"
}


# 품종별 그래프 색상
species_colors = {
    "Iris-setosa": "#4C9BE8",
    "Iris-versicolor": "#31A879",
    "Iris-virginica": "#D77AC5"
}


# =========================================
# 4. 데이터 기본 정보
# =========================================

st.subheader("📚 데이터 정보")

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "전체 데이터",
        f"{len(df)}개"
    )

with col2:

    st.metric(
        "붓꽃 품종",
        f"{df['품종'].nunique()}종"
    )

with col3:

    st.metric(
        "측정 속성",
        "4개"
    )


with st.expander("학습 데이터 확인하기"):

    st.dataframe(
        df,
        use_container_width=True
    )


st.divider()


# =========================================
# 5. 머신러닝 알고리즘 3가지
# =========================================

def create_models():

    models = {

        "SVM": Pipeline([
            ("scaler", StandardScaler()),
            ("model", SVC(
                kernel="rbf",
                C=1.0,
                gamma="scale"
            ))
        ]),

        "랜덤 포레스트": RandomForestClassifier(
            n_estimators=100,
            random_state=42
        ),

        "KNN": Pipeline([
            ("scaler", StandardScaler()),
            ("model", KNeighborsClassifier(
                n_neighbors=5
            ))
        ])

    }

    return models


# =========================================
# 6. 알고리즘 작동 원리
# =========================================

algorithm_info = {

    "SVM": {
        "title": "서포트 벡터 머신 (SVM)",
        "description": """
SVM은 여러 품종의 데이터 사이에서
가장 적절한 분류 경계선을 찾는 알고리즘입니다.

새로운 꽃의 측정값이 어느 영역에 위치하는지
판단하여 품종을 예측합니다.

이번 프로그램은 RBF 커널을 사용하여
복잡한 형태의 데이터도 구분할 수 있습니다.
"""
    },

    "랜덤 포레스트": {
        "title": "랜덤 포레스트 (Random Forest)",
        "description": """
랜덤 포레스트는 여러 개의 결정 트리를 만들어
각각의 결과를 종합하는 알고리즘입니다.

각 결정 트리가 꽃의 측정값을 분석하고
품종을 예측합니다.

마지막에는 여러 트리의 결과를 모아
다수결 방식으로 최종 품종을 결정합니다.
"""
    },

    "KNN": {
        "title": "K-최근접 이웃 (KNN)",
        "description": """
KNN은 새로운 데이터와 기존 데이터 사이의
거리를 계산하는 알고리즘입니다.

가장 가까운 5개의 데이터를 찾은 뒤
그 데이터에서 가장 많이 나타나는 품종을
새로운 꽃의 품종으로 예측합니다.
"""
    }

}


# =========================================
# 7. 예측 프로그램 함수
# =========================================

def prediction_tab(
    feature1,
    feature2,
    tab_key,
    title,
    description
):

    st.subheader(title)

    st.write(description)

    # -------------------------------------
    # 입력값 범위 설정
    # -------------------------------------

    min1 = float(df[feature1].min())
    max1 = float(df[feature1].max())

    min2 = float(df[feature2].min())
    max2 = float(df[feature2].max())

    # -------------------------------------
    # 사용자 입력
    # -------------------------------------

    st.markdown("### 🌱 꽃의 크기 입력")

    col1, col2 = st.columns(2)

    with col1:

        value1 = st.slider(
            f"{feature1} (cm)",
            min_value=min1,
            max_value=max1,
            value=round((min1 + max1) / 2, 1),
            step=0.1,
            key=f"{tab_key}_input1"
        )

    with col2:

        value2 = st.slider(
            f"{feature2} (cm)",
            min_value=min2,
            max_value=max2,
            value=round((min2 + max2) / 2, 1),
            step=0.1,
            key=f"{tab_key}_input2"
        )

    st.caption(
        f"{feature1} 입력 범위: "
        f"{min1:.1f} ~ {max1:.1f} cm"
    )

    st.caption(
        f"{feature2} 입력 범위: "
        f"{min2:.1f} ~ {max2:.1f} cm"
    )

    # -------------------------------------
    # 학습 데이터 준비
    # -------------------------------------

    X = df[[feature1, feature2]]
    y = df["품종"]

    input_data = pd.DataFrame(
        [[value1, value2]],
        columns=[feature1, feature2]
    )

    # -------------------------------------
    # 교차 검증 설정
    # -------------------------------------

    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42
    )

    models = create_models()

    results = {}
    scores = {}

    # -------------------------------------
    # 세 가지 알고리즘 학습 및 예측
    # -------------------------------------

    for name, model in models.items():

        cv_scores = cross_val_score(
            model,
            X,
            y,
            cv=cv,
            scoring="accuracy"
        )

        scores[name] = (
            cv_scores.mean() * 100
        )

        model.fit(X, y)

        prediction = model.predict(
            input_data
        )[0]

        results[name] = prediction

    # =====================================
    # 8. 알고리즘별 예측 결과
    # =====================================

    st.divider()

    st.markdown("### 🔍 알고리즘별 품종 예측")

    cols = st.columns(3)

    for i, (name, prediction) in enumerate(
        results.items()
    ):

        with cols[i]:

            st.markdown(f"**{name}**")

            st.success(
                species_korean.get(
                    prediction,
                    prediction
                )
            )

            st.metric(
                "교차 검증 정확도",
                f"{scores[name]:.2f}%"
            )

    # =====================================
    # 9. 예측 결과 비교 표
    # =====================================

    st.divider()

    st.markdown("### 🏆 세 알고리즘 결과 비교")

    comparison_df = pd.DataFrame({

        "알고리즘": list(results.keys()),

        "예측 품종": [
            species_korean.get(v, v)
            for v in results.values()
        ],

        "교차 검증 정확도": [
            f"{scores[k]:.2f}%"
            for k in results.keys()
        ]

    })

    st.dataframe(
        comparison_df,
        use_container_width=True,
        hide_index=True
    )

    # =====================================
    # 10. 품종별 투표 결과
    # =====================================

    st.markdown("### 📊 품종별 예측 횟수")

    vote_counts = pd.Series(
        list(results.values())
    ).value_counts()

    all_species = sorted(y.unique())

    vote_data = pd.DataFrame({

        "품종": [
            species_korean.get(s, s)
            for s in all_species
        ],

        "예측 횟수": [
            int(vote_counts.get(s, 0))
            for s in all_species
        ]

    })

    fig_vote = go.Figure()

    fig_vote.add_trace(
        go.Bar(
            x=vote_data["품종"],
            y=vote_data["예측 횟수"],
            text=vote_data["예측 횟수"],
            textposition="outside",
            marker_color="#4C9BE8"
        )
    )

    fig_vote.update_layout(
        template="plotly_white",
        height=350,
        xaxis_title="붓꽃 품종",
        yaxis_title="예측 횟수",
        yaxis=dict(
            range=[0, 3.8],
            dtick=1
        )
    )

    st.plotly_chart(
        fig_vote,
        use_container_width=True,
        key=f"{tab_key}_vote_chart"
    )

    # -------------------------------------
    # 다수결 최종 결과
    # -------------------------------------

    max_votes = int(vote_counts.max())

    winners = vote_counts[
        vote_counts == max_votes
    ].index.tolist()

    st.markdown("### 🥇 최종 예측 결과")

    if len(winners) == 1:

        winner = winners[0]

        st.success(
            f"다수결 결과: "
            f"{species_korean.get(winner, winner)} "
            f"({max_votes}/3표)"
        )

        if max_votes == 3:

            st.write(
                "🎉 세 알고리즘 모두 같은 품종을 예측했습니다!"
            )

        else:

            st.write(
                "세 알고리즘 중 두 개 이상이 "
                "같은 품종을 예측했습니다."
            )

    else:

        st.warning(
            "세 알고리즘의 예측이 모두 달라 "
            "다수결로 하나의 품종을 결정할 수 없습니다."
        )

    # =====================================
    # 11. 정확도 비교 그래프
    # =====================================

    st.divider()

    st.markdown("### 📈 알고리즘 정확도 비교")

    accuracy_df = pd.DataFrame({

        "알고리즘": list(scores.keys()),

        "정확도": list(scores.values())

    })

    fig_accuracy = go.Figure()

    fig_accuracy.add_trace(
        go.Bar(
            x=accuracy_df["알고리즘"],
            y=accuracy_df["정확도"],
            text=[
                f"{v:.2f}%"
                for v in accuracy_df["정확도"]
            ],
            textposition="outside",
            marker_color="#31A879"
        )
    )

    fig_accuracy.update_layout(
        template="plotly_white",
        height=380,
        yaxis_title="정확도 (%)",
        xaxis_title="알고리즘",
        yaxis=dict(
            range=[0, 110],
            dticks=20
        )
    )

    st.plotly_chart(
        fig_accuracy,
        use_container_width=True,
        key=f"{tab_key}_accuracy_chart"
    )

    st.caption(
        "정확도는 5겹 교차 검증의 평균값입니다. "
        "새로운 꽃에 대한 예측 결과와는 다른 지표입니다."
    )

    # =====================================
    # 12. 산점도
    # =====================================

    st.divider()

    st.markdown("### 📊 꽃의 크기 산점도")

    st.write(
        "가로축은 측정한 첫 번째 속성, "
        "세로축은 두 번째 속성입니다."
    )

    fig = go.Figure()

    # 기존 붓꽃 데이터
    for species in sorted(df["품종"].unique()):

        subset = df[
            df["품종"] == species
        ]

        fig.add_trace(
            go.Scatter(

                x=subset[feature1],

                y=subset[feature2],

                mode="markers",

                name=species_korean.get(
                    species,
                    species
                ),

                marker=dict(
                    size=8,
                    color=species_colors.get(
                        species,
                        "#888888"
                    ),
                    opacity=0.65
                ),

                hovertemplate=(
                    f"{feature1}: %{{x:.1f}}cm<br>"
                    f"{feature2}: %{{y:.1f}}cm"
                    "<extra></extra>"
                )

            )
        )

    # 사용자가 입력한 위치
    fig.add_trace(
        go.Scatter(

            x=[value1],

            y=[value2],

            mode="markers",

            name="사용자 입력 ⭐",

            marker=dict(
                symbol="star",
                size=25,
                color="yellow",
                line=dict(
                    color="black",
                    width=1.5
                )
            ),

            hovertemplate=(
                "사용자 입력<br>"
                f"{feature1}: %{{x:.1f}}cm<br>"
                f"{feature2}: %{{y:.1f}}cm"
                "<extra></extra>"
            )

        )
    )

    fig.update_layout(

        template="plotly_white",

        height=550,

        xaxis_title=f"{feature1} (cm)",

        yaxis_title=f"{feature2} (cm)",

        legend_title="붓꽃 품종",

        xaxis=dict(
            range=[min1 - 0.2, max1 + 0.2]
        ),

        yaxis=dict(
            range=[min2 - 0.2, max2 + 0.2]
        )

    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=f"{tab_key}_scatter"
    )

    st.info(
        "⭐ 노란색 별은 사용자가 입력한 값입니다. "
        "다른 점들은 기존 붓꽃 데이터입니다."
    )

    # =====================================
    # 13. 알고리즘 작동 원리
    # =====================================

    st.divider()

    st.markdown("### 🧠 알고리즘별 작동 원리")

    st.write(
        "이번 품종 예측에 사용한 세 가지 "
        "분류 알고리즘의 작동 방식을 알아봅시다."
    )

    for name, info in algorithm_info.items():

        with st.expander(
            f"📚 {info['title']} 알아보기"
        ):

            st.write(
                info["description"]
            )

            st.caption(
                f"이번 측정 방식의 교차 검증 정확도: "
                f"{scores[name]:.2f}%"
            )

    # =====================================
    # 14. 입력값 확인
    # =====================================

    with st.expander("입력한 꽃의 측정값 확인"):

        st.dataframe(
            input_data,
            use_container_width=True
        )


# =========================================
# 15. 두 가지 예측 탭
# =========================================

tab1, tab2 = st.tabs([

    "🌼 꽃잎으로 예측하기",

    "🌿 꽃받침으로 예측하기"

])


# 첫 번째 탭
with tab1:

    prediction_tab(

        feature1="꽃잎 길이",

        feature2="꽃잎 너비",

        tab_key="petal",

        title="🌼 꽃잎 크기로 품종 예측",

        description=(
            "꽃잎 길이와 꽃잎 너비를 입력하여 "
            "붓꽃의 품종을 예측합니다."
        )

    )


# 두 번째 탭
with tab2:

    prediction_tab(

        feature1="꽃받침 길이",

        feature2="꽃받침 너비",

        tab_key="sepal",

        title="🌿 꽃받침 크기로 품종 예측",

        description=(
            "꽃받침 길이와 꽃받침 너비를 입력하여 "
            "붓꽃의 품종을 예측합니다."
        )

    )


# =========================================
# 16. 프로그램 하단 안내
# =========================================

st.divider()

st.markdown("### 💡 프로그램 안내")

st.write(
    """
    - 사용 데이터: Iris 붓꽃 데이터셋
    - 학습 데이터: CSV 파일의 전체 데이터
    - 분류 알고리즘: SVM, 랜덤 포레스트, KNN
    - 검증 방식: 5겹 교차 검증
    - 최종 비교: 세 알고리즘의 예측 결과 및 다수결
    """
)

st.caption(
    "Iris 데이터셋을 활용한 머신러닝 분류 분석 프로그램"
)
