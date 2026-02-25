#!/bin/bash
source .venv/Scripts/activate
export SERVICE_TYPE=EMITTER
python -m modules.microservice.main
deactivate
