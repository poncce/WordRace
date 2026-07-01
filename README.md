# 🎯 WordRace

> Un **Wordle multijugador en español**, jugado en tiempo real. Creá una sala, invitá a tus amigos con un código y compitan para descubrir la palabra antes que los demás.

---

# 🌐 Probar la aplicación

La aplicación ya se encuentra desplegada y disponible para cualquier usuario.

👉 **https://wordiirace.onrender.com/**

No es necesario instalar nada. Solo ingresá a la URL desde cualquier navegador, creá una sala o uníte a una existente y comenzá a jugar.

---

# 📖 Descripción

WordRace permite que varios jugadores participen simultáneamente de una misma partida de Wordle.

Todos reciben la **misma palabra oculta** al mismo tiempo y gana quien la adivine utilizando **menos intentos**. En caso de empate, se utiliza el **tiempo de resolución** como criterio de desempate.

---

# 🕹️ ¿Cómo se juega?

1. 🎮 Un jugador crea una sala.
2. 🔗 Comparte el código o el enlace de invitación.
3. 👥 Los demás jugadores se unen a la sala.
4. ▶️ El host inicia la partida.
5. ✍️ Todos intentan descubrir la misma palabra en simultáneo.
6. 🏆 Gana quien la resuelve con menos intentos y en el menor tiempo.

## Sistema de colores

| Color | Significado |
| ------ | ----------- |
| 🟩 Verde | Letra correcta en la posición correcta |
| 🟨 Amarillo | Letra correcta en una posición incorrecta |
| ⬜ Gris | La letra no pertenece a la palabra |

Durante la partida es posible observar el progreso de los demás jugadores sin revelar las letras que escribieron.

Al finalizar se genera un ranking ordenado por:

1. Menor cantidad de intentos.
2. Menor tiempo de resolución.

---

# ✨ Funcionalidades

- 🏠 Salas privadas con código de invitación.
- 🔗 Enlace directo para unirse a una sala.
- ⚡ Juego en tiempo real mediante **WebSockets (Socket.IO)**.
- 🔄 Sin necesidad de recargar la página.
- ⚙️ Configuración de la partida:
  - Palabras de **5 a 8 letras**.
  - Entre **3 y 10 intentos**.
- 🔌 Reconexión automática de jugadores en caso de desconexión.
- 📚 Validación de palabras utilizando el diccionario de la **RAE**.
- 📊 Ranking en vivo según intentos y tiempo.
- 🧹 Eliminación automática de salas inactivas y jugadores desconectados.

---

# 🛠️ Stack Tecnológico

| Área | Tecnología |
|------|------------|
| Backend | Python 3 + Flask |
| Tiempo real | Flask-SocketIO (WebSockets) |
| Frontend | HTML, CSS y JavaScript Vanilla |
| Persistencia | En memoria (sin base de datos) |
| Servidor de producción | Gunicorn + simple-websocket |
| Despliegue | Render |

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

La aplicación está organizada siguiendo una arquitectura por capas (**Domain**, **Repositories** y **Services**), permitiendo mantener una clara separación de responsabilidades y facilitando futuras ampliaciones o cambios en la persistencia.

---

# ☁️ Despliegue

La aplicación se encuentra desplegada en **Render**, utilizando **Gunicorn** junto con **simple-websocket** para ofrecer soporte completo de WebSockets en producción.

---

# 🎓 Contexto académico

Proyecto desarrollado como trabajo grupal para la materia **Programación sobre Redes**.

**Docente**

- Sergio Daniel Ioppolo

### 👨‍💻 Integrantes

- Julián Prol
- Gonzalo Esteche
- Máximo Casanovas
- Ignacio Ponce

---

# ⭐ Características principales

- ✅ Multijugador en tiempo real.
- ✅ Salas privadas.
- ✅ Ranking automático.
- ✅ Configuración personalizada de las partidas.
- ✅ Reconexión de jugadores.
- ✅ Sin base de datos.
- ✅ Arquitectura por capas.
- ✅ Desplegado en Render.

## 🚧 Estado del proyecto

**WordRace** continúa en fase de **desarrollo y depuración**, por lo que es posible que algunas funcionalidades presenten errores o comportamientos inesperados.

Si encontrás algún problema, bug o tenés alguna sugerencia de mejora, te invitamos a reportarlo utilizando la sección de **Issues** del repositorio en GitHub. Tu feedback ayuda a mejorar el proyecto y corregir errores más rápidamente.
