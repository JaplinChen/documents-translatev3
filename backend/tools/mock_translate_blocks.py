import argparse
import json
import sys

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mock-translate extracted blocks."
    )
    parser.add_argument("--in", dest="blocks_in", required=True)
    parser.add_argument("--out", dest="blocks_out", required=True)
    args = parser.parse_args()

    try:
        with open(args.blocks_in, encoding="utf-8") as handle:
            blocks = json.load(handle)
    except OSError as exc:
        print(f"Failed to read blocks file: {exc}", file=sys.stderr)
        return 1

    for block in blocks:
        source_text = block.get("source_text", "")
        block["translated_text"] = f"TR:{source_text}" if source_text else ""

    try:
        with open(args.blocks_out, "w", encoding="utf-8") as handle:
            json.dump(blocks, handle, ensure_ascii=True, indent=2)
            handle.write("\n")
    except OSError as exc:
        print(f"Failed to write blocks file: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
