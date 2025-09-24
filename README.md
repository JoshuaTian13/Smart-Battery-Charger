# Smart Battery Charger

An IoT-enabled charging system for lithium batteries, combining embedded sensing, real-time telemetry, and cloud-based optimization.  
Hardware and core functionality are complete.  
This GitHub repo is a **work in progress** — code and detailed documentation are being cleaned up and added.  

---

## Overview of Subsystems

### Embedded Hardware & Firmware
- Custom PCB built around ESP32  
- INA219 sensor for current/voltage monitoring  
- DS18B20 sensor for temperature tracking  
- Arduino C++ firmware streams sensor data for telemetry  

### Cloud Telemetry
- Data pipeline planned via **AWS IoT Core**  
- Storage with **DynamoDB**  
- Real-time query and visualization supported  

### Optimization / ML
- Initial experiments in **AWS SageMaker** to predict battery health and optimize charging profiles  

### Dashboard
- Prototype **React.js web interface** for visualization of voltage, current, and temperature trends  

---

## Repository Status
- Hardware + firmware: functional  
- Cloud integration: prototype tested, docs in progress  
- Dashboard: prototype running, code cleanup pending  
- Repo documentation: ongoing (expect updates soon)  

---

## 📌 Future Vision
- Multi-cell battery pack support  
- Mobile alerts and visualization  
- Advanced ML for predictive maintenance  
