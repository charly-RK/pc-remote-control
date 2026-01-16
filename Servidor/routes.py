import json
import platform
import qrcode
from io import BytesIO
import base64
from flask import jsonify
import time

import config

def setup_routes(app):
    @app.route('/')
    def index():
        connection_info = {
            'server_ip': config.SERVER_IP,
            'server_port': config.SERVER_PORT,
            'pin_code': config.PIN_CODE,
            'active_connections': len([c for c in config.active_connections.values() if c.get('authenticated', False)]),
            'platform': platform.system(),
            'qr_code_url': f'http://{config.SERVER_IP}:{config.SERVER_PORT}/qr'
        }
        return jsonify(connection_info)

    @app.route('/qr')
    def qr_code():
        if not config.SERVER_IP or not config.PIN_CODE:
            return "Server not initialized", 500
        
        connection_url = f"http://{config.SERVER_IP}:{config.SERVER_PORT}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(connection_url)
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
                    <p><strong>IP:</strong> {config.SERVER_IP}:{config.SERVER_PORT}</p>
                    <div class="pin">{config.PIN_CODE}</div>
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
            'uptime': time.time() - config.start_time,
            'active_connections': len(config.active_connections),
            'authenticated_connections': len([c for c in config.active_connections.values() if c.get('authenticated', False)]),
            'pin_code': config.PIN_CODE,
            'platform': platform.system()
        }
        return jsonify(status_info)