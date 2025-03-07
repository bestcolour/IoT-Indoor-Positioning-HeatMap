# from flask import Flask, render_template

# app = Flask(__name__)

# @app.route("/")
# @app.route("/index")
# def index():
# 	return render_template("index.html")

# if __name__ == '__main__':
# 	app.run(debug=True)

import os
import sqlite3
from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Set correct path to positioning.db (stored in BLE_only/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  
DB_PATH = os.path.join(BASE_DIR, "../BLE_only/positioning.db")  

@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/api/heatmap")
def get_heatmap_data():
    """Fetch processed position data (X, Y) for visualization"""
    conn = sqlite3.connect(DB_PATH)  # Use correct path
    cursor = conn.cursor()

    cursor.execute("SELECT x, y FROM positions")  # Fetch (X, Y) from Person 2’s table
    data = cursor.fetchall()
    
    conn.close()

    return jsonify([{"x": d[0], "y": d[1], "value": 1} for d in data])

if __name__ == '__main__':
    app.run(debug=True)

