import pyautogui
from pynput import keyboard

keyboard_controller = keyboard.Controller()

def handle_key_press(data):
    try:
        key = data.get('key', '')
        action = data.get('action', 'press')
        ctrl = data.get('ctrl', False)
        alt = data.get('alt', False)
        shift = data.get('shift', False)
        win = data.get('win', False) or data.get('meta', False)
        
        if not key:
            return {"ok": False, "error": "No key specified"}
            
        # If modifiers are present, use hotkey
        if ctrl or alt or shift or win:
            keys = []
            if ctrl: keys.append('ctrl')
            if alt: keys.append('alt')
            if shift: keys.append('shift')
            if win: keys.append('win')
            keys.append(key)
            
            pyautogui.hotkey(*keys)
            return {"ok": True, "message": f"Hotkey: {'+'.join(keys)}"}
            
        # Map special keys for single key press
        # Use pyautogui for specific keys that might be problematic with pynput
        if key in ['escape', 'f11', 'home', 'win']:

            pyautogui.press(key if key != 'escape' else 'esc')
            return {"ok": True, "message": f"Key press (pyautogui): {key}"}

        key_mapping = {
            'escape': keyboard.Key.esc,
            'f11': keyboard.Key.f11,
            'home': keyboard.Key.home,
            'enter': keyboard.Key.enter,
            'tab': keyboard.Key.tab,
            'delete': keyboard.Key.delete,
            'backspace': keyboard.Key.backspace,
            'ctrl': keyboard.Key.ctrl,
            'alt': keyboard.Key.alt,
            'shift': keyboard.Key.shift,
            'win': keyboard.Key.cmd,
            'cmd': keyboard.Key.cmd,
            'insert': keyboard.Key.insert,
            'menu': keyboard.Key.menu,
            'page_up': keyboard.Key.page_up,
            'page_down': keyboard.Key.page_down,
            'end': keyboard.Key.end,
            'caps_lock': keyboard.Key.caps_lock,
            'print_screen': keyboard.Key.print_screen,
            'scroll_lock': keyboard.Key.scroll_lock,
            'pause': keyboard.Key.pause,
        }

        key_obj = key
        if key in key_mapping:
            key_obj = key_mapping[key]
        elif len(key) > 1:
            if hasattr(keyboard.Key, key):
                key_obj = getattr(keyboard.Key, key)
            else:
                # Handle special cases or ignore
                pass

        
        if action == 'press':
            keyboard_controller.press(key_obj)
            keyboard_controller.release(key_obj)
        elif action == 'down':
            keyboard_controller.press(key_obj)
        elif action == 'up':
            keyboard_controller.release(key_obj)
        
        return {"ok": True, "message": f"Key {action}: {key}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def handle_text_input(data):
    try:
        text = data.get('text', '')
        if text:
            pyautogui.write(text)
            return {"ok": True, "message": f"Text typed: {text[:50]}..."}
        return {"ok": False, "error": "No text specified"}
    except Exception as e:
        return {"ok": False, "error": str(e)}