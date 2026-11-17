
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from pathlib import Path

from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier


# --------------------------------------------------
# 기본 페이지 설정
# --------------------------------------------------

st.set_page_config(
    page_title="붓꽃 품종 예측",
    page_icon="🌸",
    layout="wide"
)

st.title("🌸 붓꽃 품종 예측 프로그램")
st.write(
    "붓꽃의 꽃잎 또는 꽃받침의 길이와 너비를 입력하면 "
    "3가지 인공지능 알고리즘이 품종을 예측합니다."
)


# --------------------------------------------------
# 데이터 불러오기
# --------------------------------------------------

@st.cache_data
def load_data():

    current_dir = Path(__file__).resolve().parent

    possible_paths = [
        current_dir.parent / "iris.csv",
        current_dir / "iris.csv",
        Path.cwd() / "iris.csv"
    ]

    file_path = None

    for path in possible_paths:
        if path.exists():
            file_path = path
            break

    if file_path is None:
        st.error(
            "iris.csv 파일을 찾을 수 없습니다. "
            "프로젝트 최상위 폴더에 iris.csv 파일을 넣어주세요."
        )
        st.stop()

    data = None

    for encoding in ["cp949", "utf-8-sig", "utf-8"]:
        try:
            data = pd.read_csv(file_path, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue

    if data is None:
        st.error("CSV 파일의 인코딩을 확인해 주세요.")
        st.stop()

    required_columns = [
        "꽃받침 길이",
        "꽃받침 너비",
        "꽃잎 길이",
        "꽃잎 너비",
        "품종"
    ]

    missing_columns = [
        col for col in required_columns
        if col not in data.columns
    ]

    if missing_columns:
        st.error(
            f"CSV 파일에 필요한 열이 없습니다: {missing_columns}"
        )
        st.stop()

    for col in required_columns[:4]:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data = data.dropna(subset=required_columns).copy()

    if data["품종"].nunique() < 2:
        st.error("예측하려면 두 종류 이상의 품종 데이터가 필요합니다.")
        st.stop()

    if data["품종"].value_counts().min() < 5:
        st.error("각 품종의 데이터가 최소 5개 이상 있어야 합니다.")
        st.stop()

    return data


df = load_data()


# --------------------------------------------------
# 품종 이름 및 색상
# --------------------------------------------------

species_korean = {
    "Iris-setosa": "세토사",
    "Iris-versicolor": "버시컬러",
    "Iris-virginica": "버지니카"
}

def korean_name(name):
    return species_korean.get(str(name), str(name))


species_list = sorted(df["품종"].unique())

color_map = {
    species_list[0]: "#3498DB",
    species_list[1]: "#2ECC71",
    species_list[2]: "#E74C3C"
}

# 데이터가 3종류보다 많을 경우 기본 색상 추가
extra_colors = [
    "#9B59B6",
    "#F39C12",
    "#1ABC9C",
    "#34495E"
]

for i, species in enumerate(species_list[3:]):
    color_map[species] = extra_colors[i % len(extra_colors)]


# --------------------------------------------------
# 알고리즘 만들기
# --------------------------------------------------

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


algorithm_info = {
    "SVM": {
        "title": "① SVM (서포트 벡터 머신)",
        "description": """
SVM은 데이터를 가장 잘 구분할 수 있는 경계선을 찾는 알고리즘입니다.

- 특징: 품종 사이의 경계를 찾아 분류합니다.
- 장점: 데이터의 특징이 복잡해도 분류할 수 있습니다.
- 활용: 꽃의 길이와 너비처럼 여러 수치로 품종을 구분할 때 사용할 수 있습니다.
"""
    },

    "랜덤 포레스트": {
        "title": "② 랜덤 포레스트",
        "description": """
랜덤 포레스트는 여러 개의 결정 트리를 만들어 결과를 종합하는 알고리즘입니다.

- 특징: 여러 결정 트리의 예측 결과를 모읍니다.
- 장점: 여러 기준을 활용해 안정적으로 분류할 수 있습니다.
- 활용: 꽃의 여러 측정값을 바탕으로 품종을 구분할 때 사용할 수 있습니다.
"""
    },

    "KNN": {
        "title": "③ KNN (최근접 이웃)",
        "description": """
KNN은 새로운 데이터와 가까운 기존 데이터들을 찾아 품종을 예측하는 알고리즘입니다.

- 특징: 가까운 데이터 5개의 품종을 참고합니다.
- 장점: 원리를 이해하기 쉽고 직관적입니다.
- 활용: 새로운 꽃의 측정값과 기존 꽃의 측정값을 비교할 때 사용할 수 있습니다.
"""
    }
}


# --------------------------------------------------
# 예측 탭 함수
# --------------------------------------------------

def prediction_tab(feature1, feature2, tab_key, title, description):

    st.header(title)
    st.write(description)

    st.subheader("🌱 붓꽃 측정값 입력하기")

    col1, col2 = st.columns(2)

    min1 = float(df[feature1].min())
    max1 = float(df[feature1].max())

    min2 = float(df[feature2].min())
    max2 = float(df[feature2].max())

    with col1:
        value1 = st.slider(
            feature1,
            min_value=min1,
            max_value=max1,
            value=float(df[feature1].median()),
            step=0.1,
            key=f"{tab_key}_value1"
        )

    with col2:
        value2 = st.slider(
            feature2,
            min_value=min2,
            max_value=max2,
            value=float(df[feature2].median()),
            step=0.1,
            key=f"{tab_key}_value2"
        )

    st.caption(
        f"{feature1}: {min1} ~ {max1} / "
        f"{feature2}: {min2} ~ {max2}"
    )

    input_data = pd.DataFrame(
        [[value1, value2]],
        columns=[feature1, feature2]
    )

    X = df[[feature1, feature2]]
    y = df["품종"]

    models = create_models()

    # --------------------------------------------------
    # 3가지 알고리즘 예측 및 정확도 계산
    # --------------------------------------------------

    predictions = {}
    accuracy_results = {}

    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42
    )

    for name, model in models.items():

        scores = cross_val_score(
            model,
            X,
            y,
            cv=cv,
            scoring="accuracy"
        )

        accuracy_results[name] = scores.mean() * 100

        model.fit(X, y)

        prediction = model.predict(input_data)[0]

        predictions[name] = prediction

    # --------------------------------------------------
    # 예측 결과 카드
    # --------------------------------------------------

    st.divider()
    st.subheader("🔍 알고리즘별 예측 결과")

    result_cols = st.columns(3)

    for i, (name, prediction) in enumerate(predictions.items()):

        with result_cols[i]:
            st.metric(
                label=name,
                value=korean_name(prediction),
                delta=f"정확도 {accuracy_results[name]:.1f}%"
            )

    # --------------------------------------------------
    # 예측 결과 비교 표
    # --------------------------------------------------

    st.divider()
    st.subheader("📊 세 가지 알고리즘 결과 비교")

    comparison_df = pd.DataFrame({
        "알고리즘": list(predictions.keys()),
        "예측 품종": [
            korean_name(pred)
            for pred in predictions.values()
        ],
        "교차 검증 정확도": [
            f"{accuracy_results[name]:.2f}%"
            for name in predictions.keys()
        ]
    })

    st.dataframe(
        comparison_df,
        use_container_width=True,
        hide_index=True
    )

    # --------------------------------------------------
    # 다수결 결과
    # --------------------------------------------------

    st.divider()
    st.subheader("🏆 알고리즘 다수결 결과")

    vote_counts = pd.Series(
        list(predictions.values())
    ).value_counts()

    max_votes = vote_counts.max()
    winners = vote_counts[vote_counts == max_votes].index.tolist()

    vote_data = []

    for species in species_list:
        vote_data.append({
            "품종": korean_name(species),
            "투표 수": int(vote_counts.get(species, 0))
        })

    vote_df = pd.DataFrame(vote_data)

    fig_vote = px.bar(
        vote_df,
        x="품종",
        y="투표 수",
        text="투표 수",
        title="알고리즘별 품종 투표 결과"
    )

    fig_vote.update_layout(
        template="plotly_white",
        height=350,
        xaxis_title="붓꽃 품종",
        yaxis_title="투표 수"
    )

    st.plotly_chart(
        fig_vote,
        use_container_width=True
    )

    if len(winners) == 1:
        st.success(
            f"세 알고리즘의 다수결 결과는 "
            f"**{korean_name(winners[0])}**입니다. "
            f"총 {max_votes}표를 받았습니다."
        )
    else:
        winner_names = ", ".join(
            korean_name(name) for name in winners
        )

        st.info(
            f"동률입니다. 공동 결과: {winner_names}"
        )

    # --------------------------------------------------
    # 정확도 비교 그래프
    # --------------------------------------------------

    st.divider()
    st.subheader("📈 알고리즘별 교차 검증 정확도")

    accuracy_df = pd.DataFrame({
        "알고리즘": list(accuracy_results.keys()),
        "정확도": list(accuracy_results.values())
    })

    fig_accuracy = px.bar(
        accuracy_df,
        x="알고리즘",
        y="정확도",
        text=accuracy_df["정확도"].map(
            lambda x: f"{x:.1f}%"
        ),
        title="알고리즘별 정확도 비교"
    )

    # Plotly에서 호환성이 높은 방식으로 레이아웃 설정
    fig_accuracy.update_layout(
        template="plotly_white",
        height=400,
        margin=dict(l=20, r=20, t=60, b=20),
        showlegend=False
    )

    fig_accuracy.update_xaxes(
        title_text="알고리즘"
    )

    fig_accuracy.update_yaxes(
        title_text="정확도 (%)",
        range=[0, 105]
    )

    fig_accuracy.update_traces(
        textposition="outside"
    )

    st.plotly_chart(
        fig_accuracy,
        use_container_width=True
    )

    st.caption(
        "정확도는 5개 구간으로 나누어 검증한 결과의 평균입니다. "
        "새로운 꽃 한 송이에 대한 예측 결과와는 다른 값입니다."
    )

    # --------------------------------------------------
    # 산점도
    # --------------------------------------------------

    st.divider()
    st.subheader("🌼 붓꽃 데이터 분포 그래프")

    fig_scatter = go.Figure()

    for species in species_list:

        species_data = df[df["품종"] == species]

        fig_scatter.add_trace(
            go.Scatter(
                x=species_data[feature1],
                y=species_data[feature2],
                mode="markers",
                name=korean_name(species),
                marker=dict(
                    size=9,
                    color=color_map[species],
                    opacity=0.7
                )
            )
        )

    # 사용자가 입력한 데이터: 노란색 별표
    fig_scatter.add_trace(
        go.Scatter(
            x=[value1],
            y=[value2],
            mode="markers",
            name="내가 입력한 데이터",
            marker=dict(
                symbol="star",
                size=22,
                color="yellow",
                line=dict(
                    color="black",
                    width=1.5
                )
            )
        )
    )

    fig_scatter.update_layout(
        template="plotly_white",
        height=550,
        xaxis_title=feature1,
        yaxis_title=feature2,
        legend_title_text="붓꽃 품종",
        margin=dict(l=20, r=20, t=40, b=20)
    )

    st.plotly_chart(
        fig_scatter,
        use_container_width=True
    )

    st.caption(
        "노란색 별표는 사용자가 입력한 붓꽃의 위치입니다."
    )

    # --------------------------------------------------
    # 알고리즘 설명
    # --------------------------------------------------

    st.divider()
    st.subheader("📚 사용한 알고리즘 알아보기")

    for name, info in algorithm_info.items():

        with st.expander(info["title"]):
            st.markdown(info["description"])

    # --------------------------------------------------
    # 입력값 확인
    # --------------------------------------------------

    with st.expander("입력한 측정값 확인하기"):

        st.write(f"**{feature1}:** {value1} cm")
        st.write(f"**{feature2}:** {value2} cm")


# --------------------------------------------------
# 데이터 기본 정보
# --------------------------------------------------

with st.expander("📋 붓꽃 데이터 정보 확인하기"):

    col1, col2, col3 = st.columns(3)

    col1.metric("전체 데이터 수", f"{len(df)}개")
    col2.metric("붓꽃 품종 수", f"{df['품종'].nunique()}종")
    col3.metric("측정 항목 수", "4개")

    st.write("**데이터 미리보기**")
    st.dataframe(
        df.head(10),
        use_container_width=True
    )

    st.write("**품종별 데이터 개수**")
    st.dataframe(
        df["품종"].value_counts().rename("데이터 수"),
        use_container_width=True
    )


# --------------------------------------------------
# 두 가지 예측 탭
# --------------------------------------------------

tab1, tab2 = st.tabs([
    "🌸 꽃잎으로 예측하기",
    "🍃 꽃받침으로 예측하기"
])

with tab1:

    prediction_tab(
        feature1="꽃잎 길이",
        feature2="꽃잎 너비",
        tab_key="petal",
        title="🌸 꽃잎 측정값으로 품종 예측",
        description=(
            "꽃잎의 길이와 너비를 입력하여 "
            "붓꽃의 품종을 예측합니다."
        )
    )

with tab2:

    prediction_tab(
        feature1="꽃받침 길이",
        feature2="꽃받침 너비",
        tab_key="sepal",
        title="🍃 꽃받침 측정값으로 품종 예측",
        description=(
            "꽃받침의 길이와 너비를 입력하여 "
            "붓꽃의 품종을 예측합니다."
        )
    )


# --------------------------------------------------
# 하단 안내
# --------------------------------------------------

st.divider()

st.caption(
    "🌱 본 프로그램은 Iris 붓꽃 데이터를 활용한 "
    "머신러닝 품종 예측 학습용 프로그램입니다."
)
