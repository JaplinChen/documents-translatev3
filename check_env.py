import pkg_resources
import sys


def check_requirements(requirements_file="requirements.txt"):
    with open(requirements_file, "r") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    missing = []
    for req in requirements:
        try:
            # Handle cases with version specs
            pkg_name = (
                req.split("==")[0].split(">=")[0].split("<=")[0].split(">")[0].split("<")[0].strip()
            )
            pkg_resources.require(req)
        except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
            missing.append(req)

    if missing:
        print(f"Missing or mismatched packages: {', '.join(missing)}")
        return False
    return True


if __name__ == "__main__":
    if check_requirements():
        print("All requirements are satisfied.")
        sys.exit(0)
    else:
        sys.exit(1)
