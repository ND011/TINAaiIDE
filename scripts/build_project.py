import os
import subprocess
import sys
import shutil

def run_command(command, cwd=None):
    print(f"Executing: {command}")
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=cwd
        )
        for line in process.stdout:
            print(line, end="")
        process.wait()
        return process.returncode == 0
    except Exception as e:
        print(f"Error executing command: {e}")
        return False

def build_react_frontend():
    print("--- Building React Frontend (ai-editor) ---")
    editor_dir = os.path.join(os.getcwd(), "ai-editor")
    
    if not os.path.exists(editor_dir):
        print(f"Error: Editor directory not found at {editor_dir}")
        return False

    # 1. Install dependencies
    print("Installing npm dependencies...")
    if not run_command("npm install", cwd=editor_dir):
        return False

    # 2. Run build
    print("Running vite build...")
    if not run_command("npm run build", cwd=editor_dir):
        return False

    print("Frontend build successful.")
    return True

def package_python_app():
    print("--- Packaging Python Application ---")
    # This is a placeholder for PyInstaller or similar packaging logic
    # For now, we'll just verify requirements.txt exists
    if os.path.exists("requirements.txt"):
        print("requirements.txt found. Verifying environment...")
        run_command("pip install -r requirements.txt")
    
    print("Python packaging step complete.")
    return True

def main():
    print("========================================")
    print("   Tina AI IDE - Master Build System")
    print("========================================\n")

    # Ensure build directory exists
    if not os.path.exists("dist"):
        os.makedirs("dist")

    success = True
    
    # Optional frontend build
    if os.path.exists("ai-editor"):
        if not build_react_frontend():
            success = False

    # App packaging
    if success:
        if not package_python_app():
            success = False

    if success:
        print("\nBUILD SUCCESSFUL!")
    else:
        print("\nBUILD FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
