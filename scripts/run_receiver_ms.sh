#!/bin/bash
source .venv/Scripts/activate
export SERVICE_TYPE=RECEIVER
python -m modules.microservice.main
deactivate
