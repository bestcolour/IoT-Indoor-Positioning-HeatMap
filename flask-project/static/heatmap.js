document.addEventListener("DOMContentLoaded", function () {
    const container = document.getElementById("heatmapContainer");

    // Get actual width & height dynamically
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Define padding/margins for better positioning
    const padding = 60; // Leave some space for axes and labels

    // Default physical coordinate ranges (larger than before)
    const DEFAULT_MIN_X = 0;
    const DEFAULT_MAX_X = 4.3;      // doubled from 2.15
    const DEFAULT_MIN_Y = 0;
    const DEFAULT_MAX_Y = 11.68;    // doubled from 5.84

    // Optional scale factor to further enlarge the dynamic range (set to 1 for no extra scaling)
    const scaleFactor = 1; // Increase above 1 (e.g., 1.5 or 2) to further enlarge the spread

    // Create Heatmap instance with a larger radius if needed
    var heatmap = h337.create({
        container: container,
        radius: 50, // Increased radius
        maxOpacity: 0.6,
        minOpacity: 0.1,
        blur: 0.75
    });

    // Fetch heatmap data from your API endpoint
    fetch('/api/heatmap')
        .then(response => response.json())
        .then(data => {
            console.log("Raw Heatmap Data:", data);
            // Fallback sample data for four points if no data returned.
            if (!data || data.length === 0) {
                console.log("No data returned, using fallback sample data.");
                data = [
                    { x: 0.1, y: 5.7, value: 1 },
                    { x: 2.0, y: 5.7, value: 1 },
                    { x: 0.1, y: 0.3, value: 1 },
                    { x: 2.0, y: 0.3, value: 1 }
                ];
            }

            // Compute dynamic physical ranges from data
            let dynamicMinX = Math.min(...data.map(d => d.x));
            let dynamicMaxX = Math.max(...data.map(d => d.x));
            let dynamicMinY = Math.min(...data.map(d => d.y));
            let dynamicMaxY = Math.max(...data.map(d => d.y));

            // If the data's range is smaller than our desired default range, use the default range.
            if ((dynamicMaxX - dynamicMinX) < (DEFAULT_MAX_X - DEFAULT_MIN_X)) {
                dynamicMinX = DEFAULT_MIN_X;
                dynamicMaxX = DEFAULT_MAX_X;
            }
            if ((dynamicMaxY - dynamicMinY) < (DEFAULT_MAX_Y - DEFAULT_MIN_Y)) {
                dynamicMinY = DEFAULT_MIN_Y;
                dynamicMaxY = DEFAULT_MAX_Y;
            }

            // Optionally, enlarge the dynamic range further using a scale factor.
            // This will expand the range while keeping the center the same.
            if (scaleFactor > 1) {
                let centerX = (dynamicMinX + dynamicMaxX) / 2;
                let rangeX = (dynamicMaxX - dynamicMinX) * scaleFactor;
                dynamicMinX = centerX - rangeX / 2;
                dynamicMaxX = centerX + rangeX / 2;

                let centerY = (dynamicMinY + dynamicMaxY) / 2;
                let rangeY = (dynamicMaxY - dynamicMinY) * scaleFactor;
                dynamicMinY = centerY - rangeY / 2;
                dynamicMaxY = centerY + rangeY / 2;
            }

            console.log("Using Ranges:", dynamicMinX, dynamicMaxX, dynamicMinY, dynamicMaxY);

            // Scale the physical coordinates into canvas coordinates
            let scaledData = data.map(d => ({
                x: Math.floor(padding + ((d.x - dynamicMinX) / (dynamicMaxX - dynamicMinX)) * (width - padding * 2)),
                // Flip the y-axis so that physical y=0 is at the bottom
                y: Math.floor(height - padding - ((d.y - dynamicMinY) / (dynamicMaxY - dynamicMinY)) * (height - padding * 2)),
                value: d.value || 1
            }));

            console.log("Scaled Heatmap Data:", scaledData);

            heatmap.setData({
                max: 10,
                data: scaledData
            });

            // Draw axes using the dynamic (or default) physical coordinate ranges
            drawAxes(container, width, height, dynamicMinX, dynamicMaxX, dynamicMinY, dynamicMaxY, padding);
        })
        .catch(error => console.error("Error loading heatmap data:", error));
});

// Function to draw X and Y axes with numeric labels
function drawAxes(container, width, height, minX, maxX, minY, maxY, padding) {
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    canvas.style.position = "absolute";
    canvas.style.left = "0px";
    canvas.style.top = "0px";
    container.appendChild(canvas);

    const ctx = canvas.getContext("2d");

    // Draw X-Axis (at the bottom)
    ctx.beginPath();
    ctx.moveTo(padding, height - padding);
    ctx.lineTo(width - padding, height - padding);
    ctx.strokeStyle = "black";
    ctx.lineWidth = 3;
    ctx.stroke();

    // Draw Y-Axis (on the left)
    ctx.beginPath();
    ctx.moveTo(padding, height - padding);
    ctx.lineTo(padding, padding);
    ctx.strokeStyle = "black";
    ctx.lineWidth = 3;
    ctx.stroke();

    // Use a larger font for labels
    ctx.font = "20px Arial";
    ctx.fillText("X (m)", width - padding + 20, height - padding);
    ctx.fillText("Y (m)", padding - 40, padding - 10);

    // Define the number of divisions (tick marks)
    const divisions = 5;

    // X-Axis numeric labels
    for (let i = 0; i <= divisions; i++) {
        let posX = padding + i * ((width - padding * 2) / divisions);
        let labelX = (minX + (i / divisions) * (maxX - minX)).toFixed(2);
        ctx.fillText(labelX, posX - 10, height - padding + 30);
    }

    // Y-Axis numeric labels
    for (let i = 0; i <= divisions; i++) {
        let posY = height - padding - i * ((height - padding * 2) / divisions);
        let labelY = (minY + (i / divisions) * (maxY - minY)).toFixed(2);
        ctx.fillText(labelY, padding - 50, posY + 5);
    }
}
