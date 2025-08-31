import os
import cv2
import numpy as np
import pyautogui
import time
import sys
from PIL import ImageGrab
from pynput import mouse
import threading
import win32api
import win32con
import win32gui
import ctypes
from ctypes import wintypes
import logging

# For system tray icon
import pystray
from pystray import MenuItem, Menu
from PIL import Image, ImageDraw

class ButtonClicker:
    def __init__(self, button_images_folder, confidence=0.8, check_interval=1): 
        self.button_images = self.load_button_images(button_images_folder)
        self.confidence = confidence
        self.check_interval = check_interval
        self.running = False
        self.paused = False
        self.tray_icon = None
        self.console_visible = True
        
        # Get console window handle
        self.console_hwnd = win32gui.GetForegroundWindow()

    def load_button_images(self, folder_path):
        """Load all button images from the specified folder."""
        button_images = {}
        
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Folder '{folder_path}' not found")
            
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                name = os.path.splitext(filename)[0]
                path = os.path.join(folder_path, filename)
                button_images[name] = cv2.imread(path, cv2.IMREAD_COLOR)
                
                if button_images[name] is None:
                    print(f"Warning: Could not load image {filename}")
                    del button_images[name]
                    
        if not button_images:
            raise ValueError("No valid button images found in the folder")
        print(f"Use Mouse right Click to start/pause")
        print(f"Loaded {len(button_images)} button images")
        return button_images
    
    def find_button(self, button_image):
        """Find a button on the screen.""" 
        try:
            screenshot = np.array(ImageGrab.grab())
            screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR) 
            result = cv2.matchTemplate(screenshot, button_image, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= self.confidence: 
                h, w = button_image.shape[:-1]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                return (center_x, center_y)
        except Exception as e:
            print(f"find_button Error : {e}")
            self.paused = not self.paused
            status = "Paused" if self.paused else "Resumed"
            print(status)
            if self.tray_icon:
                self.update_tray_tooltip(f"clicker - {status}")
        return None
    
    def click_button(self, position):
        """Click at the specified position."""
        pyautogui.moveTo(position[0], position[1])
        pyautogui.click()
        print(f"Clicked at {position}")
    
    def on_right_click(self, x, y, button, pressed):
        """Toggle pause on right mouse button click."""
        if button == mouse.Button.right and pressed:
            self.paused = not self.paused
            status = "Paused" if self.paused else "Resumed"
            print(status)
            if self.tray_icon:
                self.update_tray_tooltip(f"Skip clicker - {status}")

    def toggle_console(self, visible=None):
        """Show or hide the console window."""
        if visible is None:
            self.console_visible = not self.console_visible
        else:
            self.console_visible = visible
            
        if self.console_visible:
            win32gui.ShowWindow(self.console_hwnd, win32con.SW_SHOW)
        else:
            win32gui.ShowWindow(self.console_hwnd, win32con.SW_HIDE)
            
    def hide_from_taskbar(self):
        """Hide the console window from the taskbar."""
        # Remove from taskbar
        ex_style = win32gui.GetWindowLong(self.console_hwnd, win32con.GWL_EXSTYLE)
        ex_style |= win32con.WS_EX_TOOLWINDOW
        ex_style &= ~win32con.WS_EX_APPWINDOW
        win32gui.SetWindowLong(self.console_hwnd, win32con.GWL_EXSTYLE, ex_style)
        
    def show_in_taskbar(self):
        """Show the console window in the taskbar."""
        ex_style = win32gui.GetWindowLong(self.console_hwnd, win32con.GWL_EXSTYLE)
        ex_style &= ~win32con.WS_EX_TOOLWINDOW
        ex_style |= win32con.WS_EX_APPWINDOW
        win32gui.SetWindowLong(self.console_hwnd, win32con.GWL_EXSTYLE, ex_style)
        
    def minimize_to_tray(self):
        """Minimize the window to system tray."""
        self.hide_from_taskbar()
        self.toggle_console(False)
        
    def restore_from_tray(self):
        """Restore the window from system tray."""
        self.show_in_taskbar()
        self.toggle_console(True)
        win32gui.ShowWindow(self.console_hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(self.console_hwnd)
    def create_tray_image(self):
        """Create system tray icon"""
        width = 64
        height = 64
        # image = Image.new('RGB', (width, height), color='white')
        # dc = ImageDraw.Draw(image)
        # dc.rectangle([width//2-15, height//2-15, width//2+15, height//2+15], fill='blue')
        # dc.text((width//2-10, height//2-5), "BC", fill='white') 
        # 
        image = Image.new('RGBA', (width, height), color=(255, 255, 255, 0))  # Transparent background

        dc = ImageDraw.Draw(image)

        # Draw square background
        dc.rectangle(
            [width//2-15, height//2-15, width//2+15, height//2+15],
            fill="blue"
        )

        # Draw mouse pointer (triangle arrow shape)
        pointer = [
            (10, 10),   # top
            (10, 40),   # bottom left
            (25, 30)    # right
        ]
        dc.polygon(pointer, fill="black")

        # Add text in the square
        dc.text((width//2-10, height//2-5), "BC", fill="white")
        return image
    
    def create_tray_icon(self):
        """Create a system tray icon."""
        # Create an image for the tray icon
        # width = 64
        # height = 64
        # image = Image.new('RGB', (width, height), color='white')
        # dc = ImageDraw.Draw(image)
        # dc.rectangle([width//2-15, height//2-15, width//2+15, height//2+15], fill='blue')
        # dc.text((width//2-10, height//2-5), "BC", fill='white')
        image = self.create_tray_image()
        # Create menu
        menu = Menu(
            MenuItem('Skip clicker', None),
            pystray.Menu.SEPARATOR,
            MenuItem('Show/Hide log', lambda: self.toggle_console()),
            MenuItem('Start', lambda: self.start_clicker()),
            MenuItem('Stop', lambda: self.stop_clicker()),
            MenuItem('Exit', lambda: self.exit_clicker())
        )
        
        # Create tray icon
        self.tray_icon = pystray.Icon("button_clicker", image, "Skip clicker", menu)
        
        # Run the tray icon in a separate thread
        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()
        
    def update_tray_tooltip(self, tooltip):
        """Update the tray icon tooltip."""
        if self.tray_icon:
            self.tray_icon.title = tooltip
            
    def start_clicker(self):
        """Start the Skip clicker."""
        if not self.running:
            self.running = True
            self.paused = False
            print("Skip clicker started")
            self.update_tray_tooltip("Skip clicker - Running")
            
    def stop_clicker(self):
        """Stop the Skip clicker."""
        if self.running:
            self.running = False
            print("Skip clicker stopped")
            self.update_tray_tooltip("Skip clicker - Stopped")
            
    def exit_clicker(self):
        """Exit the application."""
        self.stop_clicker()
        if self.tray_icon:
            self.tray_icon.stop()
        print("Exiting...")
        os._exit(0)
        
    def run(self):
        """Main loop to continuously check for buttons."""
        self.running = True
        print("Starting button detection... Right-click to pause/resume.")
        
        # Create system tray icon
        self.create_tray_icon()
        
        # Set up mouse listener
        listener = mouse.Listener(on_click=self.on_right_click)
        listener.start()

        try:
            while True:
                if not self.running:
                    time.sleep(1)
                    continue
                    
                if self.paused: 
                    time.sleep(1)
                    continue

                for name, image in self.button_images.items():
                    position = self.find_button(image)
                    if position:
                        print(f"Found button: {name}")
                        self.click_button(position) 
                        time.sleep(1)
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print("\nStopped by user")
            self.running = False
        finally:
            listener.stop()
            if self.tray_icon:
                self.tray_icon.stop()

def log_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler."""
    if issubclass(exc_type, KeyboardInterrupt):
        # Allow Ctrl+C to exit without logging
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # Log exception with traceback
    logging.error(
        "Uncaught exception",
        exc_info=(exc_type, exc_value, exc_traceback)
    )

if __name__ == "__main__":
    log_dir = "logs"
    from datetime import datetime
    today_date = datetime.now().strftime("%Y-%m-%d")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    logging.basicConfig(
        filename=f"logs/error_log-{today_date}.txt",   # log file
        level=logging.ERROR,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    # Set global exception handler
    sys.excepthook = log_exception
    # Configuration
    BUTTON_IMAGES_FOLDER = "button_images"   
    CONFIDENCE_LEVEL = 0.8  
    CHECK_INTERVAL = 2  
     
    try:
        clicker = ButtonClicker(
            button_images_folder=BUTTON_IMAGES_FOLDER,
            confidence=CONFIDENCE_LEVEL,
            check_interval=CHECK_INTERVAL
        )
        
        # Hide from taskbar when minimized
        clicker.hide_from_taskbar()
        
        # Start the main loop
        clicker.run()
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")