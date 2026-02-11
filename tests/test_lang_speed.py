import time
from backend.services.language_detect import detect_language

blocks_count = 1386
sample_text = "This is a sample text for testing language detection performance."

start = time.perf_counter()
for i in range(blocks_count):
    detect_language(f"{sample_text} {i}")  # Use different text to avoid cache
duration = time.perf_counter() - start

print(f"Detected {blocks_count} blocks in {duration:.4f}s")
print(f"Average: {(duration / blocks_count) * 1000:.4f}ms per block")
