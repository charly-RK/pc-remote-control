import pyautogui
from pynput.mouse import Button, Controller as MouseController

# Deshabilitar fail-safe para evitar errores en esquinas
pyautogui.FAILSAFE = False

mouse = MouseController()

def handle_mouse_move(data):
    try:
        x = data.get('x', 0)
        y = data.get('y', 0)
        pyautogui.moveRel(x, y, duration=0.01)
        return {"ok": True, "message": f"Mouse moved: {x}, {y}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def handle_mouse_click(data):
    try:
        button = data.get('button', 'left')
        click_type = data.get('type', 'single')
        
        if button == 'left':
            btn = Button.left
        elif button == 'right':
            btn = Button.right
        elif button == 'middle':
            btn = Button.middle
        else:
            btn = Button.left
        
        if click_type == 'single':
            mouse.click(btn)
        elif click_type == 'double':
            mouse.click(btn, 2)
        elif click_type == 'down':
            mouse.press(btn)
        elif click_type == 'up':
            mouse.release(btn)
        
        return {"ok": True, "message": f"Mouse {button} click: {click_type}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def handle_mouse_scroll(data):
    try:
        dx = data.get('dx', 0)
        dy = data.get('dy', 0)
        pyautogui.scroll(dy)
        return {"ok": True, "message": f"Scroll: {dy}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}