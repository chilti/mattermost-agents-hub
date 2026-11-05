import datetime
from typing import Dict, Any, List, Optional
from .client import MattermostClient

# Cache de usuarios {user_id: username} para no saturar la API
_USER_CACHE: Dict[str, str] = {}

def _resolve_username(client: MattermostClient, user_id: str, token: Optional[str] = None) -> str:
    if not user_id:
        return "system"
    if user_id in _USER_CACHE:
        return _USER_CACHE[user_id]
    try:
        user_info = client.get(f"/users/{user_id}", override_token=token)
        uname = user_info.get("username", user_id)
        _USER_CACHE[user_id] = uname
        return uname
    except Exception:
        return user_id

def mattermost_get_my_profile(user_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Obtiene la identidad del usuario actual autenticado con el que opera el agente.
    Permite verificar qué cuenta (ej. jlja, hcarrillo, etc.) se está usando.
    """
    client = MattermostClient()
    user = client.get("/users/me", override_token=user_token)
    return {
        "id": user.get("id"),
        "username": user.get("username"),
        "email": user.get("email"),
        "first_name": user.get("first_name"),
        "last_name": user.get("last_name"),
        "nickname": user.get("nickname"),
        "roles": user.get("roles")
    }

def mattermost_list_my_teams(user_token: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Lista todos los Teams (equipos de trabajo) en los que participa el usuario autenticado.
    Retorna el ID, nombre interno y nombre para mostrar de cada Team.
    """
    client = MattermostClient()
    teams = client.get("/users/me/teams", override_token=user_token)
    return [
        {
            "id": t.get("id"),
            "name": t.get("name"),
            "display_name": t.get("display_name"),
            "description": t.get("description")
        }
        for t in teams
    ]

def mattermost_list_my_channels(
    team_name_or_id: Optional[str] = None,
    user_token: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Lista todos los canales (públicos y privados) a los que tiene acceso el usuario.
    Si se especifica team_name_or_id, lista los canales de ese Team específico.
    """
    client = MattermostClient()
    
    # Si no se pasó equipo, buscar en el primer equipo del usuario o listar todos
    if not team_name_or_id:
        teams = client.get("/users/me/teams", override_token=user_token)
        if not teams:
            return []
        team_id = teams[0].get("id")
    else:
        # Resolver si es nombre o ID
        if len(team_name_or_id) == 26:
            team_id = team_name_or_id
        else:
            team_info = client.get(f"/teams/name/{team_name_or_id}", override_token=user_token)
            team_id = team_info.get("id")

    channels = client.get(f"/users/me/teams/{team_id}/channels", override_token=user_token)
    result = []
    for c in channels:
        result.append({
            "id": c.get("id"),
            "team_id": c.get("team_id"),
            "name": c.get("name"),
            "display_name": c.get("display_name"),
            "type": "public" if c.get("type") == "O" else ("private" if c.get("type") == "P" else "direct"),
            "purpose": c.get("purpose"),
            "header": c.get("header"),
            "total_msg_count": c.get("total_msg_count")
        })
    return result

def mattermost_get_channel_by_name(
    team_name: str,
    channel_name: str,
    user_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Obtiene la información y el ID de un canal a partir del nombre del equipo y el nombre del canal.
    Ejemplo: team_name="thinktank", channel_name="think-tank".
    """
    client = MattermostClient()
    c = client.get(f"/teams/name/{team_name}/channels/name/{channel_name}", override_token=user_token)
    return {
        "id": c.get("id"),
        "name": c.get("name"),
        "display_name": c.get("display_name"),
        "type": c.get("type"),
        "purpose": c.get("purpose"),
        "header": c.get("header")
    }

def mattermost_get_channel_posts(
    channel_id: str,
    limit: int = 30,
    user_token: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Obtiene los mensajes más recientes de un canal ordenados cronológicamente.
    Permite al agente leer lo discutido en una sesión de think tank o canal de proyecto.
    """
    client = MattermostClient()
    res = client.get(f"/channels/{channel_id}/posts", params={"per_page": limit}, override_token=user_token)
    
    order = res.get("order", [])
    posts_map = res.get("posts", {})
    
    formatted_posts = []
    for pid in reversed(order):
        p = posts_map.get(pid, {})
        uid = p.get("user_id")
        author = _resolve_username(client, uid, user_token)
        
        # Convertir timestamp milisegundos a fecha legible
        create_ts = p.get("create_at", 0) / 1000.0
        dt_str = datetime.datetime.fromtimestamp(create_ts).strftime("%Y-%m-%d %H:%M:%S") if create_ts else "N/A"
        
        formatted_posts.append({
            "id": p.get("id"),
            "user_id": uid,
            "author": author,
            "timestamp": dt_str,
            "message": p.get("message"),
            "root_id": p.get("root_id", ""),
            "reply_count": p.get("reply_count", 0),
            "is_pinned": p.get("is_pinned", False)
        })
    return formatted_posts

def mattermost_get_thread(
    post_id: str,
    user_token: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Obtiene el hilo completo de discusión que cuelga de un mensaje raíz (post_id).
    Ideal para que el agente examine a fondo un debate específico, objeciones y propuestas.
    """
    client = MattermostClient()
    res = client.get(f"/posts/{post_id}/thread", override_token=user_token)
    
    order = res.get("order", [])
    posts_map = res.get("posts", {})
    
    thread_posts = []
    for pid in reversed(order):
        p = posts_map.get(pid, {})
        uid = p.get("user_id")
        author = _resolve_username(client, uid, user_token)
        create_ts = p.get("create_at", 0) / 1000.0
        dt_str = datetime.datetime.fromtimestamp(create_ts).strftime("%Y-%m-%d %H:%M:%S") if create_ts else "N/A"
        
        thread_posts.append({
            "id": p.get("id"),
            "author": author,
            "timestamp": dt_str,
            "message": p.get("message"),
            "root_id": p.get("root_id", "")
        })
    return thread_posts

def mattermost_create_post(
    channel_id: str,
    message: str,
    root_id: Optional[str] = None,
    user_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Publica un nuevo mensaje en un canal o responde dentro de un hilo específico.
    Se publica automáticamente en nombre del usuario correspondiente al token (ej. jlja o hcarrillo).
    
    Args:
        channel_id: El ID del canal donde se publicará.
        message: El texto del mensaje (soporta Markdown completo y fórmulas).
        root_id: ID del post raíz si es una respuesta en un hilo (dejar None para mensaje nuevo en el canal).
        user_token: Token de usuario opcional para publicar como un usuario específico.
    """
    client = MattermostClient()
    payload: Dict[str, Any] = {
        "channel_id": channel_id,
        "message": message
    }
    if root_id:
        payload["root_id"] = root_id

    res = client.post("/posts", payload, override_token=user_token)
    return {
        "id": res.get("id"),
        "channel_id": res.get("channel_id"),
        "root_id": res.get("root_id"),
        "message": res.get("message"),
        "create_at": res.get("create_at")
    }

def mattermost_search_posts(
    terms: str,
    team_id: Optional[str] = None,
    user_token: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Busca mensajes en el historial de Mattermost por términos clave o conceptos.
    """
    client = MattermostClient()
    
    # Obtener el team si no se provee
    if not team_id:
        teams = client.get("/users/me/teams", override_token=user_token)
        if not teams:
            return []
        team_id = teams[0].get("id")

    payload = {
        "terms": terms,
        "is_or_search": False
    }
    res = client.post(f"/teams/{team_id}/posts/search", payload, override_token=user_token)
    
    order = res.get("order", [])
    posts_map = res.get("posts", {})
    
    results = []
    for pid in order:
        p = posts_map.get(pid, {})
        uid = p.get("user_id")
        author = _resolve_username(client, uid, user_token)
        results.append({
            "id": p.get("id"),
            "channel_id": p.get("channel_id"),
            "author": author,
            "message": p.get("message"),
            "root_id": p.get("root_id", "")
        })
    return results
