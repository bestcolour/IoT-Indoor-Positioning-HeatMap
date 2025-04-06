# Evaluation Metrics Steps

## 1. Ground Truth Tables
Ensure that each of the positioning.db consists of the 'ground_truth_positions' table. If not, run the respective command according to the required mode(s):
```
python setup_grd_truth.py wifi
```
```
python setup_grd_truth.py ble
```
```
python setup_grd_truth.py hybrid
```

## 2. Compute the Evaluation Metrics
Run the script to compute the evaluation metrics of the required mode(s):
```
python calculate_accuracy.py wifi
```
```
python calculate_accuracy.py ble
```
```
python calculate_accuracy.py hybrid
```

## 3. Plotting of Evaluation Metrics for All Methods
Run the following command to generate the mean & median error plot, and the mean latency plot:
```
python evaluation_plots.py
```