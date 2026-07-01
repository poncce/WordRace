🎯 Wordle Race

Wordle multijugador en español, jugado en tiempo real. Creá una sala, invitá a tus amigos con un código y compitan para ver quién adivina la palabra primero. Todos juegan la misma palabra al mismo tiempo — gana quien la resuelve en menos intentos.

🕹️ Cómo se juega


Un jugador crea una sala y comparte el código (o el link directo) con los demás.
Todos los jugadores se unen a la sala y esperan a que el host inicie la partida.
Al arrancar, todos reciben la misma palabra oculta y compiten en simultáneo.
Cada intento se marca con el clásico sistema de colores de Wordle:

🟩 Verde: letra correcta en la posición correcta
🟨 Amarillo: letra correcta en la posición incorrecta
⬜ Gris: letra no está en la palabra



Se puede ver en vivo el progreso de los demás jugadores (colores de sus intentos, sin revelar las letras) hasta que termina la partida.
Al finalizar, se arma un ranking según quién resolvió la palabra en menos intentos y en menor tiempo.


✨ Funcionalidades


Salas privadas con código de invitación y link directo para unirse
Tiempo real vía WebSockets (Socket.IO) — sin necesidad de recargar la página
Configuración de partida: largo de palabra (5 a 8 letras) y cantidad máxima de intentos (3 a 10)
Reconexión de jugadores: si alguien se desconecta, tiene una ventana de tiempo para volver a entrar sin perder su progreso
Validación de palabras contra el diccionario de la RAE
Ranking en vivo por intentos usados y tiempo de resolución
Limpieza automática de salas inactivas y jugadores "fantasma"


🛠️ Stack técnico

CapaTecnologíaBackendPython 3 + FlaskTiempo realFlask-SocketIO (WebSockets)FrontendHTML, CSS y JavaScript vanillaPersistenciaEn memoria (sin base de datos)Servidor de producciónGunicorn (worker threaded) + simple-websocketDespliegueRender

📁 Estructura del proyecto

app/
├── api/            # Endpoints HTTP (health check, info de salas, stats)
├── data/           # Listado de palabras
├── domain/         # Modelos de dominio (Room, Player, Game, excepciones)
├── repositories/   # Persistencia en memoria de salas, jugadores y cache
├── services/       # Lógica de negocio (salas, partidas, validación de palabras)
├── sockets/        # Eventos y handlers de Socket.IO
├── static/         # Frontend (HTML, CSS, JS)
└── config.py       # Configuración de la app

run.py              # Punto de entrada de la aplicación
requirements.txt    # Dependencias de Python

La arquitectura separa responsabilidades en capas (dominio, repositorios, servicios) para facilitar el mantenimiento y, eventualmente, poder reemplazar el almacenamiento en memoria por uno persistente (Redis, por ejemplo) sin tocar la lógica de negocio.

🚀 Correrlo localmente

Requisitos: Python 3.10 o superior

bash# 1. Clonar el repositorio
git clone <URL_DEL_REPO>
cd wordle-race

# 2. Crear entorno virtual (opcional pero recomendado)
python -m venv venv
source venv/bin/activate   # En Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env

# 5. Iniciar el servidor
python run.py

La app va a estar disponible en http://localhost:5000.

☁️ Despliegue

El proyecto está preparado para desplegarse en Render usando el archivo render.yaml incluido (Render Blueprint). El servidor de producción corre con Gunicorn en modo threaded, aprovechando simple-websocket para mantener el soporte completo de WebSockets sin depender de eventlet/gevent.

🎓 Contexto académico

Este proyecto fue desarrollado como trabajo grupal para la materia Programación sobre Redes, a cargo del docente Sergio Daniel Ioppolo.

Integrantes:


Julián Prol
Gonzalo Esteche
Máximo Casanovas
Ignacio Ponce
