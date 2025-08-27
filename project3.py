import requests
import csv
import json
import os

BASE_URL = "https://xg4moshwx0.execute-api.us-west-2.amazonaws.com/dev"

def get_json(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

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

        # Write to CSV
        csv_file = os.path.join(output_folder, f"{region}_data_centers.csv")
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=output_data[0].keys())
            writer.writeheader()
            writer.writerows(output_data)

        print(f"Data for georegion '{region}' written to {csv_file}")

if __name__ == "__main__":
    main()