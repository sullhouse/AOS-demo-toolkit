from google.cloud import bigquery
import datetime
import random

def generate_delivery_data(order_id):
    client = bigquery.Client()

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
            rows_to_insert.append(row)

    errors = client.insert_rows_json(table_id, rows_to_insert)

    if errors:
        print(f"Encountered errors while inserting rows: {errors}")
    else:
        print("Primary delivery rows have been successfully inserted.")