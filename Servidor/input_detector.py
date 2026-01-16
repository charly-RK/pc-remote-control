import time
import threading
import json
import pyautogui
import win32gui  # Solo para Windows
import win32con
import config

class InputDetector:
    def __init__(self, socketio=None):
        self.socketio = socketio
        self.running = False
        self.detection_thread = None
        self.last_window = None
        
    def start(self):
        """Iniciar detección de ventanas"""
        if self.running:
            return
            
        self.running = True
        self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.detection_thread.start()
        print("Input detector iniciado (modo simplificado)")
    
    def stop(self):
        """Detener detección"""
        self.running = False
        if self.detection_thread:
            self.detection_thread.join(timeout=1)
        print("Input detector detenido")
    
    def _detection_loop(self):
        """Loop simplificado que detecta cambios de ventana"""
        while self.running:
            try:
                # Obtener ventana activa
                hwnd = win32gui.GetForegroundWindow()
                window_title = win32gui.GetWindowText(hwnd)
                
                # Si la ventana cambió
                if window_title != self.last_window:
                    print(f"Ventana cambiada: {window_title}")
                    self.last_window = window_title
                    
                    # Detectar si es una aplicación donde probablemente se escriba
                    text_apps = ['Chrome', 'Firefox', 'Edge', 'Word', 'Notepad', 
                                'Visual Studio', 'Excel', 'PowerPoint', 'Outlook',
                                'Teams', 'WhatsApp', 'Discord', 'Telegram', 'Steam']
                    
                    # Verificar si es una aplicación de texto
                    is_text_app = any(app in window_title for app in text_apps)
                    
                    if is_text_app:
                        self._send_keyboard_event('show', {
                            'window': window_title,
                            'timestamp': time.time()
                        })
                    else:
                        self._send_keyboard_event('hide', {
                            'window': window_title,
                            'timestamp': time.time()
                        })
                
                time.sleep(0.5)  # Verificar cada 500ms
                
            except Exception as e:
                print(f"Error en detección: {e}")
                time.sleep(1)
    
    def _send_keyboard_event(self, event_type, data):
        """Enviar evento de teclado"""
        if self.socketio:
            try:
                for client_id, conn_info in config.active_connections.items():
                    if conn_info.get('authenticated'):
                        self.socketio.emit('keyboard_event', {
                            'event': event_type,
                            'data': data
                        }, room=client_id)
                print(f"Evento de teclado enviado: {event_type}")
            except Exception as e:
                print(f"Error enviando evento de teclado: {e}")