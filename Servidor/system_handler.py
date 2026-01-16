import os
import platform
import pyautogui
import webbrowser
import time

def handle_system_control(data):
    try:
        command = data.get('command', '')
        
        if command == 'shutdown':
            if platform.system() == "Windows":
                os.system("shutdown /s /t 0")
            else:
                os.system("shutdown -h now")
            return {"ok": True, "message": "System shutdown initiated"}
        
        elif command == 'restart':
            if platform.system() == "Windows":
                os.system("shutdown /r /t 0")
            else:
                os.system("reboot")
            return {"ok": True, "message": "System restart initiated"}
        
        elif command == 'sleep':
            if platform.system() == "Windows":
                # Hibernate/Sleep
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            elif platform.system() == "Darwin":
                os.system("pmset sleepnow")
            else:
                os.system("systemctl suspend")
            return {"ok": True, "message": "System sleep initiated"}
            
        elif command == 'logout':
            if platform.system() == "Windows":
                os.system("shutdown /l")
            elif platform.system() == "Darwin":
                # macOS logout usually requires AppleScript or killing loginwindow
                os.system("pkill loginwindow")
            else:
                os.system("gnome-session-quit --no-prompt")
            return {"ok": True, "message": "System logout initiated"}

        elif command == 'lock':
            if platform.system() == "Windows":
                os.system("rundll32.exe user32.dll,LockWorkStation")
            elif platform.system() == "Darwin":
                os.system("pmset displaysleepnow")
            else:
                os.system("gnome-screensaver-command -l")
            return {"ok": True, "message": "System locked"}
            
        elif command == 'task_manager':
            pyautogui.hotkey('ctrl', 'shift', 'esc')
            return {"ok": True, "message": "Task Manager opened"}
            
        elif command == 'explorer':
            pyautogui.hotkey('win', 'e')
            return {"ok": True, "message": "File Explorer opened"}
            
        elif command == 'capture':
            # Press PrintScreen
            pyautogui.press('printscreen')
            return {"ok": True, "message": "Screenshot taken (PrintScreen pressed)"}
        
        elif command == 'show_desktop':
            pyautogui.hotkey('win', 'd')
            return {"ok": True, "message": "Show desktop"}
        
        elif command == 'open_browser':
            webbrowser.open("https://www.google.com")
            return {"ok": True, "message": "Browser opened"}
        
        else:
            return {"ok": False, "error": f"Unknown system command: {command}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
