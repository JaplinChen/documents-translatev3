
import pytest

pytest.skip("此檔為手動測試腳本，需啟動後端與樣本檔案，測試時略過", allow_module_level=True)

import requests

API_BASE = "http://localhost:5002"

def test_extract(file_path, file_type):
    url = f"{API_BASE}/api/{file_type}/extract"
    files = {'file': open(file_path, 'rb')}
    response = requests.post(url, files=files)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {file_type.upper()} Extract Success!")
        print(f"   Blocks count: {len(data.get('blocks', []))}")
        if 'sheet_count' in data:
            print(f"   Sheets: {data['sheet_count']}")
        if 'page_count' in data:
            print(f"   Pages: {data['page_count']}")
    else:
        print(f"❌ {file_type.upper()} Extract Failed: {response.text}")

if __name__ == "__main__":
    # Note: This test requires a running backend and sample files.
    # Since I cannot run the backend in a long-lived process here,
    # this script is for the user or manual verification.
    print("Test script ready. Please ensure backend is running at http://localhost:5002")
