# Port & Sail Calculation

## Comprehensive Maritime Voyage Event Analysis

This project involves extracting, transforming, and analyzing maritime voyage data using SQL and Python. The goal is to gain insights into voyage efficiencies and patterns by focusing on temporal and spatial aspects of maritime events.

## Requirements

1. **SQL Query Enhancements:**
    - Extract data for the specified vessel and voyage, and exclude records with non-null `allocatedVoyageId`.
    - Calculate precise UTC date-times for events and generate time durations between key events.
    - Identify and segment different voyage stages based on a series of 'SOSP' (Start of Sea Passage) and 'EOSP' (End of Sea Passage) events.
    - Calculate the cumulative sailing time and the time spent at ports for each voyage segment.
    - Calculate the distance between consecutive ports based on latitude and longitude data.

2. **Programming Task Enhancements:**
    - Replicate the SQL query logic in Python to perform equivalent data processing.
    - Implement a function to calculate distances between geographic coordinates.
    - Use data visualization to plot the timeline of events and durations for visual insights into the voyage pattern.
    - Incorporate error handling and data validation to ensure robust script performance.

## Database Setup

### Creating the Table and Inserting Data

```sql
CREATE TABLE voyages (
    id INT,
    event VARCHAR(50),
    dateStamp INT,
    timeStamp FLOAT,
    voyage_From VARCHAR(50),
    lat DECIMAL(9,6),
    lon DECIMAL(9,6),
    imo_num VARCHAR(20),
    voyage_Id VARCHAR(20),
    allocatedVoyageId VARCHAR(20)
);

INSERT INTO voyages VALUES
(1, 'SOSP', 43831, 0.708333, 'Port A', 34.0522, -118.2437, '9434761', '6', NULL),
(2, 'EOSP', 43831, 0.791667, 'Port A', 34.0522, -118.2437, '9434761', '6', NULL),
(3, 'SOSP', 43832, 0.333333, 'Port B', 36.7783, -119.4179, '9434761', '6', NULL),
(4, 'EOSP', 43832, 0.583333, 'Port B', 36.7783, -119.4179, '9434761', '6', NULL);
```
### Implementing the Haversine Function
The haversine function calculates the great-circle distance between two points on the Earth's surface given their latitude and longitude.

```sql
DELIMITER //

CREATE FUNCTION haversine(lat1 DOUBLE, lon1 DOUBLE, lat2 DOUBLE, lon2 DOUBLE)
RETURNS DOUBLE
DETERMINISTIC
BEGIN
    DECLARE R DOUBLE DEFAULT 6371; -- Earth radius in kilometers
    DECLARE dLat DOUBLE;
    DECLARE dLon DOUBLE;
    DECLARE a DOUBLE;
    DECLARE c DOUBLE;
    DECLARE d DOUBLE;

    SET lat1 = RADIANS(lat1);
    SET lon1 = RADIANS(lon1);
    SET lat2 = RADIANS(lat2);
    SET lon2 = RADIANS(lon2);

    SET dLat = lat2 - lat1;
    SET dLon = lon2 - lon1;

    SET a = SIN(dLat / 2) * SIN(dLat / 2) + COS(lat1) * COS(lat2) * SIN(dLon / 2) * SIN(dLon / 2);
    SET c = 2 * ATAN2(SQRT(a), SQRT(1 - a));

    SET d = R * c;

    RETURN d; -- distance in kilometers
END //

DELIMITER ;
```
### Running the SQL Query
The following SQL query extracts and processes the voyage data, calculates distances, and segments the voyage into stages.

```sql
WITH voyage_data AS (
    SELECT
        id,
        event,
        DATE_ADD(DATE_ADD('1899-12-30', INTERVAL dateStamp DAY), INTERVAL timeStamp * 86400 SECOND) AS event_datetime,
        voyage_From,
        lat,
        lon,
        imo_num,
        voyage_Id,
        LAG(event) OVER (PARTITION BY voyage_Id ORDER BY dateStamp, timeStamp) AS prev_event,
        LAG(DATE_ADD(DATE_ADD('1899-12-30', INTERVAL dateStamp DAY), INTERVAL timeStamp * 86400 SECOND)) OVER (PARTITION BY voyage_Id ORDER BY dateStamp, timeStamp) AS prev_event_datetime,
        LAG(lat) OVER (PARTITION BY voyage_Id ORDER BY dateStamp, timeStamp) AS prev_lat,
        LAG(lon) OVER (PARTITION BY voyage_Id ORDER BY dateStamp, timeStamp) AS prev_lon
    FROM voyages
    WHERE imo_num = '9434761' AND voyage_Id = '6' AND allocatedVoyageId IS NULL
)
SELECT
    id,
    event,
    event_datetime,
    voyage_From,
    lat,
    lon,
    imo_num,
    voyage_Id,
    prev_event,
    prev_event_datetime,
    TIMESTAMPDIFF(SECOND, prev_event_datetime, event_datetime) / 3600.0 AS duration_hours,
    CASE 
        WHEN event = 'SOSP' AND prev_event = 'EOSP' THEN 'At Sea'
        WHEN event = 'EOSP' AND prev_event = 'SOSP' THEN 'At Port'
        ELSE 'Unknown'
    END AS stage,
    IFNULL(haversine(lat, lon, prev_lat, prev_lon), 0) AS distance_travelled
FROM voyage_data
ORDER BY event_datetime;
```
## Python Script
The Python script replicates the SQL query logic, calculates distances, and visualizes the voyage data.
### script
```python
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
```

## Explanation of Output
The output of the SQL query and Python script provides detailed information on the voyage events, including:
- Event Datetimes: Precise UTC datetime calculated from the dateStamp and timeStamp.
- Durations: Time durations between the current and previous events, in hours.
- Stages: Categorization of the voyage into 'At Sea', 'At Port', and 'Unknown' stages.
- Distance Travelled: Distance in kilometers between the current and previous port, calculated using the haversine formula.
