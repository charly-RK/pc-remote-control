import json
import platform
import qrcode
from io import BytesIO
import base64
from flask import jsonify
from utils import generate_pin, get_local_ip

def setup_routes(app, socketio):
    from main import SERVER_IP, SERVER_PORT, PIN_CODE, active_connections, start_time
    
    @app.route('/')
    def index():
        connection_info = {
            'server_ip': SERVER_IP,
            'server_port': SERVER_PORT,
            'pin_code': PIN_CODE,
            'active_connections': len([c for c in active_connections.values() if c.get('authenticated', False)]),
            'platform': platform.system(),
            'qr_code_url': f'http://{SERVER_IP}:{SERVER_PORT}/qr'
        }
        return jsonify(connection_info)

    @app.route('/qr')
    def qr_code():
        if not SERVER_IP or not PIN_CODE:
            return "Server not initialized", 500
        
        connection_data = {
            "ip": SERVER_IP,
            "port": SERVER_PORT,
            "code": PIN_CODE
        }
        connection_json = json.dumps(connection_data)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(connection_json)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>PC Control - QR Code</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    text-align: center;
                    padding: 50px;
                    background-color: #f0f0f0;
                }}
                .container {{
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                    display: inline-block;
                }}
                .info {{
                    margin-top: 20px;
                    font-size: 14px;
                    color: #666;
                }}
                .pin {{
                    font-family: monospace;
                    font-size: 24px;
                    color: #e74c3c;
                    font-weight: bold;
                    letter-spacing: 2px;
                    padding: 10px;
                    background: #fff5f5;
                    border-radius: 5px;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>PC Control Server</h2>
                <img src="data:image/png;base64,{img_str}" alt="QR Code">
                <div class="info">
                    <p><strong>IP:</strong> {SERVER_IP}:{SERVER_PORT}</p>
                    <div class="pin">{PIN_CODE}</div>
                    <p>Escanea este codigo QR con la app movil</p>
                </div>
            </div>
        </body>
        </html>
        '''
        return html

    @app.route('/status')
    def status():
        status_info = {
            'server_running': True,
            'uptime': time.time() - start_time,
            'active_connections': len(active_connections),
            'authenticated_connections': len([c for c in active_connections.values() if c.get('authenticated', False)]),
            'pin_code': PIN_CODE,
            'platform': platform.system()
        }
        return jsonify(status_info)

def start_server(socketio, app, port):
    from main import SERVER_IP, PIN_CODE, start_time, active_connections
    
    PIN_CODE = generate_pin()
    SERVER_IP = get_local_ip()
    SERVER_PORT = port
    
    # Registrar handlers de socket
    from socket_handlers import register_socket_handlers
    register_socket_handlers(socketio)
    
    # Configurar rutas HTTP
    setup_routes(app, socketio)
    
    print("\n" + "="*50)
    print("PC CONTROL SERVER")
    print("="*50)
    print(f"Server IP: {SERVER_IP}")
    print(f"Port: {port}")
    print(f"PIN Code: {PIN_CODE}")
    print(f"QR Code URL: http://{SERVER_IP}:{port}/qr")
    print(f"Status URL: http://{SERVER_IP}:{port}/status")
    print("="*50)
    print("\nWaiting for connections...")
    print("Press Ctrl+C to stop the server\n")
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=False,
        use_reloader=False,
        allow_unsafe_werkzeug=True
    )