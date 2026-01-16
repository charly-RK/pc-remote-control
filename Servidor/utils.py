import random
import socket
import time
import json
import os
import sys

PIN_FILE = "server_pin.json"

def get_pin_file_path():
    """Obtiene la ruta absoluta del archivo de PIN"""
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(application_path, PIN_FILE)

def save_pin(pin):
    """Guarda el PIN en un archivo local"""
    try:
        with open(get_pin_file_path(), 'w') as f:
            json.dump({'pin': pin}, f)
    except Exception as e:
        print(f"Error guardando PIN: {e}")

def load_pin():
    """Carga el PIN guardado si existe"""
    try:
        path = get_pin_file_path()
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
                return data.get('pin')
    except Exception as e:
        print(f"Error cargando PIN: {e}")
    return None

def clear_pin():
    """Elimina el archivo de PIN"""
    try:
        path = get_pin_file_path()
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"Error eliminando PIN: {e}")

def generate_pin():
    # Intentar cargar PIN existente
    saved_pin = load_pin()
    if saved_pin:
        return saved_pin
        
    # Generar nuevo si no existe
    new_pin = str(random.randint(100000, 999999))
    save_pin(new_pin)
    return new_pin

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

class NetworkManager:
    def __init__(self, default_port=5000, port_range=(5000, 5100), auto_find=True):
        self.default_port = default_port
        self.port_range = port_range
        self.auto_find = auto_find
    
    def is_port_in_use(self, port):
        """Verifica si un puerto está en uso"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            try:
                s.bind(('0.0.0.0', port))
                return False  # Puerto disponible
            except socket.error:
                return True  # Puerto ocupado
    
    def get_available_port(self):
        """Obtiene un puerto disponible"""
        if not self.auto_find:
            return self.default_port
            
        # Primero intentar el puerto por defecto
        if not self.is_port_in_use(self.default_port):
            return self.default_port
            
        # Si está ocupado, buscar en el rango
        for port in range(self.port_range[0], self.port_range[1] + 1):
            if not self.is_port_in_use(port):
                return port
                
        # Si no encuentra en el rango, buscar cualquier puerto > 1024
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]