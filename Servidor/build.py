import PyInstaller.__main__
import os
import shutil

def build():
    print("Building PC Remote Control...")
    
    # Ensure requirements are installed
    # os.system("pip install -r requirements.txt")
    
    # Clean previous build
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
        
    # Define icon path
    icon_path = os.path.join("src", "Logo.ico")
    if not os.path.exists(icon_path):
        # Try png if ico doesn't exist (PyInstaller prefers ico for exe icon)
        icon_path = os.path.join("src", "Logo.png")
    
    # PyInstaller arguments
    args = [
        'gui_app.py',
        '--name=PCRemoteControl',
        '--noconsole',
        '--onefile',
        '--clean',
        f'--icon={icon_path}',
        '--add-data=src;src',  # Include src folder
        # Add hidden imports if needed
        '--hidden-import=engineio.async_drivers.threading',
        '--hidden-import=socketio',
        '--hidden-import=flask_socketio',
        '--hidden-import=pystray',
        '--hidden-import=PIL',
        '--hidden-import=winreg',
    ]
    
    print(f"Running PyInstaller with args: {args}")
    
    PyInstaller.__main__.run(args)
    
    print("Build complete! Check the 'dist' folder.")

if __name__ == "__main__":
    build()
