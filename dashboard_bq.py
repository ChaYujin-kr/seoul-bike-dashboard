import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from google.oauth2 import service_account
from google.cloud import bigquery
import os

# ---------------------------------------------------------
# [MIT Coder Comment]
# Google BigQuery 연동 + 상세 분석 기능이 통합된 Full Version 대시보드입니다.
# (Project ID 명시 및 Missing Column 이슈 수정 완료)
# ---------------------------------------------------------

st.set_page_config(page_title="서울시 따릉이 DW 대시보드", layout="wide")

st.title("🚲 서울시 따릉이 운영 대시보드 (Powered by BigQuery)")
st.markdown("""
<style>
    div.stButton > button:first-child {
        background-color: #00D000;
        color: white;
    }
</style>
**Data Source:** Google BigQuery (`seoul_bike_mart`)  
**Scenario:** 12:00 정각 리셋(15대) 가정 하에 실시간 OD 데이터를 반영한 재고 시뮬레이션
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. BigQuery 연결 및 데이터 로딩
# ---------------------------------------------------------
BASE_DIR = os.getcwd()
KEY_PATH = os.path.join(BASE_DIR, "keys", "seoul-bike-key.json")

# [중요] Airflow에서 사용한 프로젝트 ID와 100% 일치시켜야 합니다.
# 만약 에러가 계속 나면 구글 클라우드 콘솔에서 '프로젝트 ID'를 확인해서 여기에 적으세요.
PROJECT_ID = "seoul-bike-project" 

@st.cache_data(ttl=600) 
def load_data_from_bq():
    # [핵심 변경] st.secrets를 먼저 확인하고, 없으면 로컬 파일을 찾습니다.
    try:
        # 1순위: Streamlit Cloud 배포 환경 (Secrets)
        if "gcp_service_account" in st.secrets:
            creds = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"]
            )
        # 2순위: 로컬 개발 환경 (JSON 파일)
        else:
            file_path = os.path.join(os.getcwd(), "keys", "seoul-bike-key.json")
            creds = service_account.Credentials.from_service_account_file(file_path)
            
        client = bigquery.Client(credentials=creds, project=PROJECT_ID)

        # A. 마스터 정보 조회
        query_master = f"""
            SELECT station_id, district, lat, lon 
            FROM `{PROJECT_ID}.seoul_bike_mart.station_master`
        """
        
        # B. OD 데이터 조회
        query_od = f"""
            SELECT type, time, start_station_id, end_station_id, count
            FROM `{PROJECT_ID}.seoul_bike_mart.od_history`
            WHERE CAST(time AS INT64) >= 1200
        """
        
        with st.spinner('🛰️ 구글 클라우드(BigQuery)에서 데이터를 가져오는 중...'):
            df_master = client.query(query_master).to_dataframe()
            df_od = client.query(query_od).to_dataframe()
            
        return df_master, df_od

    except Exception as e:
        # 에러 메시지 출력
        raise e

try:
    df_stations, df_od_raw = load_data_from_bq()
except Exception as e:
    st.error(f"🚨 BigQuery 연결 실패! 에러 로그: {e}")
    st.stop()

# ---------------------------------------------------------
# 2. 데이터 가공 및 시뮬레이션 (Logic)
# ---------------------------------------------------------

# 시간 전처리 (HH 추출)
df_od_raw['hour'] = df_od_raw['time'].astype(str).str.zfill(4).str[:2].astype(int)

# 초기값 설정
df_stations['initial_stock'] = 15

# A. 대여(Out) 집계
rent_counts = df_od_raw[df_od_raw['type'] == '출발시간'].groupby('start_station_id')['count'].sum().reset_index()
rent_counts.columns = ['station_id', 'sim_outflow']

# B. 반납(In) 집계
return_counts = df_od_raw[df_od_raw['type'] == '도착시간'].groupby('end_station_id')['count'].sum().reset_index()
return_counts.columns = ['station_id', 'sim_inflow']

# C. 데이터 병합
df_stations = pd.merge(df_stations, rent_counts, on='station_id', how='left').fillna({'sim_outflow': 0})
df_stations = pd.merge(df_stations, return_counts, on='station_id', how='left').fillna({'sim_inflow': 0})

# D. 최종 재고 계산
df_stations['bike_count'] = df_stations['initial_stock'] - df_stations['sim_outflow'] + df_stations['sim_inflow']
df_stations['bike_count'] = df_stations['bike_count'].astype(int)

# E. 상태 분류
conditions = [
    (df_stations['bike_count'] < 3),
    (df_stations['bike_count'] > 25)
]
choices = ['부족 (Red)', '과잉 (Blue)']
df_stations['status'] = np.select(conditions, choices, default='적정 (Green)')

color_map = {'부족 (Red)': 'red', '과잉 (Blue)': 'blue', '적정 (Green)': 'green'}
df_stations['color_code'] = df_stations['status'].map(color_map)
df_stations['size'] = df_stations['status'].apply(lambda x: 12 if '적정' not in x else 6)

# ---------------------------------------------------------
# 3. 상단 KPI
# ---------------------------------------------------------
m1, m2, m3, m4 = st.columns(4)
m1.metric("🚲 총 대여소", f"{len(df_stations):,}개")
m2.metric("📉 부족 대여소", f"{sum(df_stations['status'] == '부족 (Red)')}개", delta_color="inverse")
m3.metric("📈 과잉 대여소", f"{sum(df_stations['status'] == '과잉 (Blue)')}개")
net_change = df_stations['sim_inflow'].sum() - df_stations['sim_outflow'].sum()
m4.metric("🔄 전체 수지 (In-Out)", f"{int(net_change):,}대")

st.divider()

# ---------------------------------------------------------
# 4. 메인 대시보드 (Map & Chart)
# ---------------------------------------------------------
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("🗺️ 실시간 재고 현황 (Map)")
    
    fig_map = px.scatter_mapbox(
        df_stations,
        lat="lat", lon="lon",
        color="status", size="size",
        color_discrete_map=color_map,
        hover_data={"station_id": True, "bike_count": True, "district": True, "lat": False, "lon": False, "size": False},
        zoom=10.5,
        center={"lat": 37.5665, "lon": 126.9780},
        height=600,
        mapbox_style="carto-positron"
    )
    fig_map.update_layout(clickmode='event+select')
    
    # 클릭 이벤트 활성화
    event = st.plotly_chart(fig_map, use_container_width=True, on_select="rerun", selection_mode="points")

with col_right:
    st.subheader("📊 자치구별 부족 현황 (Top 10)")
    
    # 구별 통계 집계
    district_agg = df_stations.groupby('district').agg(
        shortage_stations=('status', lambda x: (x == '부족 (Red)').sum())
    ).reset_index().sort_values(by='shortage_stations', ascending=False).head(10)
    
    fig_bar = px.bar(
        district_agg, x='district', y='shortage_stations',
        labels={'shortage_stations': '부족 대여소 수', 'district': '자치구'},
        color='shortage_stations', color_continuous_scale='Reds'
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    
    st.info("💡 지도 점을 클릭하면 아래에서 상세 내역을 볼 수 있습니다.")

# ---------------------------------------------------------
# 5. 상세 분석 (Drill-Down)
# ---------------------------------------------------------
st.markdown("---")
st.subheader("🔍 대여소 상세 분석")

selected_id = None
selected_district = None

# A. 지도 클릭 감지
if event and event["selection"]["points"]:
    idx = event["selection"]["points"][0]["point_index"]
    try:
        row = df_stations.iloc[idx]
        selected_id = row['station_id']
        selected_district = row['district'] # 주소 대신 구 정보 사용
    except: pass

# B. 드롭다운 선택 (Fallback)
if not selected_id:
    # 주소 대신 구 정보 표시
    opts = df_stations.apply(lambda x: f"{x['station_id']} - {x['district']}", axis=1).tolist()
    sel = st.selectbox("대여소 선택", opts)
    selected_id = sel.split(" - ")[0]
    selected_district = sel.split(" - ")[1]
else:
    st.success(f"📍 지도에서 선택됨: **{selected_id} ({selected_district})**")
    if st.button("선택 초기화"): st.rerun()

# 상세 지표 표시
target_station = df_stations[df_stations['station_id'] == selected_id].iloc[0]

col_d1, col_d2, col_d3, col_d4 = st.columns(4)
col_d1.metric("초기값 (12:00)", "15대")
col_d2.metric("대여 (Out)", f"-{int(target_station['sim_outflow'])}대")
col_d3.metric("반납 (In)", f"+{int(target_station['sim_inflow'])}대")
final_cnt = target_station['bike_count']
col_d4.metric("최종 재고", f"{final_cnt}대", delta=f"{final_cnt - 15}", delta_color="normal")

if final_cnt < 0:
    st.error(f"🚨 재고 부족 경고! ({abs(final_cnt)}대 부족)")

# ---------------------------------------------------------
# 6. 시간대별 전체 추이 (Line Chart)
# ---------------------------------------------------------
st.divider()
st.subheader("📈 시간대별 전체 이용 추이 (12시 이후)")

# 시간대별 집계
hourly_trend = df_od_raw.groupby('hour')['count'].sum().reset_index()

fig_trend = px.line(
    hourly_trend, x='hour', y='count', markers=True,
    labels={'count': '이용 건수', 'hour': '시간(Hour)'}
)
fig_trend.update_layout(xaxis=dict(tickmode='linear', tick0=12, dtick=1))
st.plotly_chart(fig_trend, use_container_width=True)