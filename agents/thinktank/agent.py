import logging
from typing import Dict, Any, Optional
from core.mattermost_client import MattermostClient
from core.llm_router import LLMRouter
from agents.thinktank.roles import detect_role, ROLES

logger = logging.getLogger("thinktank_agent")

class ThinkTankAgent:
    def __init__(self, client: MattermostClient, router: LLMRouter):
        self.client = client
        self.router = router
        self.channel_name = "think-tank"

    def should_handle(self, post: Dict[str, Any]) -> bool:
        """
        Determina si el agente de Think Tank debe procesar este mensaje.
        Interviene si:
        1. Se menciona explícitamente al bot o a cualquiera de sus 4 roles.
        2. O contiene alguno de los comandos clave (/challenge, /minuta, etc.).
        """
        msg = post.get("message", "").lower()
        
        # Menciones directas
        triggers = [
            f"@{self.client.bot_username}",
            "@thinktank",
            "@facilitador",
            "@abogado",
            "@abogado_diablo",
            "@redteam",
            "@literatura",
            "@papers",
            "@sintesis",
            "@minuta",
            "/challenge",
            "/scamper",
            "/sombrero",
            "/minuta"
        ]
        
        for t in triggers:
            if t in msg:
                return True
                
        return False

    async def handle_post(self, post: Dict[str, Any]):
        """
        Procesa el post, recupera el hilo completo, aplica el rol seleccionado y responde.
        """
        post_id = post.get("id")
        channel_id = post.get("channel_id")
        root_id = post.get("root_id") or post_id # Si no tiene root_id, este post es la raíz del hilo
        message_text = post.get("message", "")
        sender_id = post.get("user_id")
        sender_name = self.client.get_user_name(sender_id)

        logger.info(f"Procesando mensaje de @{sender_name} en post {post_id}: '{message_text[:60]}...'")

        # 1. Detectar qué rol fue convocado
        role = detect_role(message_text)
        role_name = role["name"]
        system_prompt = role["system_prompt"]

        # 2. Obtener el historial completo del hilo para memoria contextual viva
        thread_messages = self.client.get_thread_messages(root_id)
        if not thread_messages:
            thread_messages = [{"role": "user", "name": sender_name, "content": message_text}]

        # 3. Generar la respuesta dialéctica con LM Studio en la GPU local
        logger.info(f"Generando respuesta bajo el rol: {role_name}")
        reply_content = self.router.generate(
            messages=thread_messages,
            system_prompt=system_prompt,
            temperature=0.7
        )

        # 4. Formatear la respuesta con el membrete visual del rol
        formatted_reply = f"### {role_name}\n\n{reply_content}"

        # 5. Publicar en el hilo correspondiente
        try:
            self.client.create_post(
                channel_id=channel_id,
                message=formatted_reply,
                root_id=root_id
            )
            logger.info(f"Respuesta publicada exitosamente en el hilo {root_id}")
        except Exception as e:
            logger.error(f"Error publicando respuesta en Mattermost: {e}")
