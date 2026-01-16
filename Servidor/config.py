import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Variables globales
active_connections = {}
PIN_CODE = None
SERVER_IP = None
SERVER_PORT = 5723
start_time = None

# Configuración de Flask
def create_app():
    from flask import Flask
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'pc_control_secret_key')
    app.config['DEBUG'] = False
    return app

# Configuración de SocketIO
def create_socketio(app):
    from flask_socketio import SocketIO
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='threading',
        logger=True,
        engineio_logger=True,
        ping_timeout=60,
        ping_interval=25,
        max_http_buffer_size=1e8
    )
    return socketio