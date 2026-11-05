import os
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from core.config import LM_STUDIO_URL, LM_STUDIO_API_KEY, LM_STUDIO_MODEL

logger = logging.getLogger("llm_router")

class LLMRouter:
    def __init__(self):
        self.client_local = OpenAI(
            base_url=LM_STUDIO_URL,
            api_key=LM_STUDIO_API_KEY
        )
        self.default_model = LM_STUDIO_MODEL

    def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1500
    ) -> str:
        """
        Genera una respuesta utilizando el modelo local de LM Studio (RTX 4090).
        """
        formatted_messages = [{"role": "system", "content": system_prompt}]
        
        # Inyectar el historial de mensajes
        for m in messages:
            content = m.get("content", "")
            name = m.get("name")
            role = m.get("role", "user")
            
            # Si tiene nombre de autor humano, anteponerlo para que el modelo sepa quién habló
            if name and role == "user":
                content = f"[{name}]: {content}"
                
            formatted_messages.append({"role": role, "content": content})

        try:
            response = self.client_local.chat.completions.create(
                model=self.default_model,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            choice = response.choices[0]
            answer = choice.message.content or ""
            # Si el modelo tiene razonamiento o cadena de pensamiento separada
            if not answer and hasattr(choice.message, "reasoning") and choice.message.reasoning:
                answer = choice.message.reasoning
            return answer.strip()

        except Exception as e:
            logger.error(f"Error generando con LM Studio: {e}")
            return f"⚠️ Error al conectar con el motor local de IA (LM Studio): {e}"
