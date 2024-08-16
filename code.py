# SPDX-FileCopyrightText: 2022 Liz Clark for Adafruit Industries
# SPDX-License-Identifier: MIT

import os
import time
import ssl
import wifi
import socketpool
import microcontroller
import board
import adafruit_requests
import adafruit_dht
from adafruit_io.adafruit_io import IO_HTTP, AdafruitIO_RequestError
import analogio
import digitalio

# Connect to Wi-Fi
wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'), os.getenv('CIRCUITPY_WIFI_PASSWORD'))

# Retrieve Adafruit IO credentials from environment variables
aio_username = os.getenv('aio_username')
aio_key = os.getenv('aio_key')

# Initialize socket pool and Adafruit Requests session
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

# Initialize Adafruit IO HTTP API object
io = IO_HTTP(aio_username, aio_key, requests)
print("Connected to Adafruit IO")

# Initialize DHT11 sensor (using GPIO 16 for data)
dht_device = adafruit_dht.DHT11(board.GP16)  # Use board.GP16 for GPIO 16

# Initialize sound sensor
sound_analog = analogio.AnalogIn(board.GP26)
sound_digital = digitalio.DigitalInOut(board.GP6)
sound_digital.direction = digitalio.Direction.INPUT

# Manage feeds
try:
    picowTemp_feed = io.get_feed("pitemp")
    picowHumid_feed = io.get_feed("pihumid")
    soundAnalog_feed = io.get_feed("soundanalog")
    soundDigital_feed = io.get_feed("sounddigital")
except AdafruitIO_RequestError:
    picowTemp_feed = io.create_new_feed("pitemp")
    picowHumid_feed = io.create_new_feed("pihumid")
    soundAnalog_feed = io.create_new_feed("soundanalog")
    soundDigital_feed = io.create_new_feed("sounddigital")

feed_names = [picowTemp_feed, picowHumid_feed, soundAnalog_feed, soundDigital_feed]
print("Feeds created")

clock = 10

def read_analog(pin):
    return (pin.value * 3.3) / 65536  # Convert the analog value to voltage

while True:
    try:
        if clock > 10:
            # Read temperature and humidity from DHT11 sensor
            temperature = dht_device.temperature
            humidity = dht_device.humidity
            
            # Read analog and digital values from the sound sensor
            sound_analog_value = read_analog(sound_analog)
            sound_digital_value = sound_digital.value
            
            # Check if readings are valid
            if temperature is not None and humidity is not None:
                data = [temperature, humidity, sound_analog_value]
                for z in range(4):
                    io.send_data(feed_names[z]["key"], data[z])
                    print(f"Sent {data[z]:0.2f} to feed '{feed_names[z]['name']}'")
                    time.sleep(1)
                
                # Print sensor data to the REPL
                print(f"\nTemperature: {temperature:0.1f} C")
                print(f"Humidity: {humidity:0.1f} %")
                print(f"Sound Analog: {sound_analog_value:0.2f} V")
                print(f"Sound Digital: {sound_digital_value}")
                print()
            else:
                print("Failed to retrieve data from sensor")
            
            # Reset clock
            clock = 0
        else:
            clock += 1
    except Exception as e:
        print("Error:\n", str(e))
        print("Resetting microcontroller in 10 seconds")
        time.sleep(10)
        microcontroller.reset()
    
    # Delay and print clock value
    time.sleep(1)
    print(clock)
