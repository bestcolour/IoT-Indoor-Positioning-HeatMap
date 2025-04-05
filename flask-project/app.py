
import os
import sqlite3
from flask import Flask, render_template, request

import plotly.graph_objects as go
import numpy as np
import pandas as pd
from PIL import Image
import base64
import io
import html as html_lib
from scipy.ndimage import gaussian_filter

app = Flask(__name__)

# Base path setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WIFI_DB = os.path.join(BASE_DIR, "../Wifi_only/positioning.db")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/plotly-heatmap")
def plotly_heatmap():
    # === Load background image ===
    image_path = os.path.join("static", "Retail-store-layouts-Grid.jpg")
    img = Image.open(image_path)
    width, height = img.size

    # === Query WiFi DB ===
    conn = sqlite3.connect(WIFI_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT x, y FROM wifi_estimated_positions")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "No WiFi data found.", 404

    data = pd.DataFrame(rows, columns=["x", "y"])
    data["value"] = 1

    # === Rescale coordinates to match image size ===
    data["x"] = (data["x"] - data["x"].min()) / (data["x"].max() - data["x"].min()) * width
    data["y"] = (data["y"] - data["y"].min()) / (data["y"].max() - data["y"].min()) * height

    # === Bin into 2D heatmap ===
    grid_x, grid_y = 150, 150
    x_edges = np.linspace(0, width, grid_x + 1)
    y_edges = np.linspace(0, height, grid_y + 1)
    heatmap_matrix, xbins, ybins = np.histogram2d(
        data['x'], data['y'], bins=[x_edges, y_edges], weights=data['value']
    )

    # === Boost visibility ===
    heatmap_matrix = gaussian_filter(heatmap_matrix, sigma=2)
    heatmap_matrix[heatmap_matrix == 0] = None

    fig = go.Figure()
    fig.add_trace(go.Heatmap(
        z=heatmap_matrix.T,
        x=xbins,
        y=ybins,
        colorscale='YlOrRd',  # brighter, no dark tones
        opacity=0.75,
        showscale=True,
        zsmooth='best',
        zmax=2
    ))

    fig.update_layout(
        images=[dict(
            source="data:image/png;base64," + encode_image(img),
            xref="x", yref="y",
            x=0, y=0,
            sizex=width, sizey=height,
            sizing="stretch",
            layer="below"
        )],
        xaxis=dict(range=[0, width], scaleanchor="y", showgrid=False),
        yaxis=dict(range=[height, 0], showgrid=False),
        margin=dict(l=0, r=0, t=0, b=0),
        width=width, height=height
    )

    html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    escaped_html = html_lib.escape(html)
    return f"<iframe style='border:none;width:100%;height:100vh;' srcdoc='{escaped_html}'></iframe>"

def encode_image(img):
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode()

if __name__ == '__main__':
    app.run(debug=True)
