# Servidor PC Remote Control

Servidor Python para Windows que permite el control remoto del PC desde dispositivos móviles.

## 📋 Características

- Servidor Flask con SocketIO para comunicación en tiempo real
- Interfaz gráfica moderna con CustomTkinter
- Generación automática de código QR para conexión
- Autenticación mediante PIN
- Control de mouse y teclado
- Inicio automático con Windows
- Minimización a bandeja del sistema
- Detección automática de IP y puerto disponible

## 💻 Requisitos

- Windows 10/11
- Python 3.13 o superior

## 🚀 Instalación

### Opción 1: Crear y Usar el Ejecutable (Recomendado)

1. **Generar el ejecutable:**
   Abre una terminal en la carpeta `Servidor` y ejecuta:
   ```bash
   pyinstaller PCRemoteControl.spec
   ```

2. **Ejecutar:**
   - Ve a la carpeta `dist/` creada
   - Ejecuta `PCRemoteControl.exe`

3. El servidor se iniciará automáticamente y se minimizará a la bandeja del sistema.

### Opción 2: Ejecutar desde código fuente (Recomendado para desarrollo)

1. Instala las dependencias:
```bash
pip install -r requirements.txt
```

2. Ejecuta el servidor:
```bash
python gui_app.py
```

## 📖 Uso

### Primera vez

1. Inicia el servidor (desde código o ejecutable compilado)
2. El servidor se iniciará automáticamente
3. Aparecerá un código QR en la interfaz
4. Escanea el código QR desde la app móvil
5. Ingresa el PIN mostrado en la interfaz

### ⚙️ Configuración

Accede a la sección "Configuración" en la interfaz para:

- **Iniciar con Windows**: El servidor se ejecutará automáticamente al iniciar el sistema
- **Minimizar a la bandeja**: Mantiene el servidor en segundo plano sin cerrar
- **Iniciar servidor automáticamente**: El servidor se inicia al abrir la aplicación

### 🔔 Bandeja del sistema

Cuando el servidor está minimizado en la bandeja:
- Haz clic derecho en el icono para ver opciones
- "Mostrar" para abrir la interfaz
- "Salir" para cerrar completamente el servidor

## 📁 Estructura del Proyecto

```
Servidor/
├── gui_app.py              # Aplicación principal con interfaz gráfica
├── config.py               # Configuración de Flask y SocketIO
├── routes.py               # Rutas HTTP del servidor
├── socket_handlers.py      # Manejadores de eventos SocketIO
├── input_detector.py       # Detección de entrada del sistema
├── utils.py                # Utilidades (IP, PIN, etc.)
├── requirements.txt        # Dependencias Python
├── src/                    # Recursos (iconos, imágenes)
├── dist/                   # Ejecutable compilado (no incluido en repo)
└── build/                  # Archivos de compilación (no incluido en repo)
```

## 🔧 Compilar el Ejecutable

Para generar un nuevo ejecutable después de modificar el código:

### Paso 1: Instalar/Actualizar Dependencias

Asegúrate de tener todas las dependencias instaladas:

```bash
pip install -r requirements.txt
```

### Paso 2: Compilar con el archivo .spec

Usa el archivo `PCRemoteControl.spec` que ya está configurado con todos los imports necesarios:

```bash
pyinstaller PCRemoteControl.spec
```

El ejecutable se generará en `dist\PCRemoteControl.exe`

### Solución de Problemas

#### Si aparece el error "invalid syscall":

1. **Compilar en modo consola para ver errores:**
   - Edita `PCRemoteControl.spec`
   - Cambia `console=False` a `console=True`
   - Recompila: `pyinstaller PCRemoteControl.spec`
   - Ejecuta el .exe y observa los mensajes de error

2. **Verificar que pywin32 esté instalado correctamente:**
   ```bash
   python -c "import win32gui; print('OK')"
   ```

3. **Reinstalar pywin32 con scripts post-instalación:**
   ```bash
   pip uninstall pywin32
   pip install pywin32
   python -m pywin32_postinstall -install
   ```

#### Notas Importantes:

- El archivo `.spec` ya incluye todos los hidden imports necesarios (42 imports)
- Se excluyen librerías innecesarias (numpy, pandas, etc.) para reducir el tamaño
- El icono debe estar en `src\Logo.ico`
- Los recursos (imágenes, iconos) deben estar en la carpeta `src`
- **Recomendación:** Usa siempre el archivo `.spec` en lugar del comando directo

## 📦 Dependencias Principales

- **Flask**: Framework web
- **Flask-SocketIO**: Comunicación en tiempo real
- **CustomTkinter**: Interfaz gráfica moderna
- **PyAutoGUI**: Control de mouse y teclado
- **Pillow**: Procesamiento de imágenes
- **qrcode**: Generación de códigos QR
- **pystray**: Icono en bandeja del sistema

## 🌐 Configuración de Red

El servidor:
- Detecta automáticamente la IP local
- Usa el puerto **5723** por defecto
- Si el puerto está ocupado, busca uno disponible automáticamente
- Escucha en todas las interfaces (0.0.0.0)

**Asegúrate de que:**
- El firewall de Windows permita conexiones en el puerto configurado
- El PC y el dispositivo móvil estén en la misma red local

## 🐛 Solución de Problemas

### El servidor no inicia
- Verifica que el puerto 5723 no esté en uso
- Ejecuta como administrador si es necesario

### No se puede conectar desde la app móvil
- Verifica que ambos dispositivos estén en la misma red
- Revisa la configuración del firewall
- Asegúrate de que la IP mostrada sea correcta

### El servidor se cierra al cerrar la ventana
- Activa "Minimizar a la bandeja" en Configuración
- El servidor se mantendrá en segundo plano

## 👨‍💻 Desarrollo

### Modificar la interfaz

La interfaz está construida con CustomTkinter. Los componentes principales están en:
- `create_sidebar()`: Barra lateral de navegación
- `create_home_frame()`: Panel de conexión
- `create_settings_frame()`: Panel de configuración
- `create_about_frame()`: Panel de información

### Agregar nuevos comandos

1. Define el manejador en `socket_handlers.py`
2. Implementa la lógica de control
3. Actualiza la app móvil para enviar el comando

## 🔒 Notas de Seguridad

- El servidor solo acepta conexiones de la red local
- Se requiere autenticación mediante PIN
- El PIN se genera aleatoriamente en cada inicio
- No exponer el servidor a internet sin medidas de seguridad adicionales

---

**Desarrollado por RISK KEEP**
