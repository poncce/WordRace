from dotenv import load_dotenv
load_dotenv()

from app import create_app, socketio
import os

app = create_app()

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV", "production") == "development"
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
