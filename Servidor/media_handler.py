import pyautogui
import platform
import os

def handle_media_control(data):
    try:
        command = data.get('command', '')
        
        if not command:
            return {"ok": False, "error": "No command provided"}
            
        if command == 'play_pause':
            pyautogui.press('playpause')
        elif command == 'next':
            pyautogui.press('nexttrack')
        elif command == 'previous':
            pyautogui.press('prevtrack')
        elif command == 'volume_up':
            pyautogui.press('volumeup')
        elif command == 'volume_down':
            pyautogui.press('volumedown')
        elif command == 'mute':
            pyautogui.press('volumemute')
        elif command == 'game_bar':
            pyautogui.hotkey('win', 'g')
        elif command == 'record':
            pyautogui.hotkey('win', 'alt', 'r')
        elif command == 'mic_mute':
            # Try common mic mute shortcut (Win+Alt+K for Teams/System)
            pyautogui.hotkey('win', 'alt', 'k')
        elif command == 'set_volume':
            level = data.get('level') # 0.0 to 1.0
            if level is not None:
                try:
                    # Convert to 0-100
                    vol_int = int(float(level) * 100)
                    if platform.system() == 'Windows':
                        # Use PowerShell to set volume (requires nircmd or similar usually, but we can try a complex script or just approximate)
                        # Actually, without external tools, setting absolute volume on Windows via command line is hard.
                        # We will use a simple approximation: mute then volume up N times? No, that's slow.
                        # Better approach: Use a VBScript or PowerShell snippet if possible.
                        # For now, let's assume the user might have 'nircmd' or just use the relative keys if we can't do absolute.
                        # But wait, the user specifically asked for the slider.
                        # I will try to use a PowerShell script that uses AudioEndpointVolume if possible, but that's complex to embed.
                        # Let's try the "nircmd" way if it exists, otherwise... 
                        # Actually, I'll use a python library if installed. I'll try to import pycaw inside the function.
                        try:
                            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                            from comtypes import CLSCTX_ALL
                            import pythoncom
                            pythoncom.CoInitialize()
                            devices = AudioUtilities.GetSpeakers()
                            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                            volume = interface.QueryInterface(IAudioEndpointVolume)
                            # volume.GetMasterVolumeLevel()
                            volume.SetMasterVolumeLevelScalar(float(level), None)
                            return {"ok": True, "message": f"Volume set to {vol_int}%"}
                        except ImportError:
                            # Fallback: We can't set absolute volume easily without pycaw.
                            # We will just log it or maybe try to use nircmd if available.
                            # For now, return error or warning.
                            return {"ok": False, "error": "pycaw not installed, cannot set absolute volume"}
                except Exception as e:
                    return {"ok": False, "error": f"Error setting volume: {e}"}
            else:
                 return {"ok": False, "error": "No level provided for set_volume"}
        else:
             # Fallback for generic commands
             pyautogui.press(command)
             
        return {"ok": True, "message": f"Media command executed: {command}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}