import csv
import json
import os
from google.cloud import bigquery
import datetime
import random
from google.cloud import secretmanager
import ftplib
import requests
import base64

def generate_delivery_data(order_id, basic_auth):
    client = bigquery.Client()

    # Decode the basic_auth parameter
    encoded_auth = basic_auth.split(" ")[1]
    decoded_auth = base64.b64decode(encoded_auth).decode('utf-8')
    user_info, password_info = decoded_auth.split(':')
    api_user, api_tenant_name, production_system_name, ftp_user, ftp_host, ftp_folder = user_info.split('||')
    print(f"API User: {api_user}, API Tenant Name: {api_tenant_name}, Production System Name: {production_system_name}, FTP User: {ftp_user}, FTP Host: {ftp_host}, FTP Folder: {ftp_folder}")
    api_pass, api_key, ftp_pass = password_info.split('||')
    print(f"API Password: {api_pass}, API Key: {api_key}, FTP Password: {ftp_pass}")

    # Query to get the line item details
    query = f"""
    SELECT
        line_items.id AS line_item_id,
        line_items.name AS line_item_name,
        line_items.start_date,
        line_items.end_date,
        line_items.quantity,
        line_items.advertiser_id,
        advertisers.name AS advertiser_name,
        orders.name AS order_name
    FROM `aos-demo-toolkit.orders.line_items` AS line_items
    JOIN `aos-demo-toolkit.orders.advertisers` AS advertisers
    ON line_items.advertiser_id = advertisers.id
    JOIN `aos-demo-toolkit.orders.orders` AS orders
    ON line_items.order_id = orders.id
    WHERE line_items.order_id = {order_id}
    """
    query_job = client.query(query)
    results = query_job.result()
    line_items = []
    for row in results:
        line_item = {
            "line_item_id": row.line_item_id,
            "line_item_name": row.line_item_name,
            "start_date": row.start_date,
            "end_date": row.end_date,
            "advertiser_id": row.advertiser_id,
            "advertiser_name": row.advertiser_name,
            "order_name": row.order_name,
            "quantity": row.quantity
        }
        line_items.append(line_item)

    table_id = "aos-demo-toolkit.delivery.primary_delivery"

    rows_to_insert = []
    csv_rows = []

    current_timestamp = datetime.datetime.now().isoformat()  # Convert to ISO 8601 string

    for line_item in line_items:
        start_date = line_item['start_date']
        end_date = line_item['end_date']
        delta = end_date - start_date

        for i in range(delta.days + 1):
            delivered_date = start_date + datetime.timedelta(days=i)
            # Calculate the delivered quantity per day
            base_quantity_per_day = line_item['quantity'] / (delta.days + 1)
            # Apply a random factor between -10% and +10%
            random_factor = random.uniform(0.9, 1.1)
            delivered_quantity = round(base_quantity_per_day * random_factor)
            row = {
                "delivered_date": delivered_date.strftime('%Y-%m-%d'),
                "advertiser_id": line_item['advertiser_id'],
                "advertiser_name": line_item['advertiser_name'],
                "order_id": order_id,
                "order_name": line_item['order_name'],
                "line_item_id": line_item['line_item_id'],
                "line_item_name": line_item['line_item_name'],
                "line_item_start_date": start_date.strftime('%Y-%m-%d'),
                "line_item_end_date": end_date.strftime('%Y-%m-%d'),
                "line_item_delivered_quantity_1": delivered_quantity,
                "line_item_unit_type_1": "impressions",
                "line_item_delivered_quantity_2": round(delivered_quantity * .1),
                "line_item_unit_type_2": "actions",
                "line_item_delivered_quantity_3": round(delivered_quantity * .01),
                "line_item_unit_type_3": "clicks",
                "inserted_at": current_timestamp
            }
            csv_row = {
                "Delivered Date": delivered_date.strftime('%Y-%m-%d'),
                "Advertiser ID": line_item['advertiser_id'],
                "Advertiser Name": line_item['advertiser_name'],
                "Order ID": order_id,
                "Order Name": line_item['order_name'],
                "Line Item ID": line_item['line_item_id'],
                "Line Item Name": line_item['line_item_name'],
                "Line Item Start Date": start_date.strftime('%Y-%m-%d'),
                "Line Item End Date": end_date.strftime('%Y-%m-%d'),
                "Line Item Delivered Quantity 1": delivered_quantity,
                "Line Item Unit Type 1": "impressions",
                "Line Item Delivered Quantity 2": round(delivered_quantity * .1),
                "Line Item Unit Type 2": "actions",
                "Line Item Delivered Quantity 3": round(delivered_quantity * .01),
                "Line Item Unit Type 3": "clicks",
            }
            rows_to_insert.append(row)
            csv_rows.append(csv_row)

    errors = client.insert_rows_json(table_id, rows_to_insert)

    # Ensure the /tmp directory exists
    tmp_dir = "/tmp"
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    # Generate CSV file
    today_date = datetime.datetime.now().strftime('%Y-%m-%d')
    csv_filename = f"Operative_DeliveryPull_{today_date}.csv"
    csv_file_path = os.path.join(tmp_dir, csv_filename)  # Use /tmp directory for Cloud Run
    
    with open(csv_file_path, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=csv_rows[0].keys())
        writer.writeheader()
        for row in csv_rows:
            writer.writerow(row)
    
    with ftplib.FTP(ftp_host) as ftp:
        ftp.login(user=ftp_user, passwd=ftp_pass)
        ftp.cwd(ftp_folder)  # Change to the specified folder
        with open(csv_file_path, 'rb') as file:
            ftp.storbinary(f'STOR {csv_filename}', file)

    if errors:
        print(f"Encountered errors while inserting rows: {errors}")
    else:
        print("Primary delivery rows have been successfully inserted.")
        trigger_pull_api(csv_filename, api_user, api_pass, api_key, api_tenant_name, production_system_name)

    # Clean up the temporary CSV file
    os.remove(csv_file_path)

    return f"Primary delivery data has been generated and uploaded to FTP server."

def trigger_pull_api(filename, api_user, api_pass, api_key, api_tenant_name, production_system_name):
    environment = os.getenv("ENVIRONMENT")
    print(f"ENVIRONMENT: {environment}")

    api_mayiservice = "https://staging-api.aos.operative.com/mayiservice/tenant/"
    api_envurl = "aos-stg-gw.operativeone.com"

    # Construct the URL for the mayiservice
    url = f"{api_mayiservice}{api_tenant_name}"
    print(f"Mayiservice URL: {url}")

    payload = {
        "expiration": 360,
        "password": api_pass,
        "userId": api_user,
        "apiKey": api_key
    }

    # Make the POST request to get the bearer token
    response = requests.post(url, json=payload)
    response.raise_for_status()  # Raise an exception for HTTP errors

    # Extract the token from the JSON response
    token = response.json().get("token")
    print(f"Bearer Token: {token}")

    # Construct the URL for the GET request to get the production_system_id
    get_url = f"https://{api_envurl}/mdm/v1/{api_key}/psDefinition"
    print(f"GET URL: {get_url}")

    # Make the GET request to get the production_system_id
    headers = {"Authorization": f"Bearer {token}"}
    get_response = requests.get(get_url, headers=headers)
    get_response.raise_for_status()  # Raise an exception for HTTP errors

    # Extract the production_system_id from the JSON response
    ps_definitions = get_response.json()
    production_system_id = next((item["id"] for item in ps_definitions if item["name"] == production_system_name), None)
    print(f"Production System ID: {production_system_id}")

    # Read the payload template from the JSON file
    with open("delivery_pull_trigger_payload.json", "r") as f:
        post_payload_template = f.read()

    # Replace placeholders with actual values
    today_date = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.0')
    end_date = "2025-12-24T12:10:00.0"
    post_payload = post_payload_template.replace("PRODUCTION_SYSTEM_ID", production_system_id)
    post_payload = post_payload.replace("TODAYS_DATE", today_date)
    post_payload = post_payload.replace("END_DATE", end_date)

    # Convert the modified payload back to a dictionary
    post_payload_dict = json.loads(post_payload)

    # Construct the URL for the POST request to trigger the delivery pull
    post_url = f"https://{api_envurl}/ingress/v2/{api_key}/ingest/inlinePayload"
    print(f"POST URL: {post_url}")

    # Make the POST request to trigger the delivery pull
    post_response = requests.post(post_url, json=post_payload_dict, headers=headers)
    post_response.raise_for_status()  # Raise an exception for HTTP errors

    job_id = post_response.json().get("jobId")

    print("Delivery pull triggered successfully with job ID:", job_id)
    return job_id