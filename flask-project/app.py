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
BLEWIFI_DB = os.path.join(BASE_DIR, "../BLE+Wifi/positioning.db")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/plotly-heatmap")
def plotly_heatmap():
    mode = request.args.get("mode", "ble").lower()

    if mode == "ble":
        db_path = BLE_DB
        table = "estimated_positions"
    elif mode == "wifi":
        db_path = WIFI_DB
        table = "wifi_estimated_positions"
    elif mode == "hybrid":
        db_path = BLEWIFI_DB
        table = "hybrid_estimated_positions"
    else:
        return "Invalid mode", 400

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT x, y FROM {table}")
    rows = cursor.fetchall()
    conn.close()

    df = pd.DataFrame(rows, columns=["x", "y"])
    if df.empty:
        return "No data found", 404

    # Load and resize image for consistency
    img_path = os.path.join("static", "Supermarket-Mockup-Layout.png")
    img = Image.open(img_path)
    img = img.resize((1300, int(1300 * img.height / img.width)))
    width, height = img.size

    # Normalize and scale coordinates
    df["x"] = (df["x"] - df["x"].min()) / (df["x"].max() - df["x"].min()) * width
    df["y"] = (df["y"] - df["y"].min()) / (df["y"].max() - df["y"].min()) * height

    # Clamp values inside canvas
    df["x"] = df["x"].clip(lower=0, upper=width)
    df["y"] = df["y"].clip(lower=0, upper=height)

    # KDE grid with padding
    padding = 20
    xy = np.vstack([df["x"], df["y"]])
    kde = gaussian_kde(xy, bw_method=0.1)
    xgrid = np.linspace(padding, width - padding, 300)
    ygrid = np.linspace(padding, height - padding, 300)
    xmesh, ymesh = np.meshgrid(xgrid, ygrid)
    positions = np.vstack([xmesh.ravel(), ymesh.ravel()])
    zvals = np.reshape(kde(positions).T, xmesh.shape)

    zvals = zvals / np.nanmax(zvals)
    zvals[zvals < 0.01] = np.nan

    fig = go.Figure()
    fig.add_trace(go.Heatmap(
        z=zvals,
        x=xgrid,
        y=ygrid,
        colorscale=[
            [0.0, "rgb(0, 0, 255)"],
            [0.05, "rgb(0, 128, 255)"],
            [0.1, "rgb(0, 255, 255)"],
            [0.2, "rgb(0, 255, 128)"],
            [0.3, "rgb(0, 255, 0)"],
            [0.4, "rgb(128, 255, 0)"],
            [0.5, "rgb(255, 255, 0)"],
            [0.6, "rgb(255, 200, 0)"],
            [0.7, "rgb(255, 165, 0)"],
            [0.8, "rgb(255, 100, 0)"],
            [0.9, "rgb(255, 50, 0)"],
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
            xref="x",
            yref="y",
            x=0,
            y=0,
            sizex=width,
            sizey=height,
            sizing="stretch",
            opacity=1.0,
            layer="below"
        )],
        xaxis=dict(
            range=[0, width],
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            scaleanchor='y',
            constrain='domain'
        ),
        yaxis=dict(
            range=[height, 0],
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            scaleratio=1
        ),
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
