import glob
import os
import shutil

def clean_workspace():
    # 1. Python Cache
    for root, dirs, _files in os.walk("."):
        if "__pycache__" in dirs:
            shutil.rmtree(os.path.join(root, "__pycache__"))
            print(f"Deleted: {os.path.join(root, '__pycache__')}")

    for pyc in glob.glob("**/*.pyc", recursive=True):
        os.remove(pyc)
        print(f"Deleted: {pyc}")

    # 2. Build Artifacts
    artifacts = [
        "frontend/dist",
        "ai-router-package-win.zip",
        "ai-router-package.zip",
        "backend/build",
        "backend/dist",
        "*.spec",
    ]

    for path in artifacts:
        resolved = glob.glob(path, recursive=True)
        for p in resolved:
            try:
                if os.path.isfile(p):
                    os.remove(p)
                elif os.path.isdir(p):
                    shutil.rmtree(p)
                print(f"Deleted: {p}")
            except Exception as e:
                print(f"Error deleting {p}: {e}")

    # 3. Logs
    for log in glob.glob("**/*.log", recursive=True):
        os.remove(log)
        print(f"Deleted: {log}")

    print("Cleanup complete.")


if __name__ == "__main__":
    clean_workspace()
