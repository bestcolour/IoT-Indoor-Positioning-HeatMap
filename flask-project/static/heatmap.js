document.addEventListener("DOMContentLoaded", function () {
    const container = document.getElementById("heatmapContainer");

    // Get actual width & height dynamically
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Define padding/margins for better positioning
    const padding = 60; // Keep some space inside the graph

    // Create Heatmap instance
    var heatmap = h337.create({
        container: container,
        radius: 35, // Reduce radius to prevent overlap
        maxOpacity: 0.6,
        minOpacity: 0.1,
        blur: 0.75
    });

    // Fetch heatmap data
    fetch('/api/heatmap')
        .then(response => response.json())
        .then(data => {
            console.log("Raw Heatmap Data:", data);

            // Force minX to start at 90
            let minX = 90;
            let maxX = Math.max(...data.map(d => d.x));  // Keep max X dynamic
            let minY = Math.min(...data.map(d => d.y));
            let maxY = Math.max(...data.map(d => d.y));

            // Scale X and Y values to fit within container bounds
            let scaledData = data.map(d => ({
                x: Math.floor(((d.x - minX) / (maxX - minX)) * (width - padding * 2) + padding),  // Scale x starting from 90
                y: Math.floor(height - (((d.y - minY) / (maxY - minY)) * (height - padding * 2) + padding)), // Scale & flip y
                value: 1
            }));

            console.log("Scaled Heatmap Data:", scaledData);

            heatmap.setData({
                max: 10,
                data: scaledData
            });

            // Draw X and Y axes
            drawAxes(container, width, height, minX, maxX, minY, maxY, padding);
        })
        .catch(error => console.error("Error loading heatmap data:", error));
});

// Function to draw X and Y axes with labels
function drawAxes(container, width, height, minX, maxX, minY, maxY, padding) {
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    canvas.style.position = "absolute";
    canvas.style.left = "0px";
    canvas.style.top = "0px";
    container.appendChild(canvas);

    const ctx = canvas.getContext("2d");

    // Draw X-Axis (Bottom)
    ctx.beginPath();
    ctx.moveTo(padding, height - padding);
    ctx.lineTo(width - padding, height - padding);
    ctx.strokeStyle = "black";
    ctx.lineWidth = 3;
    ctx.stroke();

    // Draw Y-Axis (Left)
    ctx.beginPath();
    ctx.moveTo(padding, height - padding);
    ctx.lineTo(padding, padding);
    ctx.strokeStyle = "black";
    ctx.lineWidth = 3;
    ctx.stroke();

    // Label axes
    ctx.font = "16px Arial";
    ctx.fillText("X", width - padding + 20, height - padding);
    ctx.fillText("Y", padding - 30, padding - 10);

    // Add numeric labels for X-Axis starting from 90
    for (let i = 0; i <= 5; i++) {
        let posX = padding + i * ((width - padding * 2) / 5);
        let labelX = Math.round(minX + (i / 5) * (maxX - minX)); // Starts at 90
        ctx.fillText(labelX, posX, height - padding + 20);
    }

    // Add numeric labels for Y-Axis
    for (let i = 0; i <= 5; i++) {
        let posY = height - padding - i * ((height - padding * 2) / 5);
        let labelY = Math.round(minY + (i / 5) * (maxY - minY));
        ctx.fillText(labelY, padding - 40, posY);
    }
}
