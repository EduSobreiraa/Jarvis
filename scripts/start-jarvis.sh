#!/bin/zsh
set -u

ROOT="/Users/eduardopires/projetos/Jarvis"
LOG_DIR="$ROOT/data/logs"
URL="http://127.0.0.1:5176/"
mkdir -p "$LOG_DIR"

listening() {
  /usr/sbin/lsof -nP -t -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

if ! listening 11434; then
  /usr/bin/open -gj -a /Applications/Ollama.app
  for _ in {1..60}; do
    listening 11434 && break
    /bin/sleep 1
  done
  listening 11434 || { print -u2 "Ollama não iniciou. Confira se o app está instalado."; exit 1; }
fi

if ! listening 8765; then
  /usr/bin/nohup "$ROOT/.venv/bin/python" "$ROOT/main.py" >/dev/null 2>> "$LOG_DIR/backend.log" < /dev/null &
fi

if ! listening 5176; then
  /usr/bin/nohup /opt/homebrew/bin/npm --prefix "$ROOT/frontend" run dev -- --host 127.0.0.1 --port 5176 --strictPort >> "$LOG_DIR/frontend.log" 2>&1 < /dev/null &
fi

for _ in {1..120}; do
  if listening 8765 && listening 5176 && /usr/bin/curl --silent --fail --max-time 1 "$URL" >/dev/null; then
    /usr/bin/open "$URL"
    exit 0
  fi
  /bin/sleep 0.5
done

print -u2 "Jarvis não iniciou. Confira os registros em $LOG_DIR."
exit 1
