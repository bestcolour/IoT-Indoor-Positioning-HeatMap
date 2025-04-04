import os
import sqlite3
from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Correct database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "../Wifi_only/positioning.db")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/heatmap")
def get_heatmap_data():
    """Fetch (X, Y) position data from estimated_positions"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT x, y FROM estimated_positions")  # Fetch (X, Y) positions
    data = cursor.fetchall()
    conn.close()

    # Normalize values for Heatmap.js
    heatmap_data = [{"x": d[0], "y": d[1], "value": 1} for d in data]

    return jsonify(heatmap_data)

if __name__ == '__main__':
    app.run(debug=True)
