import json
import time
from datetime import datetime
from flask import request
from flask_socketio import emit
import platform

import config
from mouse_handler import handle_mouse_move, handle_mouse_click, handle_mouse_scroll
from keyboard_handler import handle_key_press, handle_text_input
from media_handler import handle_media_control
from system_handler import handle_system_control

def setup_socket_handlers(socketio, on_auth_success=None, on_disconnect=None):
    @socketio.on('connect')
    def handle_connect():
        client_id = request.sid
        print(f"CLIENT CONNECTED: {client_id}")
        print(f"Client IP: {request.remote_addr}")
        
        config.active_connections[client_id] = {
            'connected_at': datetime.now(),
            'authenticated': False,
            'ip': request.remote_addr
        }

    @socketio.on('disconnect')
    def handle_disconnect_event():
        client_id = request.sid
        print(f"CLIENT DISCONNECTED: {client_id}")
        if client_id in config.active_connections:
            del config.active_connections[client_id]
            
        if on_disconnect:
            try:
                on_disconnect()
            except Exception as e:
                print(f"Error in on_disconnect callback: {e}")

    @socketio.on('authenticate')
    def handle_authentication(json_data):
        try:
            data = json.loads(json_data) if isinstance(json_data, str) else json_data
            client_id = request.sid
            print(f"AUTH ATTEMPT from {client_id}")
            print(f"Received data: {data}")
            
            if not data or 'pin' not in data:
                print("ERROR: No pin in data")
                emit('authentication_result', {'success': False, 'message': 'No pin provided'})
                return
            
            pin = str(data['pin'])
            device_name = data.get('device_name', 'Dispositivo Desconocido')
            print(f"PIN received: {pin}, Expected: {config.PIN_CODE}")
            
            if client_id not in config.active_connections:
                print("ERROR: Client not in connections")
                emit('authentication_result', {'success': False, 'message': 'Connection not found'})
                return
            
            if pin == config.PIN_CODE:
                config.active_connections[client_id]['authenticated'] = True
                config.active_connections[client_id]['device_name'] = device_name
                print(f"SUCCESS: Client {client_id} authenticated ({device_name})")
                
                if on_auth_success:
                    try:
                        on_auth_success(device_name)
                    except Exception as e:
                        print(f"Error in on_auth_success callback: {e}")
                
                emit('authentication_result', {
                    'success': True,
                    'message': 'Authenticated successfully'
                })
                
                emit('system_info', {
                    'platform': platform.system(),
                    'platform_version': platform.version(),
                    'machine': platform.machine()
                })
            else:
                print(f"FAILED: Invalid PIN from {client_id}")
                emit('authentication_result', {
                    'success': False,
                    'message': 'Invalid PIN'
                })
        except Exception as e:
            print(f"ERROR in authentication: {e}")
            emit('authentication_result', {'success': False, 'message': f'Error: {str(e)}'})

    @socketio.on('command')
    def handle_command(data):
        client_id = request.sid
        # print(f"COMMAND from {client_id}: {data}")
        
        if client_id not in config.active_connections or not config.active_connections[client_id].get('authenticated', False):
            emit('command_response', {
                'ok': False,
                'error': 'Not authenticated',
                'original_action': data.get('action', 'unknown')
            })
            return

        action = data.get('action')
        response = {'ok': False, 'error': 'Unknown command'}

        try:
            if action == 'mouse_move':
                response = handle_mouse_move(data)
            elif action == 'mouse_click':
                response = handle_mouse_click(data)
            elif action == 'mouse_scroll':
                response = handle_mouse_scroll(data)
            elif action in ['key_press', 'press', 'down', 'up']:
                response = handle_key_press(data)
            elif action == 'text_input':
                response = handle_text_input(data)
            elif action == 'media_control' or action == 'media':
                response = handle_media_control(data)
            elif action in ['system_control', 'system', 'screen']:
                response = handle_system_control(data)
        except Exception as e:
            print(f"Error handling command {action}: {e}")
            response = {'ok': False, 'error': str(e)}
            
        emit('command_response', response)