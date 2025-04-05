import os
import sqlite3
import base64
import io
from flask import Flask, render_template, request
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from PIL import Image
from scipy.stats import gaussian_kde

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BLE_DB = os.path.join(BASE_DIR, "../BLE_only/positioning.db")
WIFI_DB = os.path.join(BASE_DIR, "../Wifi_only/positioning.db")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/plotly-heatmap")
def plotly_heatmap():
    mode = request.args.get("mode", "ble").lower()
    db_path = BLE_DB if mode == "ble" else WIFI_DB
    table = "estimated_positions" if mode == "ble" else "wifi_estimated_positions"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT x, y FROM {table}")
    rows = cursor.fetchall()
    conn.close()

    df = pd.DataFrame(rows, columns=["x", "y"])
    if df.empty:
        return "No data found", 404
    df["value"] = 1

    img_path = os.path.join("static", "supermarket-layout.png")
    img = Image.open(img_path)
    width, height = img.size

    # Normalize x/y to image size
    df["x"] = (df["x"] - df["x"].min()) / (df["x"].max() - df["x"].min()) * width
    df["y"] = (df["y"] - df["y"].min()) / (df["y"].max() - df["y"].min()) * height

    # KDE
    xy = np.vstack([df["x"], df["y"]])
    kde = gaussian_kde(xy, bw_method=0.1)  # Wider spread
    xgrid = np.linspace(0, width, 300)
    ygrid = np.linspace(0, height, 300)
    xmesh, ymesh = np.meshgrid(xgrid, ygrid)
    positions = np.vstack([xmesh.ravel(), ymesh.ravel()])
    zvals = np.reshape(kde(positions).T, xmesh.shape)

    # Normalize and mask
    zvals = zvals / np.nanmax(zvals)
    zvals[zvals < 0.01] = np.nan

    # Plot
    fig = go.Figure()
    fig.add_trace(go.Heatmap(
        z=zvals,
        x=xgrid,
        y=ygrid,
        colorscale=[
            [0.0, "rgb(0, 0, 255)"],
            [0.1, "rgb(0, 255, 255)"],
            [0.2, "rgb(0, 255, 128)"],
            [0.4, "rgb(0, 255, 0)"],
            [0.6, "rgb(255, 255, 0)"],
            [0.8, "rgb(255, 165, 0)"],
            [0.9, "rgb(255, 69, 0)"],
            [1.0, "rgb(255, 0, 0)"]
        ],
        zmin=0.01,
        zmax=1.0,
        opacity=0.85,
        showscale=True,
        zsmooth="best",
        hoverinfo='skip'
    ))

    fig.update_layout(
        images=[dict(
            source="data:image/png;base64," + encode_image(img),
            xref="x", yref="y",
            x=0, y=0,
            sizex=width, sizey=height,
            sizing="stretch",
            opacity=1.0,
            layer="below"
        )],
        xaxis=dict(range=[0, width], showticklabels=False, showgrid=False, zeroline=False),
        yaxis=dict(range=[height, 0], showticklabels=False, showgrid=False, zeroline=False),
        margin=dict(l=0, r=0, t=0, b=0),
        width=width,
        height=height
    )

    return fig.to_html(full_html=False, include_plotlyjs='cdn')

def encode_image(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

if __name__ == "__main__":
    app.run(debug=True)
