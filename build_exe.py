import os
import subprocess
import site
import sys

def build_executable():
    print("Preparing to build Acadence as a Windows Executable...")
    
    # Ensure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Find customtkinter installation path so we can bundle its assets (fonts, themes, etc.)
    import customtkinter
    ctk_path = os.path.dirname(customtkinter.__file__)
    
    # We must also bundle tkcalendar if necessary, but usually it compiles fine.
    
    print(f"Found CustomTkinter at: {ctk_path}")
    
    # PyInstaller command arguments
    # --onedir is better than --onefile for large AI projects because --onefile takes 
    # forever to extract PyTorch to a temp folder every time the user opens the app.
    args = [
        "pyinstaller",
        "--noconfirm",
        "--onedir",
        "--windowed", # Removes the background console window
        "--name", "Acadence",
        f"--add-data", f"{ctk_path};customtkinter/",
        "--add-data", "database/schema.sql;database/",
        "--add-data", "assets;assets/",
        "main.py"
    ]
    
    print("\nRunning PyInstaller... This may take 5-15 minutes because it is bundling the PyTorch/Whisper AI engine.")
    print("Please do not close this window...\n")
    
    try:
        # Run pyinstaller
        subprocess.check_call(args)
        print("\n=======================================================")
        print("BUILD SUCCESSFUL!")
        print("Your executable is located in the 'dist/Acadence' folder.")
        print("You can double-click 'Acadence.exe' to run the app!")
        print("=======================================================")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error code {e.returncode}")

if __name__ == "__main__":
    build_executable()
