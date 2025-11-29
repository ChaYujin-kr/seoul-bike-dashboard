# 🚲 Seoul Bike Intelligent Operation Dashboard (서울시 따릉이 지능형 운영 대시보드)

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red)](https://streamlit.io/)
[![Airflow](https://img.shields.io/badge/Airflow-2.0%2B-green)](https://airflow.apache.org/)
[![Google BigQuery](https://img.shields.io/badge/Google%20BigQuery-Enabled-yellow)](https://cloud.google.com/bigquery)

---

## 🇰🇷 한국어 (Korean)

### 📖 프로젝트 소개
이 프로젝트는 **서울시 따릉이(공공자전거)** 의 대여 및 반납 데이터를 분석하여, 각 대여소의 **실시간 재고 현황을 시뮬레이션하고 시각화**하는 지능형 대시보드입니다.
데이터 엔지니어링(ETL) 파이프라인을 통해 데이터를 수집/적재하고, Streamlit을 통해 직관적인 운영 지표를 제공합니다.

### 🚀 주요 기능
1.  **데이터 파이프라인 (ETL)**
    *   서울 열린데이터 광장 등에서 원천 데이터를 수집합니다.
    *   **Airflow**를 사용하여 주기적으로 데이터를 전처리하고 **Google BigQuery**에 적재합니다.
    *   경량화된 순차 처리 로직으로 리소스를 최적화했습니다.
2.  **운영 시뮬레이션 대시보드**
    *   **Streamlit** 기반의 웹 애플리케이션입니다.
    *   특정 시점(예: 12:00) 기준 초기 재고를 가정하고, 실제 OD(Origin-Destination) 데이터를 기반으로 시간 흐름에 따른 재고 변화를 시뮬레이션합니다.
    *   **부족(Red)/과잉(Blue)** 상태를 지도 위에 시각화하여 운영상 주의가 필요한 대여소를 식별합니다.
3.  **상세 분석**
    *   자치구별 수급 불균형 현황 차트 제공.
    *   개별 대여소의 대여(Outflow)/반납(Inflow) 상세 내역 조회.

### 📂 프로젝트 구조
```bash
.
├── bike_etl.py          # Airflow DAG: 데이터 전처리 및 BigQuery 적재
├── dashboard.py         # Streamlit 대시보드 애플리케이션
├── crawl_od.py          # 데이터 크롤링 스크립트
├── dags/                # Airflow DAG 폴더
├── data/                # 로컬 데이터 저장소 (CSV 등)
└── requirements.txt     # 의존성 패키지 목록
```

### 🛠 설치 및 실행 방법

1.  **환경 설정**
    ```bash
    # 저장소 클론
    git clone https://github.com/your-username/seoul-bike-dashboard.git
    cd seoul-bike-dashboard

    # 패키지 설치
    pip install -r requirements.txt
    ```

2.  **GCP 자격 증명 설정**
    *   `keys/seoul-bike-key.json` 경로에 Google Cloud Service Account 키 파일을 위치시켜야 BigQuery 연동이 가능합니다.

3.  **대시보드 실행**
    ```bash
    streamlit run dashboard.py
    ```

---

## 🇺🇸 English

### 📖 Introduction
This project is an **Intelligent Operation Dashboard for Seoul Bike (Ttareungyi)**. It analyzes rental and return data to **simulate and visualize real-time inventory status** for each station.
It utilizes a Data Engineering (ETL) pipeline to collect and load data, providing intuitive operational metrics via Streamlit.

### 🚀 Key Features
1.  **Data Pipeline (ETL)**
    *   Collects raw data from sources like Seoul Open Data Plaza.
    *   Uses **Airflow** to preprocess data and load it into **Google BigQuery**.
    *   Optimized with lightweight sequential processing logic.
2.  **Operation Simulation Dashboard**
    *   Web application built with **Streamlit**.
    *   Simulates inventory changes over time based on actual OD (Origin-Destination) data, assuming an initial stock at a specific time (e.g., 12:00).
    *   Visualizes **Shortage (Red) / Surplus (Blue)** statuses on a map to identify stations requiring attention.
3.  **Detailed Analysis**
    *   Charts showing supply-demand imbalance by district.
    *   Detailed lookup of Rental (Outflow) / Return (Inflow) history for individual stations.

### 📂 Project Structure
```bash
.
├── bike_etl.py          # Airflow DAG: Data preprocessing & BigQuery loading
├── dashboard.py         # Streamlit Dashboard Application
├── crawl_od.py          # Data crawling script
├── dags/                # Airflow DAGs folder
├── data/                # Local data storage (CSV, etc.)
└── requirements.txt     # Dependency list
```

### 🛠 Installation & Usage

1.  **Setup**
    ```bash
    # Clone repository
    git clone https://github.com/your-username/seoul-bike-dashboard.git
    cd seoul-bike-dashboard

    # Install dependencies
    pip install -r requirements.txt
    ```

2.  **GCP Credentials**
    *   Place your Google Cloud Service Account key file at `keys/seoul-bike-key.json` to enable BigQuery integration.

3.  **Run Dashboard**
    ```bash
    streamlit run dashboard.py
    ```
