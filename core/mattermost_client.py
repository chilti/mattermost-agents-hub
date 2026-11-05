import os
import json
import time
import asyncio
import logging
import requests
from typing import Dict, Any, List, Optional, Callable
from core.config import (
    MATTERMOST_URL,
    MATTERMOST_WS_URL,
    MATTERMOST_HOST_HEADER,
    MATTERMOST_BOT_TOKEN,
    MATTERMOST_BOT_USERNAME
)

logger = logging.getLogger("mattermost_client")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

class MattermostClient:
    def __init__(self, token: Optional[str] = None):
        self.api_url = f"{MATTERMOST_URL}/api/v4"
        self.ws_url = MATTERMOST_WS_URL
        self.token = token or MATTERMOST_BOT_TOKEN
        self.host_header = MATTERMOST_HOST_HEADER
        self.bot_username = MATTERMOST_BOT_USERNAME
        self._user_cache: Dict[str, str] = {}
        self.bot_user_id = self._get_my_id()

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Host": self.host_header,
            "X-Forwarded-Proto": "https"
        }

    def _get_my_id(self) -> str:
        try:
            r = requests.get(f"{self.api_url}/users/me", headers=self._headers(), timeout=10)
            if r.status_code == 200:
                uid = r.json().get("id", "")
                self._user_cache[uid] = self.bot_username
                return uid
        except Exception as e:
            logger.warning(f"No se pudo obtener el ID del bot: {e}")
        return ""

    def get_user_name(self, user_id: str) -> str:
        if not user_id:
            return "system"
        if user_id in self._user_cache:
            return self._user_cache[user_id]
        try:
            r = requests.get(f"{self.api_url}/users/{user_id}", headers=self._headers(), timeout=10)
            if r.status_code == 200:
                uname = r.json().get("username", user_id)
                self._user_cache[user_id] = uname
                return uname
        except Exception:
            pass
        return user_id

    def get_my_channels(self) -> List[Dict[str, Any]]:
        """
        Obtiene los canales en los que está inscrito el bot.
        """
        try:
            r = requests.get(f"{self.api_url}/users/me/channels", headers=self._headers(), timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            logger.error(f"Error listando canales: {e}")
        return []

    def get_thread_messages(self, post_id: str) -> List[Dict[str, str]]:
        """
        Recupera el historial cronológico completo de un hilo como mensajes de chat.
        Formato: [{"role": "user", "name": "hcarrillo", "content": "..."}]
        """
        url = f"{self.api_url}/posts/{post_id}/thread"
        resp = requests.get(url, headers=self._headers(), timeout=15)
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        order = data.get("order", [])
        posts_map = data.get("posts", {})
        
        history = []
        for pid in reversed(order):
            p = posts_map.get(pid, {})
            uid = p.get("user_id")
            uname = self.get_user_name(uid)
            msg = p.get("message", "").strip()
            if not msg:
                continue
            
            # Si el autor es el bot mismo, role=assistant; si es un humano, role=user con su name
            role = "assistant" if uname == self.bot_username else "user"
            history.append({
                "role": role,
                "name": uname,
                "content": msg
            })
        return history

    def create_post(
        self,
        channel_id: str,
        message: str,
        root_id: Optional[str] = None,
        file_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Publica un mensaje en un canal o responde dentro de un hilo.
        """
        url = f"{self.api_url}/posts"
        payload = {
            "channel_id": channel_id,
            "message": message
        }
        if root_id:
            payload["root_id"] = root_id
        if file_ids:
            payload["file_ids"] = file_ids

        headers = self._headers()
        headers["Content-Type"] = "application/json"
        
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        return resp.json()

    def upload_file(self, channel_id: str, file_path: str) -> Optional[str]:
        """
        Sube un archivo (PDF, HTML, PNG, CSV) a Mattermost y retorna el file_id.
        """
        if not os.path.exists(file_path):
            logger.error(f"Archivo no encontrado: {file_path}")
            return None
        
        url = f"{self.api_url}/files"
        filename = os.path.basename(file_path)
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Host": self.host_header,
            "X-Forwarded-Proto": "https"
        }
        
        with open(file_path, "rb") as f:
            files = {"files": (filename, f)}
            data = {"channel_id": channel_id}
            resp = requests.post(url, headers=headers, files=files, data=data, timeout=60)
            
        if resp.status_code in [200, 201]:
            file_infos = resp.json().get("file_infos", [])
            if file_infos:
                return file_infos[0].get("id")
        logger.error(f"Error subiendo archivo {file_path}: {resp.text}")
        return None

    async def start_listening(self, on_message_callback: Callable[[Dict[str, Any]], Any]):
        """
        Inicia un bucle de escucha continuo ultrarrápido y robusto (cada 2 segundos)
        sobre los canales del bot en Mattermost. Cero dependencias frágiles de proxies o CORS.
        """
        logger.info(f"Iniciando escucha activa de canales de Mattermost para @{self.bot_username}...")
        
        # Registrar el timestamp actual para no procesar mensajes pasados
        last_processed_timestamp = int(time.time() * 1000)
        processed_post_ids = set()

        # Precargar los últimos posts existentes para marcarlos como ya vistos
        channels = self.get_my_channels()
        for ch in channels:
            cid = ch.get("id")
            try:
                r = requests.get(f"{self.api_url}/channels/{cid}/posts?per_page=10", headers=self._headers(), timeout=10)
                if r.status_code == 200:
                    for pid in r.json().get("order", []):
                        processed_post_ids.add(pid)
            except Exception:
                pass

        logger.info(f"✅ Escucha activa iniciada en {len(channels)} canales. Monitoreando mensajes...")

        while True:
            try:
                # Revisar canales del bot
                channels = self.get_my_channels()
                for ch in channels:
                    cid = ch.get("id")
                    cname = ch.get("name")
                    
                    # Traer posts recientes
                    r = requests.get(
                        f"{self.api_url}/channels/{cid}/posts?since={last_processed_timestamp - 5000}",
                        headers=self._headers(),
                        timeout=10
                    )
                    
                    if r.status_code == 200:
                        data = r.json()
                        posts_map = data.get("posts", {})
                        order = data.get("order", [])
                        
                        # Procesar en orden cronológico
                        for pid in reversed(order):
                            if pid in processed_post_ids:
                                continue
                            
                            p = posts_map.get(pid, {})
                            create_at = p.get("create_at", 0)
                            uid = p.get("user_id")
                            
                            # Ignorar si es el propio bot
                            if uid == self.bot_user_id:
                                processed_post_ids.add(pid)
                                continue
                                
                            # Procesar el nuevo post
                            processed_post_ids.add(pid)
                            if create_at > last_processed_timestamp:
                                last_processed_timestamp = create_at
                                
                            logger.info(f"🔔 Nuevo post detectado en #{cname} (ID: {pid})")
                            asyncio.create_task(on_message_callback(p))

                # Pausa de 2 segundos antes del siguiente sondeo
                await asyncio.sleep(2)

            except Exception as e:
                logger.warning(f"Error en bucle de sondeo: {e}. Reintentando en 3s...")
                await asyncio.sleep(3)
