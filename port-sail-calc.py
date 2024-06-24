import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from math import radians, cos, sin, sqrt, atan2
import matplotlib.pyplot as plt

# Load Data
data = pd.read_csv('voyages.csv')  # Adjust to your data source

# Convert to UTC Datetime
data['event_datetime'] = pd.to_datetime(data['dateStamp'], origin='1899-12-30') + pd.to_timedelta(data['timeStamp'], unit='D')

# Sort data
data.sort_values(by=['event_datetime'], inplace=True)

# Define Haversine Function
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in kilometers
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

# Calculate Distances
data['prev_lat'] = data['lat'].shift(1)
data['prev_lon'] = data['lon'].shift(1)
data['distance_travelled'] = data.apply(
    lambda row: haversine(row['lat'], row['lon'], row['prev_lat'], row['prev_lon']) if pd.notnull(row['prev_lat']) else 0,
    axis=1
)

# Calculate Durations and Stages
data['prev_event'] = data['event'].shift(1)
data['prev_event_datetime'] = data['event_datetime'].shift(1)
data['duration_hours'] = (data['event_datetime'] - data['prev_event_datetime']).dt.total_seconds() / 3600.0
data['stage'] = np.where((data['event'] == 'SOSP') & (data['prev_event'] == 'EOSP'), 'At Sea', 
                         np.where((data['event'] == 'EOSP') & (data['prev_event'] == 'SOSP'), 'At Port', 'Unknown'))

# Visualization
plt.figure(figsize=(10, 6))
for key, grp in data.groupby(['stage']):
    plt.plot(grp['event_datetime'], grp['duration_hours'], label=key)
plt.xlabel('Event DateTime')
plt.ylabel('Duration (hours)')
plt.title('Voyage Timeline')
plt.legend()
plt.show()
