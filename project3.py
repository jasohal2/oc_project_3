import requests
import csv
import json
import os
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://xg4moshwx0.execute-api.us-west-2.amazonaws.com/dev"

# Configure a resilient HTTP session with retries and backoff to handle transient TLS/connection issues.
SESSION = requests.Session()
_retry = Retry(
    total=5,
    connect=5,
    read=5,
    backoff_factor=0.6,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=("GET", "HEAD"),
    raise_on_status=False,
)
_adapter = HTTPAdapter(max_retries=_retry, pool_connections=10, pool_maxsize=10)
SESSION.mount("https://", _adapter)
SESSION.mount("http://", _adapter)

def get_json(endpoint, params=None, timeout=(5, 30)):
    url = f"{BASE_URL}/{endpoint}"
    last_exc = None
    for attempt in range(3):
        try:
            response = SESSION.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except (requests.exceptions.SSLError,
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout) as e:
            last_exc = e
            # Exponential backoff
            time.sleep(2 ** attempt)
        except requests.exceptions.HTTPError as e:
            # For HTTP errors not covered by retry rules, re-raise immediately
            raise
    # If we exhausted retries, bubble up the last exception
    raise last_exc

def fetch_georegions():
    response = get_json("geo-regions")
    # If response is a dict with 'body', parse the body
    if isinstance(response, dict) and 'body' in response:
        body = response['body']
        if isinstance(body, str):
            return json.loads(body)
        return body
    return response

def fetch_data_centers():
    response = get_json("data-centers")
    if isinstance(response, dict) and 'body' in response:
        body = response['body']
        if isinstance(body, str):
            return json.loads(body)
        return body
    return response

def fetch_services():
    response = get_json("services")
    if isinstance(response, dict) and 'body' in response:
        body = response['body']
        if isinstance(body, str):
            return json.loads(body)
        return body
    return response

def fetch_computed_metrics(service_name=None, dc_name=None, timestamp="latest"):
    params = {}
    if service_name:
        params['service_name'] = service_name
    if dc_name:
        params['dc_name'] = dc_name
    if timestamp:
        params['timestamp'] = timestamp
    return get_json("metrics/computed", params)

def main():
    georegions = fetch_georegions()
    data_centers = fetch_data_centers()
    services = fetch_services()

    # Organize data centers by georegion
    georegion_map = {g['geo_region_name']: [] for g in georegions}

    # Create output folder if it doesn't exist
    output_folder = "output_data"
    os.makedirs(output_folder, exist_ok=True)

    for dc in data_centers:
        region_name = dc.get('geo_region_name')
        if region_name in georegion_map:
            georegion_map[region_name].append(dc)

    for region, dcs in georegion_map.items():
        output_data = []
        for dc in dcs:
            dc_name = dc.get('dc_name')
            for service in services:
                service_name = service.get('service_name')
                # Add a tiny delay to avoid hammering the API and triggering network/proxy issues
                time.sleep(0.05)
                metrics = fetch_computed_metrics(service_name=service_name, dc_name=dc_name, timestamp="latest")
                # Filter metrics for this dc_name
                dc_metrics = next((m for m in metrics if m.get('dc_name') == dc_name), {})
            
                row = {
                    "Data Center": dc_name,
                    "Service": service_name,
                    "Latitude": dc.get('latitude'),
                    "Longitude": dc.get('longitude'),
                    "City": dc.get('city'),
                    "Status": dc.get('status'),
                    "Provisioned Capacity": dc_metrics.get('provisioned_capacity'),
                    "Utilization %": dc_metrics.get('utilization_percentage'),
                    "Observed Utilization": dc_metrics.get('observed_utilization'),
                }
                output_data.append(row)

        # Write to CSV if we collected any rows
        if output_data:
            csv_file = os.path.join(output_folder, f"{region}_data_centers.csv")
            with open(csv_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=output_data[0].keys())
                writer.writeheader()
                writer.writerows(output_data)
            print(f"Data for georegion '{region}' written to {csv_file}")
        else:
            print(f"No data collected for georegion '{region}'. Skipping CSV generation.")

if __name__ == "__main__":
    main()