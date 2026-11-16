import os
import subprocess
import sys
from pathlib import Path


def build_executable(onefile=False):
    print("Preparing to build Acadence...")

    try:
        import PyInstaller as PyInstaller
    except ImportError as exc:
        raise RuntimeError(
            "Install build tools with: python -m pip install -r requirements-dev.txt"
        ) from exc

    import customtkinter

    ctk_path = os.path.dirname(customtkinter.__file__)
    root = Path(__file__).resolve().parent

    print(f"Found CustomTkinter at: {ctk_path}")

    # --onedir is better than --onefile for large AI projects because --onefile takes
    # forever to extract PyTorch to a temp folder every time the user opens the app.
    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onefile" if onefile else "--onedir",
        "--windowed",
        "--name",
        "Acadence",
        "--noupx",
        "--specpath",
        str(root / "build"),
        "--add-data",
        f"{ctk_path}{os.pathsep}customtkinter/",
        "--add-data",
        f"{root / 'database' / 'schema.sql'}{os.pathsep}database/",
        "--add-data",
        f"{root / 'assets'}{os.pathsep}assets/",
        "--collect-data",
        "whisper",
        "--hidden-import",
        "PIL._tkinter_finder",
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
        print("Your application is located in the 'dist' folder.")
        print("=======================================================")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error code {e.returncode}")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--onefile", action="store_true")
    build_executable(parser.parse_args().onefile)
