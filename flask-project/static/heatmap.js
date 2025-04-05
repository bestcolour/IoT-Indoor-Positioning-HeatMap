document.addEventListener("DOMContentLoaded", function () {
    const container = document.getElementById("heatmapContainer");
    const modeSelector = document.getElementById("modeSelector");
  
    const width = container.clientWidth;
    const height = container.clientHeight;
  
    const heatmap = h337.create({
      container: container,
      radius: 50,
      maxOpacity: 0.6,
      minOpacity: 0.1,
      blur: 0.75
    });
  
    const MIN_X = -15;
    const MAX_X = 15;
    const MIN_Y = -15;
    const MAX_Y = 20;
  
    function loadHeatmap(mode = "ble") {
      fetch(`/api/heatmap?mode=${mode}`)
        .then(response => response.json())
        .then(data => {
          console.log("Fetched data:", data);
  
          // fallback demo if no data
          if (!data || data.length === 0) {
            console.log("No data found, using demo points.");
            data = [
              { x: 0.1, y: 2, value: 1 },
              { x: 1, y: 2, value: 1 },
              { x: 2, y: 3, value: 1 },
              { x: 3.5, y: 5, value: 1 }
            ];
          }
  
          const scaledData = data.map(d => ({
            x: Math.floor(((d.x - MIN_X) / (MAX_X - MIN_X)) * width),
            y: Math.floor(height - ((d.y - MIN_Y) / (MAX_Y - MIN_Y)) * height),
            value: d.value || 1
          }));
  
          heatmap.setData({
            max: 10,
            data: scaledData
          });
        })
        .catch(err => console.error("Heatmap fetch error:", err));
    }
  
    // Initial load
    loadHeatmap();
  
    // Change source
    modeSelector.addEventListener("change", () => {
      loadHeatmap(modeSelector.value);
    });
  });
  