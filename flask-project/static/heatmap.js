document.addEventListener("DOMContentLoaded", function () {
    const container = document.getElementById("heatmapContainer");

    // Get container width and height dynamically
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Create the heatmap instance
    var heatmap = h337.create({
        container: container,
        radius: 100,  // Adjust size for visibility
        maxOpacity: 0.6,
        minOpacity: 0.1,
        blur: 0.75
    });

    // Fetch heatmap data from API
    fetch('/api/heatmap')
        .then(response => response.json())
        .then(data => {
            console.log("Raw Heatmap Data:", data);

            // Scaling X and Y values to match container size
            let scaledData = data.map(d => ({
                x: Math.floor((d.x / 6) * width),  // Scale x to fit full container
                y: Math.floor(height - (d.y / 6) * height),  // Invert Y-axis
                value: 1
            }));

            console.log("Scaled Heatmap Data:", scaledData);

            heatmap.setData({
                max: 10,
                data: scaledData
            });
        })
        .catch(error => console.error("Error loading heatmap data:", error));

    // Create Canvas for X and Y Axes
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
    ctx.moveTo(50, height - 50);
    ctx.lineTo(width - 20, height - 50);
    ctx.strokeStyle = "black";
    ctx.lineWidth = 3;
    ctx.stroke();

    // Draw Y-Axis (Left)
    ctx.beginPath();
    ctx.moveTo(50, height - 50);
    ctx.lineTo(50, 20);
    ctx.strokeStyle = "black";
    ctx.lineWidth = 3;
    ctx.stroke();

    // Label axes
    ctx.font = "20px Arial";
    ctx.fillText("X", width - 30, height - 20);
    ctx.fillText("Y", 10, 30);

    // Add numeric labels for X-Axis
    for (let i = 0; i <= 6; i++) {
        let posX = 50 + i * ((width - 100) / 6);  // Spacing for full width
        ctx.fillText(i, posX, height - 30);
    }

    // Add numeric labels for Y-Axis
    for (let i = 0; i <= 6; i++) {
        let posY = height - 50 - i * ((height - 100) / 6);  // Spacing for full height
        ctx.fillText(i, 30, posY);
    }
});

