# 🚀 Mattermost Agents Hub

Plataforma extensible y modular para hospedar y coordinar agentes de inteligencia artificial colaborativos dentro de **Mattermost**. Diseñado específicamente para entornos académicos, grupos de investigación científica y dinámicas de *think tank*.

---

## 🏛️ Arquitectura

El Hub desacopla la fontanería de red y transporte de la lógica específica de cada agente:

```
mattermost-agents-hub/
├── core/                        # FONTANERÍA TÉCNICA COMPARTIDA
│   ├── config.py                # Carga de credenciales y variables de entorno
│   ├── mattermost_client.py     # Escucha adaptativa, memoria de hilos y subida de archivos
│   └── llm_router.py            # Enrutador híbrido: Inferencia local (LM Studio / GPU) + Cloud
│
├── agents/                      # CATÁLOGO DE AGENTES POR CASO DE USO
│   └── thinktank/               # Agente 1: Think Tank de Investigación
│       ├── roles.py             # Roles dialécticos (Facilitador, Abogado, Literatura, Síntesis)
│       └── agent.py             # Detección de intenciones, contexto y respuestas
│
├── main.py                      # Despachador de eventos y punto de entrada único
└── hub_daemon.sh                # Script de control (start / stop / restart / status / logs)
```

---

## 🎭 Agentes Implementados

### 1. Think Tank Agent (`#think-tank`)
Asume 4 roles epistemológicos y dialécticos según la necesidad del debate:

* **🎭 Facilitador de Ideación (`@facilitador`, `/sombrero`, `/scamper`):** Estimula el pensamiento lateral, dinámicas de los Seis Sombreros de De Bono y analogías interdisciplinarias.
* **😈 Abogado del Diablo (`@abogado`, `/challenge`):** Red-teaming metodológico riguroso, detección de sesgos de confirmación, variables de confusión y amenazas a la validez interna/externa.
* **📚 Analista de Literatura (`@literatura`, `/papers`):** Contrasta hipótesis con el cuerpo de literatura científica, leyes bibliométricas y vacíos empíricos.
* **📝 Sintetizador y Documentador (`@sintesis`, `/minuta`):** Destila el caos creativo del debate en minutas estructuradas, consensos, controversias y siguientes pasos.
* **🤖 Coordinador General (`@thinktank-bot`):** Modera la sesión y orienta al grupo hacia el rol adecuado.

---

## ⚙️ Instalación y Puesta en Marcha

### 1. Requisitos
* Python 3.10+
* Servidor Mattermost (con cuenta de bot o Personal Access Token)
* Servidor de Inferencia Local (LM Studio / vLLM / Ollama con GPU) o API compatible con OpenAI

### 2. Configuración
Copia la plantilla de entorno y completa tus credenciales:
```bash
cp .env.example .env
nano .env
```

### 3. Ejecución como Demonio
El proyecto incluye un script de control:
```bash
./hub_daemon.sh start    # Iniciar en segundo plano
./hub_daemon.sh status   # Verificar estado del servicio
./hub_daemon.sh logs     # Ver logs en vivo
./hub_daemon.sh restart  # Reiniciar
./hub_daemon.sh stop     # Detener
```

---

## 🧩 Cómo Agregar un Nuevo Agente

Para añadir un nuevo caso de uso (ej. `vigilancia`, `editorial`, `proyectos`):
1. Crea una carpeta en `agents/<nombre_caso>/`.
2. Define su lógica y método `should_handle(post)` y `handle_post(post)`.
3. Regístralo en `main.py` dentro de `registered_agents = [...]`.
4. El nuevo agente heredará automáticamente la conexión a Mattermost, la gestión de hilos y la inferencia local.
