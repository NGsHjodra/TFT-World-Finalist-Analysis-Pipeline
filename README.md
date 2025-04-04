Absolutely! Here's a polished `README.md` tailored to your **TFT World Finalist Analysis Pipeline** using GCP:

---

```markdown
# TFT World Finalist Analysis Pipeline

This project is an end-to-end **Data Engineering Pipeline** built on **Google Cloud Platform (GCP)** to analyze **Teamfight Tactics (TFT)** match data from **world finalists**. The pipeline focuses on **trait usage, item distribution, and meta analysis** to uncover strategic insights at the highest level of play.

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

## 💾 BigQuery Schema (Simplified)

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

Traits and units are structured as nested objects for flexible querying.

---

## 🚀 Deployment

### Requirements
- GCP Project with:
  - Cloud Run
  - BigQuery
  - Cloud Scheduler
  - Pub/Sub
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
├── EL/                    # Extract & Load Cloud Run function
├── TL/                    # Transform & Load Cloud Run function
├── Dockerfile             # Container spec
├── cloudbuild.yaml        # CI/CD config
├── requirements.txt       # Python dependencies
└── README.md              # You are here
```

---

## 📊 Future Work

- Build a Looker Studio dashboard (or alternative)
- Add deduplication logic in BigQuery
- Expand data model: track augments, item slots, unit tiers, etc.
- Enable dataset refresh (re-ingest and re-transform)