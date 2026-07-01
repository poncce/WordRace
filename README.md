# 🎯 Wordle Race

> Un **Wordle multijugador en español**, jugado en tiempo real.
> Creá una sala, invitá a tus amigos con un código y compitan para descubrir la palabra antes que los demás.

---

## 📖 Descripción

Wordle Race permite que varios jugadores participen simultáneamente de una misma partida de Wordle.

Todos reciben la **misma palabra oculta** al mismo tiempo y gana quien la adivine utilizando **menos intentos**. Si hay empate, se desempata por el **menor tiempo de resolución**.

---

## 🕹️ ¿Cómo se juega?

1. 🎮 Un jugador crea una sala.
2. 🔗 Comparte el código o el enlace con los demás.
3. 👥 Los jugadores ingresan a la sala.
4. ▶️ El host inicia la partida.
5. ✍️ Todos intentan descubrir la misma palabra.
6. 🏆 Gana quien la resuelve primero con la mejor puntuación.

### Sistema de colores

| Color | Significado |
|-------|-------------|
| 🟩 Verde | Letra correcta en la posición correcta |
| 🟨 Amarillo | Letra correcta en una posición incorrecta |
| ⬜ Gris | La letra no pertenece a la palabra |

Durante la partida es posible ver el **progreso de los demás jugadores** sin revelar las letras ingresadas.

Al finalizar se muestra un **ranking** ordenado por:

1. Menor cantidad de intentos.
2. Menor tiempo empleado.

---

# ✨ Funcionalidades

- 🏠 Salas privadas con código de invitación.
- 🔗 Enlace directo para unirse a una sala.
- ⚡ Juego en tiempo real mediante **WebSockets (Socket.IO)**.
- 🔄 Sin necesidad de recargar la página.
- ⚙️ Configuración de:
  - palabras de **5 a 8 letras**
  - **3 a 10 intentos** máximos
- 🔌 Reconexión automática de jugadores.
- 📚 Validación de palabras utilizando el diccionario de la **RAE**.
- 📊 Ranking en vivo.
- 🧹 Eliminación automática de salas inactivas.

---

# 🛠️ Stack Tecnológico

| Área | Tecnología |
|------|------------|
| Backend | Python 3 + Flask |
| Tiempo Real | Flask-SocketIO (WebSockets) |
| Frontend | HTML, CSS y JavaScript Vanilla |
| Persistencia | En memoria (sin base de datos) |
| Producción | Gunicorn + simple-websocket |
| Deploy | Render |

---

# 📂 Estructura del proyecto

```text
app/
├── api/              # Endpoints HTTP
├── data/             # Listado de palabras
├── domain/           # Modelos de dominio
├── repositories/     # Persistencia en memoria
├── services/         # Lógica de negocio
├── sockets/          # Eventos Socket.IO
├── static/           # HTML, CSS y JavaScript
└── config.py

run.py
requirements.txt
```

La arquitectura está organizada por capas (**Domain**, **Repositories** y **Services**) para mantener una clara separación de responsabilidades y facilitar futuras migraciones a una base de datos persistente.

---

# 🚀 Ejecutarlo localmente

## Requisitos

- Python **3.10** o superior

## 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPO>
cd wordle-race
```

## 2. Crear un entorno virtual (opcional)

### Linux / macOS

```bash
python -m venv venv
source venv/bin/activate
```

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

## 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

## 4. Configurar variables de entorno

```bash
cp .env.example .env
```

## 5. Ejecutar el servidor

```bash
python run.py
```

La aplicación estará disponible en:

```
http://localhost:5000
```

---

# ☁️ Despliegue

El proyecto está preparado para desplegarse en **Render**.

Utiliza:

- Gunicorn
- Flask-SocketIO
- simple-websocket

para brindar soporte completo a WebSockets en producción.

---

# 🎓 Contexto académico

Proyecto desarrollado para la materia **Programación sobre Redes**.

**Docente**

- Sergio Daniel Ioppolo

### 👨‍💻 Integrantes

- Julián Prol
- Gonzalo Esteche
- Máximo Casanovas
- Ignacio Ponce

---

## ⭐ Características principales

✅ Multijugador en tiempo real

✅ Salas privadas

✅ Ranking automático

✅ Reconexión de jugadores

✅ Sin base de datos

✅ Arquitectura por capas

✅ Fácil de desplegar en Render
