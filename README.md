# Centralized Hazard Detection System

This repository contains the code and documentation for a real-time hazard detection system that monitors floods, fires, and air quality. The system uses multiple sensors, including MQ-7, MQ-135, DHT11, analog rain and soil moisture sensors, and an IR sensor for flame detection.

Key Features:
	•	Dual Microcontroller Setup: Raspberry Pi Pico collects sensor data, while Raspberry Pi Pico 2W transmits it wirelessly.
	•	Real-Time Monitoring: Data is displayed on an LCD-TFT and sent to an Excel sheet, which updates a web dashboard.
	•	Communication: UART between the two Raspberry Pis, with wireless transmission to a laptop.
	•	Custom Hardware Design: Chassis designed in SOLIDWORKS and laser-cut from acrylic.

This project was developed as part of an experiential learning initiative to integrate embedded systems, sensor networks, and real-time data visualization. 🚀
