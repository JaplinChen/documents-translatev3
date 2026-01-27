import json
import sys

from backend.services.pptx_extract import extract_blocks

def main() -> int:
    if len(sys.argv) != 2:
        print(
            "Usage: python -m backend.tools.extract_pptx <path-to-pptx>",
            file=sys.stderr,
        )
        return 1
    pptx_path = sys.argv[1]
    blocks = extract_blocks(pptx_path)
    json.dump(blocks, sys.stdout, ensure_ascii=True, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
