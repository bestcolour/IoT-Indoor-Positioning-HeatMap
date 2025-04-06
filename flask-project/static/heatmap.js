document.addEventListener("DOMContentLoaded", function () {
    const container = document.getElementById("heatmapContainer");
    const modeSelector = document.getElementById("modeSelector");
  
    let heatmap;
    let currentMode = "ble";
    let rawData = [];
  
    const MIN_X = -15;
    const MAX_X = 30;
    const MIN_Y = -15;
    const MAX_Y = 30;
  
    function computeRadius(containerWidth) {
      // Tweak the factor below for bigger/smaller blobs
      const scaleFactor = 0.05;
      return Math.floor(containerWidth * scaleFactor);
    }
  
    function createHeatmap() {
      if (heatmap) {
        container.innerHTML = ""; // Remove existing canvas
      }
  
      const width = container.clientWidth;
      const height = container.clientHeight;
  
      heatmap = h337.create({
        container: container,
        radius: computeRadius(width),
        maxOpacity: 0.6,
        minOpacity: 0.1,
        blur: 0.75
      });
    }
  
    function scaleData(data) {
      const width = container.clientWidth;
      const height = container.clientHeight;
  
      return data.map(d => ({
        x: Math.floor(((d.x - MIN_X) / (MAX_X - MIN_X)) * width),
        y: Math.floor(height - ((d.y - MIN_Y) / (MAX_Y - MIN_Y)) * height),
        value: d.value || 1
      }));
    }
  
    function loadHeatmap(mode = "ble") {
      currentMode = mode;
  
      fetch(`/api/heatmap?mode=${mode}`)
        .then(response => response.json())
        .then(data => {
          rawData = (data && data.length) ? data : [
            { x: 0.1, y: 2, value: 1 },
            { x: 1, y: 2, value: 1 },
            { x: 2, y: 3, value: 1 },
            { x: 3.5, y: 5, value: 1 }
          ];
  
          renderHeatmap();
        })
        .catch(err => {
          console.error("Heatmap fetch error:", err);
        });
    }
  
    function renderHeatmap() {
      createHeatmap();
      const scaled = scaleData(rawData);
      heatmap.setData({
        max: 10,
        data: scaled
      });
    }
  
    // Initial load
    loadHeatmap();
  
    // Change mode
    modeSelector.addEventListener("change", () => {
      loadHeatmap(modeSelector.value);
    });
  
    // Responsive support
    window.addEventListener("resize", () => {
      renderHeatmap(); // Recreate heatmap with new dimensions
    });
  });
  