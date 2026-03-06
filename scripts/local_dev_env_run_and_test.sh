#!/bin/bash

# run services
source scripts/run_emitter_ms.sh > logs/emitter.log 2>&1 &
source scripts/run_receiver_ms.sh > logs/receiver.log 2>&1 &
sleep 3

# run test
python -m tests.system.test_microservice

# shut down
curl -s http://127.0.0.1:8001/stop > /dev/null
curl -s http://127.0.0.1:8002/stop > /dev/null

# wait for end of subprocesses
wait
