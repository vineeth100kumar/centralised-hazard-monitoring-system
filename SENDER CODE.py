from machine import Pin, ADC, UART
import time

# Initialize UART0
uart = UART(0, baudrate=115200, tx=0, rx=1)  # Pin 0 for TX, Pin 1 for RX

# Initialize sensors
mq135 = ADC(Pin(27))  # MQ135 sensor connected to Pin 27
soil_moisture = ADC(Pin(26))  # Soil Moisture sensor connected to Pin 26
rain_sensor = ADC(Pin(28))  # Rain sensor connected to Pin 28

# Function to read sensor values
def read_sensors():
    mq135_value = mq135.read_u16()  # Use read_u16() to get ADC value
    soil_moisture_value = soil_moisture.read_u16()  # Use read_u16() to get ADC value
    rain_sensor_value = rain_sensor.read_u16()  # Use read_u16() to get ADC value
    return mq135_value, soil_moisture_value, rain_sensor_value

while True:
    # Read sensor values
    mq135_value, soil_moisture_value, rain_sensor_value = read_sensors()
    
    # Format data into a string
    data = f"MQ-135:{mq135_value}, Soil:{soil_moisture_value}, Rain:{rain_sensor_value}\n"
    
    # Send data over UART
    uart.write(data)
    
    # Wait before sending the next reading
    time.sleep(5)

