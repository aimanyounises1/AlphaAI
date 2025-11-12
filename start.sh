#!/bin/bash

# Start litellm
litellm --model ollama/mistral-large:latest \
        --api_base http://10.20.232.13:11434 \
        --host 10.20.232.13 \
        --port 8001 \
        --detailed_debug &

# Start chainlit
chainlit run /app/app.py --host 0.0.0.0 --port 8002 &

# Wait for both processes to complete
wait
