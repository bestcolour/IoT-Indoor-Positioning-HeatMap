import matplotlib.pyplot as plt
import numpy as np

# Sample data (update these with your actual results)
methods = ['BLE', 'Wi-Fi', 'Hybrid']
mean_errors = [5.24, 8.93, 4.67]
median_errors = [4.60, 9.23, 4.73]
mean_latencies = [0.0002, 0.0033, 1.0925]  # in milliseconds

# Set width of bars
bar_width = 0.25
x = np.arange(len(methods))

# Bar settings
x = np.arange(len(methods))
bar_width = 0.35

# Plot for Mean and Median Errors
fig, ax = plt.subplots(figsize=(8, 6))
mean_bars = ax.bar(x - bar_width/2, mean_errors, width=bar_width, label='Mean Error (m)')
median_bars = ax.bar(x + bar_width/2, median_errors, width=bar_width, label='Median Error (m)')

# Add value labels
for bar in mean_bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, height + 0.05, f'{height:.2f}', ha='center', va='bottom')

for bar in median_bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, height + 0.05, f'{height:.2f}', ha='center', va='bottom')

# Labels
ax.set_title('Positioning Error Comparison')
ax.set_xlabel('Methods')
ax.set_ylabel('Error (meters)')
ax.set_xticks(x)
ax.set_xticklabels(methods)
ax.legend()
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()


# Plot for Mean Latency
fig, ax = plt.subplots(figsize=(8, 6))
ax.bar(methods, mean_latencies, color='skyblue')

# Labels
ax.set_title('Mean Latency Comparison (Log Scale)')
ax.set_xlabel('Methods')
ax.set_ylabel('Mean Latency (ms)')
ax.set_yscale('log')
for i, val in enumerate(mean_latencies):
    ax.text(i, val + 0.0001, f'{val:.4f}', ha='center', va='bottom')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()