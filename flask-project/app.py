import os
import sqlite3
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Base path setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Paths to different databases
BLE_DB = os.path.join(BASE_DIR, "../BLE_only/positioning.db")
WIFI_DB = os.path.join(BASE_DIR, "../Wifi_only/positioning.db")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/heatmap")
def get_heatmap_data():
    mode = request.args.get("mode", "ble").lower()  # default to BLE

    if mode == "wifi":
        db_path = WIFI_DB
        table = "wifi_estimated_positions"
    else:  # default to BLE
        db_path = BLE_DB
        table = "estimated_positions"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT x, y FROM {table}")
    data = cursor.fetchall()
    conn.close()

    heatmap_data = [{"x": d[0], "y": d[1], "value": 1} for d in data]
    return jsonify(heatmap_data)

if __name__ == '__main__':
    app.run(debug=True)
