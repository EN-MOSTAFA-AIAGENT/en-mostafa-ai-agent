# Reverse Image Search & Download Script (Power Mode)
# Uses external reference path provided by user

import os
from pathlib import Path

REF_DIR = Path(r"C:\\Users\\Mostafa\\Desktop\\New folder (2)")
OUT_DIR = Path(r"C:\\mcp-agent\\Product_Images")

print("[INFO] Reverse Image Runner started")
print(f"[INFO] Reference images path: {REF_DIR}")
print(f"[INFO] Output path: {OUT_DIR}")

if not REF_DIR.exists():
    print("[ERROR] Reference directory does not exist")
    raise SystemExit(1)

images = list(REF_DIR.glob('*'))
print(f"[INFO] Found {len(images)} reference files")

# Execution pipeline placeholder – visual search & download next
print("[INFO] Reference path validated – ready to start downloads")