import openpyxl
import time
import threading
from flask import Flask, jsonify, render_template_string

# Initialize Flask app
app = Flask(__name__)

# Initialize sensor data storage
sensor_data = {
    "MQ7": [],
    "Flame": [],
    "Temp": [],
    "Humidity": [],
    "Water_Level": [],
    "Soil": [],
    "Rain": [],
    "MQ135": [],
    "Timestamp": [],
    "latest_values": {},
    "warnings": []  # Store hazard warnings
}

# Read Excel file and update sensor data
def read_excel():
    wb = openpyxl.load_workbook('sensor_data.xlsx')
    sheet = wb.active
    values = []

    for row in sheet.iter_rows(min_row=2, values_only=True):
        values.append(row)

    return values

# Hazard prediction algorithm
def hazard_prediction(latest_data):
    try:
        # Preprocess sensor values to extract numeric part
        def parse_value(value):
            try:
                # Remove non-numeric characters and convert to float
                numeric_value = ''.join(filter(str.isdigit, str(value)))
                return float(numeric_value) if numeric_value else None
            except ValueError:
                return None  # In case parsing fails
        
        rain = parse_value(latest_data[6])  # Rain Sensor Value
        water_level = parse_value(latest_data[4])  # Water Level Sensor Value
        soil_moisture = parse_value(latest_data[5])  # Soil Moisture Sensor Value
        flame = parse_value(latest_data[1])  # Flame Sensor Value
        temp = parse_value(latest_data[2])  # Temperature Sensor Value
        air_quality_mq7 = parse_value(latest_data[0])  # MQ7 Sensor Value
        air_quality_mq135 = parse_value(latest_data[7])  # MQ135 Sensor Value

        # Log the parsed values for debugging
        print(f"Parsed values - Rain: {rain}, Water Level: {water_level}, Soil: {soil_moisture}, Flame: {flame}, Temp: {temp}, MQ7: {air_quality_mq7}, MQ135: {air_quality_mq135}")

        # Initialize hazard status
        hazard_status = {
            "Flood": False,
            "Fire": False,
            "Air Quality": False
        }

        # Hazard conditions (ensure values are within a valid range before checking)
        if rain is not None and water_level is not None and soil_moisture is not None:
            if rain < 40000 and water_level < 200 and soil_moisture < 40000:
                hazard_status["Flood"] = True

        # Check flame sensor value for fire hazard (flame less than 4500)
        if flame is not None:
            if flame < 3500:
                hazard_status["Fire"] = True
            if temp/10 > 31:
                hazard_status["Fire"] = True# Trigger fire warning if flame value is low

        if air_quality_mq7 is not None and air_quality_mq135 is not None:
            if air_quality_mq135 > 9000:
                hazard_status["Air Quality"] = True
                

        return hazard_status
    except Exception as e:
        print(f"Error in hazard_prediction: {e}")
        return {"Flood": False, "Fire": False, "Air Quality": False}

# Update sensor data from Excel every 2 seconds
def update_sensor_data():
    while True:
        try:
            data = read_excel()
            if data:
                latest_data = data[-1]  # Get the latest row of data
                timestamp = latest_data[8]  # Timestamp column index

                # Append data to respective lists
                sensor_data["MQ7"].append(latest_data[0])
                sensor_data["Flame"].append(latest_data[1])
                sensor_data["Temp"].append(latest_data[2])
                sensor_data["Humidity"].append(latest_data[3])
                sensor_data["Water_Level"].append(latest_data[4])
                sensor_data["Soil"].append(latest_data[5])
                sensor_data["Rain"].append(latest_data[6])
                sensor_data["MQ135"].append(latest_data[7])
                sensor_data["Timestamp"].append(timestamp)

                # Update latest values
                sensor_data["latest_values"] = {
                    "MQ7": latest_data[0],
                    "Flame": latest_data[1],
                    "Temp": latest_data[2],
                    "Humidity": latest_data[3],
                    "Water_Level": latest_data[4],
                    "Soil": latest_data[5],
                    "Rain": latest_data[6],
                    "MQ135": latest_data[7],
                }

                # Call hazard prediction
                hazard_status = hazard_prediction(latest_data)
                sensor_data["hazard_status"] = hazard_status
                print(f"Updated hazard status: {hazard_status}")

            time.sleep(2)  # Update every 2 seconds

        except Exception as e:
            print(f"Error in update_sensor_data: {e}")

# Flask route to get sensor data as JSON
@app.route('/data')
def data():
    return jsonify(sensor_data)

# Flask route to render the HTML page
@app.route('/')
def index():
    return render_template_string(open_html_template())

# HTML Template
def open_html_template():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart City System</title>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/plotly.js-dist@2.14.0/plotly.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #121212;
            color: #ffffff;
            margin: 0;
            padding: 20px;
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
        }
        .container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .chart-container, .status-container {
            padding: 10px;
            background: #1e1e1e;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.4);
        }
        .status-container {
            grid-column: span 2;
            text-align: center;
        }
        .status-container i {
            font-size: 40px;
            margin-right: 10px;
        }
        .hazard-section {
            margin: 20px 0;
        }
        .hazard {
            font-size: 18px;
            margin: 10px 0;
        }
        .hazard i {
            font-size: 20px;
            margin-right: 10px;
        }
        .hazard-safe {
            color: #4CAF50;
        }
        .hazard-danger {
            color: #FF5722;
        }
    </style>
    <script>
        // Function to fetch data every 2 seconds and update UI
        function fetchData() {
            $.ajax({
                url: '/data',
                type: 'GET',
                success: function(data) {
                    updateGraphs(data);
                    updateLatestValues(data);
                    updateHazardStatus(data);
                }
            });
        }

        // Function to update graphs
        function updateGraphs(data) {
            const timestamps = data.Timestamp;
            Plotly.react('mq7Graph', [{ x: timestamps, y: data.MQ7, type: 'scatter', mode: 'lines+markers', name: 'MQ7 Sensor' }], { title: 'MQ7 Sensor' });
            Plotly.react('flameGraph', [{ x: timestamps, y: data.Flame, type: 'scatter', mode: 'lines+markers', name: 'Flame Sensor' }], { title: 'Flame Sensor' });
            Plotly.react('tempGraph', [{ x: timestamps, y: data.Temp, type: 'scatter', mode: 'lines+markers', name: 'Temperature' }], { title: 'Temperature' });
            Plotly.react('humidityGraph', [{ x: timestamps, y: data.Humidity, type: 'scatter', mode: 'lines+markers', name: 'Humidity' }], { title: 'Humidity' });
            Plotly.react('waterLevelGraph', [{ x: timestamps, y: data.Water_Level, type: 'scatter', mode: 'lines+markers', name: 'Water Level' }], { title: 'Water Level' });
        }

        // Function to update the latest sensor values
        function updateLatestValues(data) {
            $('#mq7Value').text(data.latest_values.MQ7);
            $('#flameValue').text(data.latest_values.Flame);
            $('#tempValue').text(data.latest_values.Temp);
            $('#humidityValue').text(data.latest_values.Humidity);
            $('#waterLevelValue').text(data.latest_values.Water_Level);
        }

        // Function to update the hazard status
        function updateHazardStatus(data) {
            const hazardStatus = data.hazard_status;

            // Flood status
            const floodElement = $('#floodStatus');
            if (hazardStatus.Flood) {
                floodElement.html('<i class="fas fa-exclamation-triangle hazard-danger"></i> Flood Warning');
                floodElement.attr('class', 'hazard hazard-danger');
            } else {
                floodElement.html('<i class="fas fa-check-circle hazard-safe"></i> Flood Safe');
                floodElement.attr('class', 'hazard hazard-safe');
            }

            // Fire status (based on flame sensor value < 4500)
            const fireElement = $('#fireStatus');
            if (hazardStatus.Fire) {        
                fireElement.html('<i class="fas fa-exclamation-triangle hazard-danger"></i> Fire Warning');
                fireElement.attr('class', 'hazard hazard-danger');
            } else {    
                fireElement.html('<i class="fas fa-check-circle hazard-safe"></i> Fire Safe');
                fireElement.attr('class', 'hazard hazard-safe');
            }

            // Air quality status
            const airElement = $('#airQualityStatus');
            if (hazardStatus['Air Quality']) {
                airElement.html('<i class="fas fa-exclamation-triangle hazard-danger"></i> Poor Air Quality');
                airElement.attr('class', 'hazard hazard-danger');
            } else {
                airElement.html('<i class="fas fa-check-circle hazard-safe"></i> Good Air Quality');
                airElement.attr('class', 'hazard hazard-safe');
            }
        }

        // Fetch data every 2 seconds
        $(document).ready(function() {
            fetchData();
            setInterval(fetchData, 2000);
        });
    </script>
</head>
<body>
    <h1>Smart City System: Hazard Warnings</h1>
    <div class="status-container">
        <div class="hazard-section">
            <div id="floodStatus" class="hazard hazard-safe"><i class="fas fa-check-circle hazard-safe"></i> Flood Safe</div>
            <div id="fireStatus" class="hazard hazard-safe"><i class="fas fa-check-circle hazard-safe"></i> Fire Safe</div>
            <div id="airQualityStatus" class="hazard hazard-safe"><i class="fas fa-check-circle hazard-safe"></i> Good Air Quality</div>
        </div>
    </div>
    <div class="container">
        <div class="chart-container">
            <div id="mq7Graph"></div>
        </div>
        <div class="chart-container">
            <div id="flameGraph"></div>
        </div>
        <div class="chart-container">
            <div id="tempGraph"></div>
        </div>
        <div class="chart-container">
            <div id="humidityGraph"></div>
        </div>
        <div class="chart-container">
            <div id="waterLevelGraph"></div>
        </div>
    </div>
</body>
</html>
    """

# Function to start the Flask app
def run_flask():
    app.run(debug=False, host='0.0.0.0', port=8000)

if __name__ == "__main__":
    # Start Flask app in a separate thread
    threading.Thread(target=run_flask).start()

    # Start updating the sensor data in a separate thread
    threading.Thread(target=update_sensor_data, daemon=True).start()
