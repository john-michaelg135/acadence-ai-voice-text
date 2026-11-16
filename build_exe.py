import os
import subprocess
import sys


def build_executable():
    print("Preparing to build Acadence as a Windows Executable...")

    try:
        import PyInstaller as PyInstaller
    except ImportError as exc:
        raise RuntimeError(
            "Install build tools with: python -m pip install -r requirements-dev.txt"
        ) from exc

    import customtkinter

    ctk_path = os.path.dirname(customtkinter.__file__)

    print(f"Found CustomTkinter at: {ctk_path}")

    # --onedir is better than --onefile for large AI projects because --onefile takes
    # forever to extract PyTorch to a temp folder every time the user opens the app.
    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name",
        "Acadence",
        "--add-data",
        f"{ctk_path};customtkinter/",
        "--add-data",
        "database/schema.sql;database/",
        "--add-data",
        "assets;assets/",
        "main.py",
    ]

    print(
        "\nRunning PyInstaller... This may take 5-15 minutes because it is bundling the PyTorch/Whisper AI engine."
    )
    print("Please do not close this window...\n")

    try:
        subprocess.check_call(args, cwd=os.path.dirname(os.path.abspath(__file__)))
        print("\n=======================================================")
        print("BUILD SUCCESSFUL!")
        print("Your executable is located in the 'dist/Acadence' folder.")
        print("You can double-click 'Acadence.exe' to run the app!")
        print("=======================================================")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error code {e.returncode}")
        raise


if __name__ == "__main__":
    build_executable()
