import time
import wifi
import socketpool
import board
import busio
from analogio import AnalogIn
import adafruit_dht
import displayio
from adafruit_st7735r import ST7735R
from adafruit_display_text import label
import terminalio
import pwmio
import adafruit_vl53l0x

# Wi-Fi Credentials
SSID = "DIR-825"
PASSWORD = "01424959"

# Server Details
SERVER_IP = "192.168.1.129"  # Replace with your laptop's IP address
SERVER_PORT = 8081

# Initialize UART0 on GPIO pins 0 (TX) and 1 (RX)
uart = busio.UART(board.GP0, board.GP1, baudrate=115200)

# Initialize sensors
mq7 = AnalogIn(board.GP26)  # MQ-7 sensor connected to Pin GP26
flame_sensor = AnalogIn(board.GP27)  # Flame sensor connected to Pin GP27
dht11 = adafruit_dht.DHT11(board.GP15)  # DHT11 sensor connected to Pin GP15

# Initialize I2C bus for VL53L0X sensor
i2c = busio.I2C(board.GP5, board.GP4)  # SCL = GP5, SDA = GP4
vl53 = adafruit_vl53l0x.VL53L0X(i2c)  # Initialize VL53L0X sensor

# Define pins for SPI and display control
mosi_pin = board.GP19
clk_pin = board.GP18
reset_pin = board.GP22
cs_pin = board.GP17
dc_pin = board.GP21
led_pin = board.GP20

# Initialize PWM for backlight control
pwm = pwmio.PWMOut(led_pin, frequency=5000)
pwm.duty_cycle = 65535

# Release any previously initialized displays
displayio.release_displays()

# Initialize SPI bus and display bus
spi = busio.SPI(clock=clk_pin, MOSI=mosi_pin)
display_bus = displayio.FourWire(spi, command=dc_pin, chip_select=cs_pin, reset=reset_pin)

# Initialize the display
display = ST7735R(display_bus, width=128, height=160, bgr=True)

# Create a display group
splash = displayio.Group()
display.root_group = splash

# Set background color
color_bitmap = displayio.Bitmap(128, 160, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0x0000FF  # Blue
bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)

# Draw the "HELLO WORLD" text
text_group = displayio.Group(scale=1, x=0, y=70)
text_area = label.Label(terminalio.FONT, text="Connecting to Wi-Fi...", color=0xFFFFFF)
text_group.append(text_area)
splash.append(text_group)
display.refresh()

# Clear the text after Wi-Fi connection
def clear_display():
    while len(splash) > 1:
        splash.pop()

# Parse UART data
def parse_uart_data(uart_data):
    try:
        uart_data_str = uart_data.decode('utf-8').strip()
        print(f"Raw UART data: {uart_data_str}")  # Debugging line

        sensor_data = {}
        items = uart_data_str.split(',')

        for item in items:
            item = item.strip()
            try:
                key, value = item.split(':', 1)
                sensor_data[key.strip()] = int(value.strip())
            except ValueError:
                print(f"Skipping invalid item: {item}")

        print(f"Parsed UART data: {sensor_data}")  # Debugging line
        return sensor_data
    except Exception as e:
        print(f"Error parsing UART data: {e}")
        return {}

# Connect to Wi-Fi
def connect_wifi():
    print("Connecting to Wi-Fi...")
    wifi.radio.connect(SSID, PASSWORD)
    print(f"Connected to Wi-Fi: {wifi.radio.ipv4_address}")

# Read sensor values
def read_sensors():
    mq7_value = mq7.value
    flame_value = flame_sensor.value
    try:
        temperature = dht11.temperature
        humidity = dht11.humidity
    except RuntimeError:
        temperature = None
        humidity = None
    return mq7_value, flame_value, temperature, humidity

# Send data to server
def send_data(data):
    pool = socketpool.SocketPool(wifi.radio)
    client_socket = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
    client_socket.connect((SERVER_IP, SERVER_PORT))
    client_socket.send(data.encode('utf-8'))
    client_socket.close()
    print("Data sent to server.")

# Main function
def main():
    connect_wifi()
    clear_display()
    time.sleep(1)

    y_offset = 10
    while True:
        mq7_value, flame_value, temperature, humidity = read_sensors()
        print(f"MQ7: {mq7_value}, Flame: {flame_value}, Temp: {temperature}, Humidity: {humidity}")  # Debugging line

        uart_data = None
        if uart.in_waiting > 0:
            uart_data = uart.read(128)
        if(uart_data == None):
            time.sleep(2)

        uart_sensor_data = parse_uart_data(uart_data) if uart_data else {}

        # Get water level from VL53L0X sensor (distance converted to water level)
        water_level = vl53.range  # Read distance in millimeters
        print(f"Water Level: {water_level} mm")

        text_lines = [
            f"MQ7: {mq7_value}",
            f"Flame: {flame_value}",
            f"Temp: {temperature if temperature is not None else 'N/A'}",
            f"Humidity: {humidity if humidity is not None else 'N/A'}",
            f"Water Level: {water_level} mm"  # Update distance to water level
        ]

        for key, value in uart_sensor_data.items():
            text_lines.append(f"{key}: {value}")

        while len(splash) > 1:
            splash.pop()

        for i, line in enumerate(text_lines):
            text_group = displayio.Group(scale=1, x=10, y=y_offset + i * 12)
            text_area = label.Label(terminalio.FONT, text=line, color=0xFFFFFF)
            text_group.append(text_area)
            splash.append(text_group)

        data_payload = ', '.join(text_lines)
        send_data(data_payload)

        time.sleep(4)

if __name__ == "__main__":
    main()
