# Adds-Skiper

Automated button clicker using image recognition and mouse control.

## Features
- Detects buttons on screen using PNG image matching
- Clicks detected buttons automatically
- Pause/resume program with right mouse button

## Setup

1. **Install requirements:**
    ```sh
    pip install -r requirements.txt
    ```
2. **Place button images** in the `button_images` folder.

## Usage

- **Run the script:**
    ```sh
    python main.py
    ```
- **Pause/resume:** Right-click anywhere on the screen.

## Creating an EXE

- **Basic build:**
    ```sh
    pyinstaller --onefile main.py
    ```
- **Build with a custom icon:**
    ```sh
    pyinstaller --onefile --icon=app.ico main.py
    ```
    > Make sure your `app.ico` file is in the project folder.

- If your script uses images or other files, make sure they are accessible to the EXE (e.g., copy the `button_images` folder next to the EXE).

## Requirements

See `requirements.txt`.