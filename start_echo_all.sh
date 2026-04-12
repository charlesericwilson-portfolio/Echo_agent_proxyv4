#!/bin/bash
# start_echo_all.sh - Starts all Echo services

echo "=== Starting Echo Agent System ==="

# Activate venv
source ~/echo_env/bin/activate
echo "Venv activated."

# 1. Start Orchestrator (main brain connector)
echo "Starting Orchestrator on port 8000..."
konsole -e bash -c "cd ~/Echo_agent_proxy && python -m src.orchestrator.main; exec bash" &

sleep 2

# 2. Start Main 14B Model (Echo)
echo "Starting Echo on port 8080..."
konsole -e bash -c "
cd ~
echo '=== Echo 14B Model Starting ==='
echo 'Model: /path'
./llama.cpp/build/bin/llama-server \
  --model '/path' \
  --ctx-size 65000 \
  --n-gpu-layers 99 \
  --port 8080 \
  --host 0.0.0.0 \
  --keep 8000 \
  --rope-scaling yarn \
  --yarn-orig-ctx 65000 \
  --yarn-ext-factor 4.0 \
  --rope-freq-base 1000000 \
  --mmap \
  --repeat-penalty 1.13 \
  --flash-attn on \
  --temp 0.3
echo '14B Model stopped.'
read -p 'Press Enter to close...'
" &

sleep 3

# 3. Start Summarizer 3B Model
echo "Starting Summarizer 3B Model on port 8082..."
konsole -e bash -c "
cd ~
echo '=== Summarizer 3B Model Starting ==='
echo 'Model: /path'
./llama.cpp/build/bin/llama-server \
  --model '/path' \
  --ctx-size 10000 \
  --n-gpu-layers 99 \
  --port 8082 \
  --host 0.0.0.0 \
  --temp 0.3
echo 'Summarizer stopped.'
read -p 'Press Enter to close...'
" &

echo "=== All services launched ==="
echo "Orchestrator → http://localhost:8000"
echo "Main Echo 14B   → http://localhost:8080"
echo "Summarizer 3B   → http://localhost:8082"
echo ""
echo "Keep this terminal open or minimize it."
echo "Use your wrapper in another terminal for chatting with Echo."
