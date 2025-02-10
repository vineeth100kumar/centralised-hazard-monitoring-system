import socket
import pandas as pd
from datetime import datetime

# Function to process and save the received data
def process_and_save_data(data):
    # Decode data from bytes to string
    data_str = data.decode('utf-8')

    # Check if the data starts with 'UART:' and remove the prefix
    if data_str.startswith("UART:"):
        data_str = data_str[5:].strip()  # Remove the UART part and strip any extra spaces

    # Split the data into individual sensor readings using commas
    items = data_str.split(',')

    # Dictionary to store the sensor data
    sensor_data = {}
    for item in items:
        item = item.strip()  # Strip any leading/trailing spaces
        try:
            key, value = item.split(':', 1)  # Use a maximum of 1 split to handle cases with extra colons
            sensor_data[key.strip()] = value.strip()  # Ensure no extra spaces are included
        except ValueError:
            print(f"Skipping invalid item: {item}")

    # Print the sensor data for verification
    print(sensor_data)

    # Add the timestamp for when the data was received
    sensor_data['Timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Save the data to an Excel file
    try:
        # Attempt to read the existing data from the Excel file
        df = pd.read_excel('sensor_data.xlsx')
    except FileNotFoundError:
        # If the file doesn't exist, create an empty DataFrame
        df = pd.DataFrame()

    # Append the new sensor data to the DataFrame using _append
    df = df._append(sensor_data, ignore_index=True)

    # Save the updated DataFrame back to the Excel file
    df.to_excel('sensor_data.xlsx', index=False)
    print(f"Data saved to Excel at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Function to start the server and handle incoming connections
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 8081))  # Listen on port 8081
    server_socket.listen(1)
    print("Server is listening on port 8081...")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Connection established with {client_address}")
        data = client_socket.recv(1024)
        print(f"Received data: {data}")

        # Process the received data
        process_and_save_data(data)

        client_socket.close()

if __name__ == "__main__":
    start_server()
