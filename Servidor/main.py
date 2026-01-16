import sys
import time
from input_detector import InputDetector

# Importar config primero para inicializar variables
import config
from utils import generate_pin, get_local_ip

def main():
    # Inicializar configuración
    app = config.create_app()
    socketio = config.create_socketio(app)
    
    # Configurar variables globales
    config.PIN_CODE = generate_pin()
    config.SERVER_IP = get_local_ip()
    config.start_time = time.time()

    # Crear e iniciar el detector de campos de entrada
    input_detector = InputDetector(socketio)
    input_detector.start()
    
    # Configurar puerto
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    config.SERVER_PORT = port
    
    # Importar y configurar handlers
    from socket_handlers import setup_socket_handlers
    from routes import setup_routes
    
    # Configurar handlers
    setup_socket_handlers(socketio)
    setup_routes(app)
    
    # Mostrar información del servidor
    print("\n" + "="*50)
    print("PC CONTROL SERVER")
    print("="*50)
    print(f"Server IP: {config.SERVER_IP}")
    print(f"Port: {port}")
    print(f"PIN Code: {config.PIN_CODE}")
    print(f"QR Code URL: http://{config.SERVER_IP}:{port}/qr")
    print(f"Status URL: http://{config.SERVER_IP}:{port}/status")
    print("="*50)
    print("\nWaiting for connections...")
    print("Press Ctrl+C to stop the server\n")
    
    
    # Iniciar servidor
    try:
        socketio.run(
            app,
            host='0.0.0.0',
            port=port,
            debug=False,
            use_reloader=False,
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Asegurarse de detener el detector
        input_detector.stop()

if __name__ == '__main__':
    main()