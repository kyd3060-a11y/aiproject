import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

# --------------------------------
# 1. 페이지 기본 설정
# --------------------------------

st.set_page_config(
    page_title="서울 관광지 TOP 10",
    page_icon="🗺️",
    layout="wide"
)

st.title("🗺️ 외국인 관광객이 좋아하는 서울 TOP 10")
st.write(
    "서울의 대표 관광 명소 10곳을 지도에서 확인하고 "
    "각 관광지의 매력을 알아보세요! ✨"
)

st.info(
    "외국인 관광객 선호도와 서울의 대표 관광 코스를 "
    "참고하여 선정한 추천 관광지입니다."
)

# --------------------------------
# 2. 관광지 데이터
# --------------------------------

attractions = [
    {
        "rank": 1,
        "name": "명동",
        "english": "Myeong-dong",
        "category": "쇼핑 · K-뷰티 · 길거리 음식",
        "lat": 37.5636,
        "lon": 126.9850,
        "description": "화장품과 패션 매장이 많고 다양한 길거리 음식을 맛볼 수 있는 대표 쇼핑 거리입니다."
    },
    {
        "rank": 2,
        "name": "홍대 거리",
        "english": "Hongdae",
        "category": "K-팝 · 공연 · 패션",
        "lat": 37.5563,
        "lon": 126.9236,
        "description": "거리 공연과 음악, 패션, 개성 있는 카페를 즐길 수 있어 젊은 여행객에게 인기가 많습니다."
    },
    {
        "rank": 3,
        "name": "경복궁",
        "english": "Gyeongbokgung Palace",
        "category": "한국 역사 · 전통문화",
        "lat": 37.5796,
        "lon": 126.9770,
        "description": "조선 시대의 대표 궁궐로 아름다운 건축물과 한복 체험을 통해 한국의 전통문화를 만날 수 있습니다."
    },
    {
        "rank": 4,
        "name": "성수동",
        "english": "Seongsu-dong",
        "category": "카페 · 팝업스토어",
        "lat": 37.5445,
        "lon": 127.0560,
        "description": "감각적인 카페와 편집숍, 다양한 브랜드 팝업스토어가 모여 있는 트렌디한 거리입니다."
    },
    {
        "rank": 5,
        "name": "강남역",
        "english": "Gangnam Station",
        "category": "쇼핑 · 맛집 · 도시문화",
        "lat": 37.4979,
        "lon": 127.0276,
        "description": "대형 상점과 음식점, 다양한 즐길 거리가 모여 있는 서울의 대표적인 번화가입니다."
    },
    {
        "rank": 6,
        "name": "N서울타워",
        "english": "N Seoul Tower",
        "category": "전망 · 야경 · 랜드마크",
        "lat": 37.5512,
        "lon": 126.9882,
        "description": "남산 정상에 있는 서울의 대표 전망 명소로 도시 전경과 아름다운 야경을 감상할 수 있습니다."
    },
    {
        "rank": 7,
        "name": "동대문디자인플라자",
        "english": "DDP",
        "category": "건축 · 전시 · 디자인",
        "lat": 37.5671,
        "lon": 127.0095,
        "description": "독특한 곡선형 건축물이 인상적인 복합문화공간으로 전시와 디자인 행사를 즐길 수 있습니다."
    },
    {
        "rank": 8,
        "name": "북촌한옥마을",
        "english": "Bukchon Hanok Village",
        "category": "전통가옥 · 사진 명소",
        "lat": 37.5826,
        "lon": 126.9830,
        "description": "전통 한옥이 모여 있는 마을로 서울의 옛 주거문화를 느낄 수 있습니다. 주민들을 위해 조용히 관람해야 합니다."
    },
    {
        "rank": 9,
        "name": "광장시장",
        "english": "Gwangjang Market",
        "category": "전통시장 · 한국 음식",
        "lat": 37.5701,
        "lon": 126.9997,
        "description": "빈대떡과 김밥 등 다양한 한국 길거리 음식을 맛보고 전통시장의 활기찬 분위기를 경험할 수 있습니다."
    },
    {
        "rank": 10,
        "name": "코엑스·별마당도서관",
        "english": "COEX & Starfield Library",
        "category": "쇼핑 · 문화공간",
        "lat": 37.5126,
        "lon": 127.0594,
        "description": "대형 쇼핑·문화 복합공간으로 높은 책장으로 유명한 별마당도서관도 함께 둘러볼 수 있습니다."
    }
]

# --------------------------------
# 3. 서울 지도 만들기
# --------------------------------

seoul_map = folium.Map(
    location=[37.5665, 126.9780],
    zoom_start=12,
    tiles="OpenStreetMap",
    control_scale=True
)

# 관광지 마커 모아보기
marker_cluster = MarkerCluster().add_to(seoul_map)

# --------------------------------
# 4. 지도에 관광지 표시
# --------------------------------

for place in attractions:

    popup_content = f"""
    <div style="width:220px; font-family:sans-serif;">
        <h3>{place['rank']}. {place['name']}</h3>
        <b>{place['english']}</b>
        <p>{place['category']}</p>
        <p>{place['description']}</p>
    </div>
    """

    folium.Marker(
        location=[
            place["lat"],
            place["lon"]
        ],

        tooltip=f"{place['rank']}. {place['name']}",

        popup=folium.Popup(
            popup_content,
            max_width=280
        ),

        icon=folium.DivIcon(
            html=f"""
            <div style="
                background-color:#2563eb;
                color:white;
                border:2px solid white;
                border-radius:50%;
                width:30px;
                height:30px;
                line-height:26px;
                text-align:center;
                font-weight:bold;
                font-size:13px;
                box-shadow:0 1px 5px #555;
            ">
                {place['rank']}
            </div>
            """
        )

    ).add_to(marker_cluster)

# --------------------------------
# 5. 지도 화면 출력
# --------------------------------

st.subheader("📍 서울 관광지 위치 지도")

st_folium(
    seoul_map,
    height=570,
    use_container_width=True,
    returned_objects=[]
)

# --------------------------------
# 6. 관광지 설명 출력
# --------------------------------

st.divider()

st.subheader("✨ 서울 관광지 TOP 10 소개")

for i in range(0, len(attractions), 2):

    columns = st.columns(2)

    for column, place in zip(
        columns,
        attractions[i:i+2]
    ):

        with column:

            st.markdown(
                f"### {place['rank']}. {place['name']}"
            )

            st.caption(
                f"{place['english']} | {place['category']}"
            )

            st.write(
                place["description"]
            )

            st.markdown("---")

# --------------------------------
# 7. 하단 안내
# --------------------------------

st.subheader("🌏 서울 여행을 즐겨보세요!")

st.write(
    "한국의 역사와 전통문화부터 쇼핑, 음식, "
    "최신 유행까지 다양한 서울의 매력을 경험해 보세요!"
)

st.caption(
    "지도 출처: OpenStreetMap | "
    "관광지 위치는 대표 지점 기준입니다."
)
