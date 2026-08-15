# Repository scope

This repository is a portfolio implementation based on the completed Smart Battery Charger's established hardware and cloud architecture. The original custom-PCB manufacturing files, credentials, AWS account resources, and complete historical source were not available for publication.

The ESP32 control core, cloud handlers, infrastructure template, machine-learning workflow, dashboard, tests, and documentation in this repository were written as a coherent reviewable implementation. They are not presented as untouched historical commits.

This project is an engineering prototype, not a certified battery-management or charging product. A dedicated charger/power-stage IC must enforce cell-chemistry limits independently of the ESP32 and cloud software. Do not connect this code directly to an unprotected lithium cell.
