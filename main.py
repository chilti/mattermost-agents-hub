#!/usr/bin/env python3
"""
Mattermost Agents Hub - Demonio Central de Agentes de IA
Gestiona la escucha en tiempo real de Mattermost y despacha eventos
a los agentes especializados (Think Tank, Vigilancia, Editorial, etc.).
"""

import sys
import os
import signal
import asyncio
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from core.mattermost_client import MattermostClient
from core.llm_router import LLMRouter
from agents.thinktank.agent import ThinkTankAgent

logger = logging.getLogger("mattermost_agents_hub")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

async def main():
    logger.info("=" * 65)
    logger.info("  🚀 INICIANDO MATTERMOST AGENTS HUB (Laboratorio C3 / UNAM)")
    logger.info("=" * 65)

    client = MattermostClient()
    router = LLMRouter()

    # -------------------------------------------------------------
    # REGISTRO DE AGENTES ACTIVOS
    # -------------------------------------------------------------
    thinktank_agent = ThinkTankAgent(client, router)
    registered_agents = [
        thinktank_agent
        # Aquí se agregarán futuros agentes:
        # surveillance_agent,
        # editorial_agent,
        # project_tracker_agent
    ]

    logger.info(f"Agentes activos registrados: {[a.__class__.__name__ for a in registered_agents]}")

    # Callback central de eventos de Mattermost
    async def dispatch_message(post: dict):
        for agent in registered_agents:
            try:
                if agent.should_handle(post):
                    await agent.handle_post(post)
            except Exception as e:
                logger.error(f"Error en despachador de agente {agent.__class__.__name__}: {e}")

    # Iniciar bucle de escucha WebSocket continuo
    await client.start_listening(dispatch_message)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Demonio detenido por el usuario.")
