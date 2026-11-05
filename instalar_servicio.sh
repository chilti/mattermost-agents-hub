#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="mattermost-agents-hub"
SERVICE_SRC="/mnt/expansion/desplegados/mattermost-agents-hub/mattermost-agents-hub.service"
SERVICE_DST="/etc/systemd/system/${SERVICE_NAME}.service"

if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Por favor ejecuta este script con sudo: sudo $0"
    exit 1
fi

echo "==> Copiando archivo de servicio a /etc/systemd/system/..."
cp "$SERVICE_SRC" "$SERVICE_DST"
chmod 644 "$SERVICE_DST"

echo "==> Recargando systemd daemon..."
systemctl daemon-reload

echo "==> Habilitando servicio para arranque automático..."
systemctl enable "${SERVICE_NAME}.service"

echo "==> Iniciando servicio ${SERVICE_NAME}..."
systemctl restart "${SERVICE_NAME}.service"

echo "==> Estado del servicio:"
systemctl status "${SERVICE_NAME}.service" --no-pager
