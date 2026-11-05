#!/usr/bin/env bash
# Gestor de servicio para Mattermost Agents Hub
BASE_DIR="/mnt/expansion/desplegados/mattermost-agents-hub"
PYTHON_BIN="/home/ambientesPy/revistaslatam/bin/python"
PID_FILE="$BASE_DIR/.hub.pid"
LOG_FILE="$BASE_DIR/hub.log"

start() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "El Hub ya está corriendo con PID $PID"
            return 0
        fi
    fi
    echo "Iniciando Mattermost Agents Hub..."
    nohup "$PYTHON_BIN" "$BASE_DIR/main.py" </dev/null >> "$LOG_FILE" 2>&1 &
    PID=$!
    disown $PID 2>/dev/null || true
    echo $PID > "$PID_FILE"
    sleep 2
    if kill -0 "$PID" 2>/dev/null; then
        echo "✅ Hub iniciado exitosamente con PID $PID (Logs en $LOG_FILE)"
    else
        echo "❌ Error al iniciar el Hub. Revisa $LOG_FILE"
        exit 1
    fi
}

stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        echo "Deteniendo Mattermost Agents Hub (PID $PID)..."
        kill -15 "$PID" 2>/dev/null || true
        sleep 2
        kill -9 "$PID" 2>/dev/null || true
        rm -f "$PID_FILE"
        echo "✅ Hub detenido."
    else
        echo "El Hub no está en ejecución."
    fi
}

status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "🟢 Mattermost Agents Hub está ONLINE (PID $PID)"
            return 0
        fi
    fi
    echo "🔴 Mattermost Agents Hub está STOPPED"
}

logs() {
    tail -n 50 -f "$LOG_FILE"
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        start
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    *)
        echo "Uso: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
