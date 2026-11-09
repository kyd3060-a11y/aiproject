
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

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import re

# ==========================================
# 1. 기본 화면
# ==========================================

st.title("🌡️ 서울 기온 분석 대시보드")
st.write(
    "서울의 장기간 기온 데이터를 활용하여 "
    "월별 평균기온과 연도별 기온 변화를 분석합니다."
)

st.divider()


# ==========================================
# 2. CSV 파일 경로 찾기
# ==========================================

current_dir = os.path.dirname(os.path.abspath(__file__))

possible_paths = [
    os.path.join(current_dir, "temperature.csv"),
    os.path.join(current_dir, "..", "temperature.csv"),
    os.path.join(os.getcwd(), "temperature.csv"),
    os.path.join(os.getcwd(), "..", "temperature.csv")
]

csv_path = next(
    (p for p in possible_paths if os.path.isfile(p)),
    None
)

if csv_path is None:
    st.error(
        "temperature.csv 파일을 찾을 수 없습니다. "
        "프로젝트 상위 폴더에 CSV 파일을 넣어주세요."
    )
    st.stop()


# ==========================================
# 3. 데이터 불러오기 및 한글 인코딩 처리
# ==========================================

@st.cache_data
def load_data(path):

    data = None

    for encoding in ["cp949", "euc-kr", "utf-8-sig", "utf-8"]:
        try:
            data = pd.read_csv(path, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue

    if data is None:
        raise ValueError("CSV 인코딩을 확인해주세요.")

    required_columns = [
        "일시",
        "평균기온(℃)",
        "최고기온(℃)",
        "최저기온(℃)"
    ]

    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"{col} 열이 없습니다.")

    # 기온 데이터를 숫자로 변환
    temp_columns = [
        "평균기온(℃)",
        "최고기온(℃)",
        "최저기온(℃)"
    ]

    for col in temp_columns:
        data[col] = pd.to_numeric(
            data[col], errors="coerce"
        )

    # ======================================
    # 4. 연도와 월 복원
    # ======================================

    month_dict = {
        "Jan": 1, "Feb": 2, "Mar": 3,
        "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9,
        "Oct": 10, "Nov": 11, "Dec": 12
    }

    years = []
    months = []

    previous_year = None
    previous_month = None

    for value in data["일시"]:

        match = re.fullmatch(
            r"([A-Za-z]{3})-(\d{2})",
            str(value).strip()
        )

        if not match:
            years.append(None)
            months.append(None)
            continue

        month_name = match.group(1).title()
        short_year = int(match.group(2))

        if month_name not in month_dict:
            years.append(None)
            months.append(None)
            continue

        month = month_dict[month_name]

        if previous_year is None:
            year = 1900 + short_year

        else:
            year = (previous_year // 100) * 100 + short_year

            # 이전 연도보다 작으면 다음 세기로 이동
            while year < previous_year:
                year += 100

            # 같은 연도에서 12월 다음 1월이면 다음 세기 표기
            if (
                year == previous_year
                and previous_month is not None
                and month < previous_month
            ):
                year += 100

        years.append(year)
        months.append(month)

        previous_year = year
        previous_month = month

    data["연도"] = years
    data["월"] = months

    data = data.dropna(subset=["연도", "월"])

    data["연도"] = data["연도"].astype(int)
    data["월"] = data["월"].astype(int)

    return data


try:
    df = load_data(csv_path)

except Exception as e:
    st.error(f"데이터 처리 오류: {e}")
    st.stop()


# ==========================================
# 5. 공통 데이터 설정
# ==========================================

years = sorted(df["연도"].unique())

months = list(range(1, 13))

month_names = [
    "1월", "2월", "3월", "4월",
    "5월", "6월", "7월", "8월",
    "9월", "10월", "11월", "12월"
]

# 그래프 공통 설정 함수
def chart_layout(fig, title, y_title="온도(℃)"):

    fig.update_layout(
        title=title,
        xaxis_title="월",
        yaxis_title=y_title,
        template="plotly_white",
        hovermode="x unified",
        height=480,
        legend_title="범례",
        margin=dict(l=40, r=30, t=70, b=50)
    )

    fig.update_xaxes(
        showgrid=True
    )

    fig.update_yaxes(
        showgrid=True
    )

    return fig


# ==========================================
# 그래프 1. 연도 선택 → 월별 평균기온
# ==========================================

st.header("📊 1. 서울의 월별 평균기온")

st.write(
    "연도를 선택하면 1월부터 12월까지 "
    "서울의 월별 평균기온을 확인할 수 있습니다."
)

selected_year = st.selectbox(
    "분석할 연도를 선택하세요.",
    years,
    index=len(years) - 1,
    key="average_year"
)

year_data = df[df["연도"] == selected_year]

monthly_avg = (
    year_data.groupby("월")["평균기온(℃)"]
    .mean()
    .reindex(months)
)

fig1 = go.Figure()

fig1.add_trace(
    go.Scatter(
        x=month_names,
        y=monthly_avg.values,
        mode="lines+markers",
        name="평균기온",
        line=dict(color="green", width=3),
        marker=dict(size=8),
        connectgaps=False
    )
)

fig1 = chart_layout(
    fig1,
    f"{selected_year}년 서울 월별 평균기온",
    "평균기온(℃)"
)

st.plotly_chart(fig1, use_container_width=True)


# ==========================================
# 그래프 2. 연도별 최고기온과 최저기온
# ==========================================

st.divider()

st.header("📈 2. 연도별 최고기온과 최저기온")

st.write(
    "각 연도에 기록된 최고기온과 최저기온의 "
    "변화를 비교합니다."
)

annual_data = (
    df.groupby("연도")
    .agg(
        최고기온=("최고기온(℃)", "max"),
        최저기온=("최저기온(℃)", "min")
    )
    .reset_index()
    .sort_values("연도")
)

fig2 = go.Figure()

# 최고기온 빨간색
fig2.add_trace(
    go.Scatter(
        x=annual_data["연도"],
        y=annual_data["최고기온"],
        mode="lines+markers",
        name="연도별 최고기온",
        line=dict(color="red", width=2),
        connectgaps=False
    )
)

# 최저기온 파란색
fig2.add_trace(
    go.Scatter(
        x=annual_data["연도"],
        y=annual_data["최저기온"],
        mode="lines+markers",
        name="연도별 최저기온",
        line=dict(color="blue", width=2),
        connectgaps=False
    )
)

fig2.update_layout(
    title="서울 연도별 최고·최저기온 변화",
    xaxis_title="연도",
    yaxis_title="온도(℃)",
    template="plotly_white",
    hovermode="x unified",
    height=520,
    legend_title="범례"
)

fig2.update_xaxes(
    dtick=10,
    showgrid=True
)

fig2.update_yaxes(
    showgrid=True
)

st.plotly_chart(fig2, use_container_width=True)


# ==========================================
# 그래프 3. 두 연도 비교
# ==========================================

st.divider()

st.header("🔍 3. 두 연도 기온 비교")

st.write(
    "두 개의 연도를 선택하여 "
    "월별 평균기온 차이를 비교할 수 있습니다."
)

col1, col2 = st.columns(2)

with col1:
    year1 = st.selectbox(
        "첫 번째 연도",
        years,
        index=max(0, len(years) - 2),
        key="compare_year1"
    )

with col2:
    year2 = st.selectbox(
        "두 번째 연도",
        years,
        index=len(years) - 1,
        key="compare_year2"
    )

if year1 == year2:

    st.warning("서로 다른 연도 2개를 선택해주세요.")

else:

    data1 = df[df["연도"] == year1]
    data2 = df[df["연도"] == year2]

    avg1 = (
        data1.groupby("월")["평균기온(℃)"]
        .mean()
        .reindex(months)
    )

    avg2 = (
        data2.groupby("월")["평균기온(℃)"]
        .mean()
        .reindex(months)
    )

    fig3 = go.Figure()

    fig3.add_trace(
        go.Scatter(
            x=month_names,
            y=avg1.values,
            mode="lines+markers",
            name=f"{year1}년 평균기온",
            line=dict(color="orange", width=3),
            connectgaps=False
        )
    )

    fig3.add_trace(
        go.Scatter(
            x=month_names,
            y=avg2.values,
            mode="lines+markers",
            name=f"{year2}년 평균기온",
            line=dict(color="purple", width=3),
            connectgaps=False
        )
    )

    fig3.update_layout(
        title=f"{year1}년과 {year2}년 월별 평균기온 비교",
        xaxis_title="월",
        yaxis_title="평균기온(℃)",
        template="plotly_white",
        hovermode="x unified",
        height=500,
        legend_title="비교 연도"
    )

    fig3.update_xaxes(showgrid=True)
    fig3.update_yaxes(showgrid=True)

    st.plotly_chart(fig3, use_container_width=True)

    # 두 연도의 월별 평균기온 비교표
    comparison = pd.DataFrame({
        "월": month_names,
        f"{year1}년": avg1.values,
        f"{year2}년": avg2.values
    })

    st.subheader("📋 두 연도 월별 평균기온 비교표")

    st.dataframe(
        comparison,
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# 6. 데이터 정보
# ==========================================

st.divider()

st.subheader("📌 데이터 정보")

col1, col2, col3 = st.columns(3)

col1.metric("전체 데이터 수", f"{len(df):,}개")
col2.metric("시작 연도", f"{df['연도'].min()}년")
col3.metric("마지막 연도", f"{df['연도'].max()}년")

st.caption(
    "자료: 업로드한 서울 기온 CSV 데이터 | "
    "결측치는 그래프에서 임의로 보정하지 않습니다."
)
