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
import tkinter as tk
from tkinter import ttk

# For system tray icon
import pystray
from pystray import MenuItem, Menu
from PIL import Image, ImageDraw
try: 
    import win32api 
    import winerror
    import win32event 
    from ctypes import windll, wintypes, Structure, byref
    WINDOWS_SUPPORT = True

    mutex = win32event.CreateMutex(None, False, "ButtonClicker-main")

    if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
        print("Another instance is already running.")
        sys.exit(0)
except ImportError:
    print("Warning: pywin32 not installed. Windows-specific features disabled.")
    WINDOWS_SUPPORT = False

class ControlUI:
    def __init__(self, button_clicker):
        self.button_clicker = button_clicker
        self.root = None
        self.status_label = None
        self.start_stop_button = None
        
    def create_ui(self):
        """Create the control UI window."""
        if self.root is not None:
            try:
                # Check if window still exists
                self.root.winfo_exists()
                self.root.lift()
                self.root.focus_force()
                return
            except:
                # Window was closed, reset root
                self.root = None
            
        self.root = tk.Tk()
        self.root.title("Button Clicker Control")
        self.root.geometry("400x250")
        self.root.resizable(False, False)
        
        # Set window icon if available
        try:
            script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            icon_path = os.path.join(script_dir, "app.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Button Clicker Control", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Status
        ttk.Label(main_frame, text="Status:", font=("Arial", 10, "bold")).grid(
            row=1, column=0, sticky=tk.W, pady=5)
        self.status_label = ttk.Label(main_frame, text="Stopped", 
                                     foreground="red")
        self.status_label.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Loaded buttons count
        ttk.Label(main_frame, text="Loaded Buttons:", font=("Arial", 10, "bold")).grid(
            row=2, column=0, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text=f"{len(self.button_clicker.button_images)}").grid(
            row=2, column=1, sticky=tk.W, pady=5)
        
        # Confidence level
        ttk.Label(main_frame, text="Confidence:", font=("Arial", 10, "bold")).grid(
            row=3, column=0, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text=f"{self.button_clicker.confidence:.1%}").grid(
            row=3, column=1, sticky=tk.W, pady=5)
        
        # Check interval
        ttk.Label(main_frame, text="Check Interval:", font=("Arial", 10, "bold")).grid(
            row=4, column=0, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text=f"{self.button_clicker.check_interval}s").grid(
            row=4, column=1, sticky=tk.W, pady=5)
        
        # Control buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        # Start/Stop button
        self.start_stop_button = ttk.Button(button_frame, text="Start", 
                                           command=self.toggle_clicker, width=15)
        self.start_stop_button.pack(side=tk.LEFT, padx=5)
        
        # Pause/Resume button
        self.pause_resume_button = ttk.Button(button_frame, text="Pause", 
                                            command=self.toggle_pause, width=15)
        self.pause_resume_button.pack(side=tk.LEFT, padx=5)
        
        # Instructions
        instructions = tk.Text(main_frame, height=4, width=45, wrap=tk.WORD)
        instructions.grid(row=6, column=0, columnspan=2, pady=(20, 0))
        instructions.insert("1.0", 
            "Instructions:\n"
            "• Right-click mouse anywhere to pause/resume\n"
            "• Use Start/Stop to control the clicker\n"
            "• Close this window to minimize to tray")
        instructions.config(state=tk.DISABLED)
        
        # Update initial state
        self.update_ui_state()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Start UI update loop
        self.update_ui_loop()
        
    def update_ui_state(self):
        """Update UI elements based on current state."""
        if self.status_label is None:
            return
            
        if self.button_clicker.running:
            if self.button_clicker.paused:
                self.status_label.config(text="Paused", foreground="orange")
                self.pause_resume_button.config(text="Resume")
            else:
                self.status_label.config(text="Running", foreground="green")
                self.pause_resume_button.config(text="Pause")
            self.start_stop_button.config(text="Stop")
        else:
            self.status_label.config(text="Stopped", foreground="red")
            self.start_stop_button.config(text="Start")
            self.pause_resume_button.config(text="Pause")
            
    def update_ui_loop(self):
        """Continuously update UI state."""
        if self.root is not None:
            self.update_ui_state()
            self.root.after(1000, self.update_ui_loop)
            
    def toggle_clicker(self):
        """Toggle start/stop of the clicker."""
        if self.button_clicker.running:
            self.button_clicker.stop_clicker()
        else:
            self.button_clicker.start_clicker()
            
    def toggle_pause(self):
        """Toggle pause/resume of the clicker."""
        if self.button_clicker.running:
            self.button_clicker.paused = not self.button_clicker.paused
            status = "Paused" if self.button_clicker.paused else "Resumed"
            print(status)
            if self.button_clicker.tray_icon:
                running_status = "Running" if not self.button_clicker.paused else "Paused"
                self.button_clicker.update_tray_tooltip(f"Button Clicker - {running_status}")
            
    def on_close(self):
        """Handle window close event."""
        #self.root.withdraw()  # Hide window instead of destroying
        self.quit_app()
        
    def quit_app(self):
        """Properly quit the application."""
        if self.root is not None:
            self.root.quit()  # Exit mainloop
            
    def show(self):
        """Show the UI window."""
        if self.root is None:
            self.create_ui()
        else:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            
    def destroy(self):
        """Destroy the UI window."""
        if self.root is not None:
            self.root.destroy()
            self.root = None

class ButtonClicker:
    def __init__(self, button_images_folder, confidence=0.8, check_interval=1): 
        self.button_images = self.load_button_images(button_images_folder)
        self.confidence = confidence
        self.check_interval = check_interval
        self.running = False
        self.paused = False
        self.tray_icon = None
        self.control_ui = ControlUI(self)
        
        # Get console window handle
        self.console_hwnd = win32gui.GetForegroundWindow()

    def load_button_images(self, folder_path):
        """Load all button images from the specified folder."""
        button_images = {}
        
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Folder '{folder_path}' not found")
            
        supported_formats = ('.png', '.jpg', '.jpeg' )
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(supported_formats):
                name = os.path.splitext(filename)[0]
                path = os.path.join(folder_path, filename)
                try:
                    img = cv2.imread(path, cv2.IMREAD_COLOR)
                    if img is not None:
                        button_images[name] = img
                    else:
                        print(f"Warning: Could not load image {filename}")
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
                        
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
                running_status = "Running" if not self.paused else "Paused"
                self.update_tray_tooltip(f"Button Clicker - {running_status}")
        return None
    
    def click_button(self, position):
        """Click at the specified position."""
        pyautogui.moveTo(position[0], position[1])
        pyautogui.click()
        print(f"Clicked at {position}")
    
    def on_right_click(self, x, y, button, pressed):
        """Toggle pause on right mouse button click."""
        if button == mouse.Button.right and pressed:
            if self.running:  # Only allow pause/resume when running
                self.paused = not self.paused
                status = "Paused" if self.paused else "Resumed"
                print(status)
                if self.tray_icon:
                    running_status = "Running" if not self.paused else "Paused"
                    self.update_tray_tooltip(f"Button Clicker - {running_status}")

    def show_control_ui(self):
        """Show the control UI."""
        self.control_ui.show()

    def create_tray_image(self):
        """Create system tray icon"""
        icon_path = None
        
        # Check if the icon file exists in the same directory as the script
        script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        possible_paths = [ 
            os.path.join(script_dir, "app.ico")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                icon_path = path
                break
        
        if icon_path:
            # Load from ICO file
            image = Image.open(icon_path)
            return image
        
        width = 64
        height = 64 
        image = Image.new('RGBA', (width, height), color=(255, 255, 255, 0))

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
        image = self.create_tray_image()
        # Create menu with dynamic functionality
        menu = Menu(
            MenuItem('Button Clicker', None, enabled=False),
            MenuItem('Show Control Panel', lambda: self.show_control_ui()),
            pystray.Menu.SEPARATOR,
            MenuItem(lambda text: 'Stop' if self.running else 'Start', lambda: self.toggle_start_stop()),
            pystray.Menu.SEPARATOR,
            MenuItem('Exit', lambda: self.exit_clicker())
        )
        
        # Create tray icon
        self.tray_icon = pystray.Icon("button_clicker", image, "Button Clicker - Stopped", menu)
        
        # Handle left click on tray icon
        def on_left_click(icon, item):
            self.show_control_ui()
        
        # Set the left click handler
        self.tray_icon.default_action = on_left_click
        
        # Run the tray icon in a separate thread
        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()
        
    def update_tray_tooltip(self, tooltip):
        """Update the tray icon tooltip."""
        if self.tray_icon:
            self.tray_icon.title = tooltip
            
    def toggle_start_stop(self):
        """Toggle start/stop from tray menu."""
        if self.running:
            self.stop_clicker()
        else:
            self.start_clicker()
            

            
    def start_clicker(self):
        """Start the Button clicker."""
        if not self.running:
            self.running = True
            self.paused = False
            print("Button clicker started")
            self.update_tray_tooltip("Button Clicker - Running")
            
    def stop_clicker(self):
        """Stop the Button clicker."""
        if self.running:
            self.running = False
            self.paused = False
            print("Button clicker stopped")
            self.update_tray_tooltip("Button Clicker - Stopped")
            
    def exit_clicker(self):
        """Exit the application."""
        self.detection_running = False
        self.stop_clicker()
        if self.tray_icon:
            self.tray_icon.stop()
        self.control_ui.quit_app()
        print("Exiting...")
        os._exit(0)
        
    def button_detection_loop(self):
        """Background thread for button detection."""
        try:
            while True:
                if not hasattr(self, 'detection_running') or not self.detection_running:
                    time.sleep(1)
                    continue
                    
                if not self.running:
                    time.sleep(1)
                    continue
                    
                if self.paused: 
                    time.sleep(1)
                    continue

                for name, image in self.button_images.items():
                    if not self.running or self.paused:
                        break
                    original_pos = pyautogui.position()
                    position = self.find_button(image)
                    if position:
                        print(f"Found button: {name}")
                        self.click_button(position) 
                        time.sleep(1)
                        pyautogui.moveTo(original_pos)  # Move back to original position
                        time.sleep(2)
                
                time.sleep(self.check_interval)
                
        except Exception as e:
            print(f"Button detection error: {e}")

    def run(self):
        """Main application entry point."""
        print("Button Clicker initialized. Use the system tray icon to control.")
        
        # Create system tray icon
        self.create_tray_icon()
        
        # Set up mouse listener
        listener = mouse.Listener(on_click=self.on_right_click)
        listener.start()

        # Start button detection in background thread
        self.detection_running = True
        detection_thread = threading.Thread(target=self.button_detection_loop, daemon=True)
        detection_thread.start()

        # Show control UI initially
        self.show_control_ui()
        
        try:
            # Run tkinter mainloop on main thread - this is crucial for proper UI operation
            if self.control_ui.root:
                self.control_ui.root.mainloop()
            else:
                # Fallback: keep main thread alive if UI isn't created
                while self.detection_running:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopped by user")
        finally:
            self.detection_running = False
            self.running = False
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
        filename=f"logs/error_log-{today_date}.txt",
        level=logging.ERROR,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    # Set global exception handler
    sys.excepthook = log_exception
    
    # Configuration
    BUTTON_IMAGES_FOLDER = "button_images"   
    CONFIDENCE_LEVEL = 0.8  
    CHECK_INTERVAL = 1  
     
    try:
        clicker = ButtonClicker(
            button_images_folder=BUTTON_IMAGES_FOLDER,
            confidence=CONFIDENCE_LEVEL,
            check_interval=CHECK_INTERVAL
        )
        
        # Start the main loop
        clicker.run()
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")