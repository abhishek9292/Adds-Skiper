import os
import cv2
import numpy as np
import pyautogui
import time
from PIL import ImageGrab
from pynput import mouse  # <-- Added import

class ButtonClicker:
    def __init__(self, button_images_folder, confidence=0.8, check_interval=1): 
        self.button_images = self.load_button_images(button_images_folder)
        self.confidence = confidence
        self.check_interval = check_interval
        self.running = False
        self.paused = False  # <-- Added paused state

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
            
        print(f"Loaded {len(button_images)} button images")
        return button_images
    
    def find_button(self, button_image):
        """Find a button on the screen."""
        # Take a screenshot
        screenshot = np.array(ImageGrab.grab())
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
        
        # Try to find the button
        result = cv2.matchTemplate(screenshot, button_image, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= self.confidence:
            # Get the center of the matched area
            h, w = button_image.shape[:-1]
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            return (center_x, center_y)
        
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
            print("Paused" if self.paused else "Resumed")

    def run(self):
        """Main loop to continuously check for buttons."""
        self.running = True
        print("Starting button detection... Press Ctrl+C to stop.")

        # Start mouse listener in the background
        listener = mouse.Listener(on_click=self.on_right_click)
        listener.start()

        try:
            while self.running:
                if self.paused:
                    print("Program paused. Waiting for resume...")
                    time.sleep(0.5)
                    continue

                for name, image in self.button_images.items():
                    position = self.find_button(image)
                    if position:
                        print(f"Found button: {name}")
                        self.click_button(position)
                        # Small delay after click to avoid multiple detections
                        time.sleep(1)
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print("\nStopped by user")
            self.running = False
        finally:
            listener.stop()

if __name__ == "__main__":
    # Configuration
    BUTTON_IMAGES_FOLDER = "button_images"  # Folder where button images are stored
    CONFIDENCE_LEVEL = 0.8  # Matching confidence (0-1)
    CHECK_INTERVAL = 1  # Seconds between checks
    
    # Create and run the button clicker
    try:
        clicker = ButtonClicker(
            button_images_folder=BUTTON_IMAGES_FOLDER,
            confidence=CONFIDENCE_LEVEL,
            check_interval=CHECK_INTERVAL
        )
        clicker.run()
    except Exception as e:
        print(f"Error: {e}")

# Install pynput if not already installed
try:
    from pynput import mouse
except ImportError:
    import pip
    pip.main(['install', 'pynput'])