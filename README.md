# OC Project 3

Minimal Python script that fetches data from an API and writes CSVs per geo-region.

## Quick start

1. Create a virtual environment
2. Install dependencies
3. Run the script

### Setup (macOS/Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Run

```bash
python project3.py
```

CSV files will be created in `output_data/`.

### Notes
- Requires internet access for the API calls.
- Customize `BASE_URL` in `project3.py` if the API endpoint changes.
