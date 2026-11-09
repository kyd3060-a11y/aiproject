
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import re

# -----------------------------------
# 1. 페이지 설정
# -----------------------------------
st.set_page_config(
    page_title="월별 기온 분석",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 월별 기온 분석")
st.write("원하는 월을 선택하면 연도별 최고기온과 최저기온을 비교할 수 있어요!")

# -----------------------------------
# 2. CSV 파일 경로 찾기
# -----------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))

possible_paths = [
    os.path.join(current_dir, "temperature.csv"),
    os.path.join(current_dir, "..", "temperature.csv"),
    os.path.join(os.getcwd(), "temperature.csv")
]

csv_path = None

for path in possible_paths:
    if os.path.exists(path):
        csv_path = path
        break

# -----------------------------------
# 3. CSV 파일 읽기
# -----------------------------------
@st.cache_data
def load_data(path):
    # 한글 인코딩 자동 대응
    for encoding in ["cp949", "euc-kr", "utf-8-sig", "utf-8"]:
        try:
            data = pd.read_csv(path, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("CSV 파일의 인코딩을 확인해주세요.")

    # 필요한 열 확인
    required_columns = [
        "일시",
        "최고기온(℃)",
        "최저기온(℃)"
    ]

    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"'{col}' 열이 CSV 파일에 없습니다.")

    # 날짜에서 월과 연도 추출
    month_dict = {
        "Jan": 1, "Feb": 2, "Mar": 3,
        "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9,
        "Oct": 10, "Nov": 11, "Dec": 12
    }

    def parse_date(value):
        match = re.fullmatch(
            r"([A-Za-z]{3})-(\d{2})",
            str(value).strip()
        )

        if not match:
            return pd.Series([None, None])

        month_name = match.group(1).title()
        year_short = int(match.group(2))

        if month_name not in month_dict:
            return pd.Series([None, None])

        # 1907~1999년, 2000~2026년 복원
        if year_short >= 7:
            year = 1900 + year_short
        else:
            year = 2000 + year_short

        month = month_dict[month_name]

        return pd.Series([year, month])

    data[["연도", "월"]] = data["일시"].apply(parse_date)

    data["연도"] = pd.to_numeric(
        data["연도"], errors="coerce"
    )

    data["월"] = pd.to_numeric(
        data["월"], errors="coerce"
    )

    data["최고기온(℃)"] = pd.to_numeric(
        data["최고기온(℃)"], errors="coerce"
    )

    data["최저기온(℃)"] = pd.to_numeric(
        data["최저기온(℃)"], errors="coerce"
    )

    data = data.dropna(subset=["연도", "월"])

    data["연도"] = data["연도"].astype(int)
    data["월"] = data["월"].astype(int)

    return data


# -----------------------------------
# 4. 데이터 불러오기
# -----------------------------------
if csv_path is None:
    st.error(
        "temperature.csv 파일을 찾을 수 없습니다. "
        "CSV 파일을 app.py 또는 상위 폴더에 넣어주세요."
    )
    st.stop()

try:
    df = load_data(csv_path)

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()


# -----------------------------------
# 5. 월 선택
# -----------------------------------
st.subheader("📅 분석할 월 선택")

month_names = [
    "1월", "2월", "3월", "4월",
    "5월", "6월", "7월", "8월",
    "9월", "10월", "11월", "12월"
]

selected_month_name = st.selectbox(
    "월을 선택하세요.",
    month_names
)

selected_month = month_names.index(
    selected_month_name
) + 1


# -----------------------------------
# 6. 선택한 월의 데이터 추출
# -----------------------------------
month_data = df[
    df["월"] == selected_month
].copy()

month_data = month_data.sort_values("연도")

# 최고기온과 최저기온이 모두 없는 행은 그래프에서 제외
month_data = month_data.dropna(
    subset=["최고기온(℃)", "최저기온(℃)"],
    how="all"
)


# -----------------------------------
# 7. 기온 꺾은선 그래프
# -----------------------------------
st.subheader("📈 월별 기온 변화")

if not month_data.empty:

    fig = go.Figure()

    # 최고기온 그래프 - 빨간색
    fig.add_trace(
        go.Scatter(
            x=month_data["연도"],
            y=month_data["최고기온(℃)"],
            mode="lines+markers",
            name="최고기온",
            line=dict(
                color="red",
                width=2
            ),
            connectgaps=False
        )
    )

    # 최저기온 그래프 - 파란색
    fig.add_trace(
        go.Scatter(
            x=month_data["연도"],
            y=month_data["최저기온(℃)"],
            mode="lines+markers",
            name="최저기온",
            line=dict(
                color="blue",
                width=2
            ),
            connectgaps=False
        )
    )

    fig.update_layout(
        title="월별 기온분석",
        xaxis_title="연도",
        yaxis_title="온도(℃)",
        legend_title="범례",
        hovermode="x unified",
        template="plotly_white",
        height=600,
        xaxis=dict(
            dtick=10,
            showgrid=True
        ),
        yaxis=dict(
            showgrid=True
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # -----------------------------------
    # 8. 데이터 표
    # -----------------------------------
    st.subheader("📋 선택한 월의 기온 데이터")

    display_data = month_data[
        ["연도", "최고기온(℃)", "최저기온(℃)"]
    ].copy()

    display_data = display_data.sort_values(
        "연도", ascending=False
    )

    st.dataframe(
        display_data,
        use_container_width=True,
        hide_index=True
    )

else:
    st.warning("선택한 월에 표시할 기온 데이터가 없습니다.")

# -----------------------------------
# 9. 데이터 정보
# -----------------------------------
st.divider()

st.caption(
    f"📊 분석 월: {selected_month_name} | "
    f"데이터 기간: {df['연도'].min()}년 ~ {df['연도'].max()}년"
)
