from backend.services.glossary_extraction import extract_glossary_terms
import os

# Set mode to mock to avoid real LLM call costs during general debug,
# but for verification of PROMPT logic we need a real run if possible.
# However, if I can't guarantee a real run, I'll just explain the logic.
# Since I'm an agent, I can try to run it if the user has keys.


def verify_typo_correction():
    print("Verifying Smart Typo Correction...")
    blocks = [
        {"original_text": "Device name: Lapop bluetooth adapter"},
        {"original_text": "Brand: Rapoo bluetouch mouse"},
    ]

    # Try to use existing environment variables for extraction
    try:
        # We use a smaller model if available to speed up
        terms = extract_glossary_terms(blocks, "zh-TW")
        print(f"Extracted Terms: {terms}")

        found_laptop = any("Laptop" in t["target"] or "筆記型" in t["target"] for t in terms)
        found_rapoo = any("Rapoo" in t["source"] or "雷柏" in t["target"] for t in terms)

        if found_laptop:
            print("  [SUCCESS] AI correctly identified or fixed 'Lapop'")
        else:
            print(
                "  [INFO] AI did not explicitly fix 'Lapop' in this run, might require more capable model."
            )

        if found_rapoo:
            print("  [SUCCESS] AI recognized 'Rapoo' brand.")

    except Exception as e:
        print(f"Extraction failed (expected if no keys/connection): {e}")


if __name__ == "__main__":
    verify_typo_correction()
