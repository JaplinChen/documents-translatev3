import argparse
import json
import sys

from backend.services.pptx_apply import apply_chinese_corrections

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply Chinese corrections to a PPTX."
    )
    parser.add_argument("--in", dest="pptx_in", required=True)
    parser.add_argument("--out", dest="pptx_out", required=True)
    parser.add_argument("--blocks", dest="blocks_path", required=True)
    parser.add_argument("--line-dash", dest="line_dash", default=None)
    args = parser.parse_args()

    try:
        with open(args.blocks_path, encoding="utf-8") as handle:
            blocks = json.load(handle)
    except OSError as exc:
        print(f"Failed to read blocks file: {exc}", file=sys.stderr)
        return 1

    apply_chinese_corrections(
        args.pptx_in,
        args.pptx_out,
        blocks,
        line_dash=args.line_dash,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
