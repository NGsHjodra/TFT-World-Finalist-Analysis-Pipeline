# TFT World Finalist Analysis Pipeline

This project is an end-to-end **Data Engineering Pipeline** built on **Google Cloud Platform (GCP)** to analyze **Teamfight Tactics (TFT)** match data from **world finalists**. The pipeline focuses on **trait usage, item distribution, and meta analysis** to uncover strategic insights at the highest level of play.

\*world finalists with some world participants

---

## 🎯 Objectives

- Extract match history of TFT world finalists using Riot Games API
- Store raw match data in **Google Cloud Storage (GCS)**
- Transform the raw data to a BigQuery-ready format
- Load the cleaned data into **BigQuery**
- Enable analysis and dashboarding via SQL or tools like Looker Studio

---

## 🧱 Architecture Overview

### 🔁 EL: Extract & Load to GCS
- Trigger: Cloud Scheduler (daily or on-demand)
- Hosted: Cloud Run (containerized Python function)
- Process:
  - Fetch `match_ids` from finalist PUUIDs
  - Download match data via Riot API
  - Save raw JSON to `gs://<bucket>/TFT/raw_matches/{match_id}.json`

### 🔁 TL: Transform & Load to BigQuery
- Trigger: Cloud Storage notification (`raw_matches/`)
- Hosted: Cloud Run (containerized Python function)
- Process:
  - Parse `info.participants[]` fields
  - Flatten key attributes: traits, units, augments, placement, etc.
  - Load cleaned rows to BigQuery table:  
    `primeval-proton-449808-i6.TFT_dataset.match_participants`

---

## 💾 BigQuery Schema

| Field           | Type             |
|----------------|------------------|
| match_id       | STRING (REQUIRED)|
| puuid          | STRING (REQUIRED)|
| placement      | INTEGER          |
| level          | INTEGER          |
| gold_left      | INTEGER          |
| traits         | RECORD (REPEATED)|
| units          | RECORD (REPEATED)|
| augments       | STRING (REPEATED)|
| game_version   | STRING           |
| game_datetime  | TIMESTAMP        |

---

Traits and units are structured as nested objects for flexible querying.
But you can also flatten them more if you prefer a more traditional schema.
With the current schema, you can easily query for trait usage and item distribution.
Sceduling those queries in BigQuery will allow you to analyze the data over time.

## 🚀 Deployment

### Requirements
- GCP Project with:
  - Cloud Run
  - BigQuery
  - Cloud Scheduler
  - IAM Service Accounts
- Docker
- Riot API Key

### Quick Setup
1. Clone the repo:
   ```bash
   git clone https://github.com/<your-username>/TFT-World-Finalist-Analysis-Pipeline
   ```
2. Deploy services using Cloud Build or manual UI steps
3. Schedule EL via Cloud Scheduler or run manually
4. TL will auto-trigger via GCS event

---

## 🛠 Folder Structure

```
.
├── config/                 # YAML config (e.g. finalist PUUID list)
├── Fetch_Load_to_GCS/                    # Extract & Load Cloud Run function
├── Transform_Load_to_Bigquery/                    # Transform & Load Cloud Run function
├── Dockerfile             # Container spec
├── cloudbuild.yaml        # CI/CD config
├── requirements.txt       # Python dependencies
└── README.md              # You are here
```

## Dashboard

[Looker Studio Dashboard](https://lookerstudio.google.com/reporting/b5acca32-6286-4697-833f-d6e025e33dca)

---

## 📊 Current Issues and Future Work

- **Current Issues**:
  - GCP cloud run function somehow can't access outside folder files (e.g. player.yaml) [currently hardcoded]
- **Future Work**:
  - Add more data sources (e.g. player stats)