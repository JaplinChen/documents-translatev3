import sys
import pkg_resources
import os

def check_requirements(requirements_path='requirements.txt'):
    """
    Checks if packages in requirements.txt are installed.
    """
    if not os.path.exists(requirements_path):
        print(f"Error: {requirements_path} not found.")
        sys.exit(1)

    print(f"Checking requirements from: {requirements_path}")
    
    with open(requirements_path, 'r') as f:
        # Parse requirements, ignoring comments and empty lines
        requirements = []
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Handle version specifiers typically found in requirements.txt
            # e.g., "fastapi==0.68.0" -> "fastapi"
            # Also handle >=, <=, etc.
            pkg_name = line.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0].strip()
            requirements.append(pkg_name)

    missing = []
    # Get all installed packages
    installed = {pkg.key.lower() for pkg in pkg_resources.working_set}

    for req in requirements:
        req_lower = req.lower()
        if req_lower not in installed:
            # Special mapping for frequent mismatches if needed (e.g. PIL -> Pillow)
            # But usually pip freeze > requirements.txt handles this.
            # python-docx is installed as python-docx but imported as docx, 
            # however pkg_resources checks distribution names, so python-docx is correct.
            missing.append(req)

    if missing:
        print(f"Missing packages: {', '.join(missing)}")
        print("Please run:")
        print(f"pip install -r {requirements_path}")
        sys.exit(1)
    
    print("All requirements satisfied.")

if __name__ == "__main__":
    check_requirements()
