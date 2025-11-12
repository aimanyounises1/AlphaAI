#!/bin/bash

# Prompt for API base
read -p "Enter the API base URL (e.g., http://localhost:11434): " API_BASE

# Prompt for model name
read -p "Enter the model name (e.g., ollama/mistral-large:latest): " MODEL_NAME

# Print the entered values for confirmation
echo "API Base: $API_BASE"
echo "Model Name: $MODEL_NAME"
read -p "Is this correct? (y/n): " CONFIRM

if [[ $CONFIRM != "y" && $CONFIRM != "Y" ]]; then
    echo "Aborted. Please run the script again with the correct parameters."
    exit 1
fi


# Start litellm
litellm --model $MODEL_NAME \
        --api_base $API_BASE \
        --host 0.0.0.0 \
        --port 8001 \
        --detailed_debug &

# Start chainlit
chainlit run appUI.py --host 0.0.0.0 --port 8002 &

# Wait for both processes to complete
wait
