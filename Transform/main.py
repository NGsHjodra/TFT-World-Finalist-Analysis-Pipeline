from flask import Flask, request
import base64
import json

app = Flask(__name__)

@app.route("/", methods=["POST"])
def handle_pubsub():
    envelope = request.get_json()
    if not envelope or "message" not in envelope:
        return "Bad Request", 400

    # Decode message
    data = base64.b64decode(envelope["message"]["data"]).decode("utf-8")
    message = json.loads(data)
    
    if message.get("trigger") == "match_data_ready":
        print("Running transform step...")
        # Run your BigQuery SQL transform here
        run_transform_query()

    return "OK", 200

@app.route("/manual", methods=["POST"])
def manual_trigger():
    run_transform_query()
    return "Manual transform complete", 200

def run_transform_query():
    from google.cloud import bigquery

    client = bigquery.Client()
    query = """
    INSERT INTO `phuttimate-temp.TFT_dataset.parsed_participants`
    SELECT
      match_id,
      p.puuid,
      p.placement,
      p.level,
      p.traits,
      p.units,
      game_version,
      game_datetime
    FROM `phuttimate-temp.TFT_dataset.raw_matches` match,
    UNNEST(match.participants) AS p
    WHERE SAFE_CAST(p.placement AS INT64) IS NOT NULL
    """
    query_job = client.query(query)
    query_job.result()
    print("Transformation complete.")
