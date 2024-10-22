from google.cloud import bigquery
import datetime

def generate_delivery_data(order):
    client = bigquery.Client()

    table_id = "aos-demo-toolkit.delivery.primary_delivery"

    rows_to_insert = []

    for line_item in order['line_items']:
        start_date = datetime.datetime.strptime(line_item['start_date'], '%Y-%m-%d')
        end_date = datetime.datetime.strptime(line_item['end_date'], '%Y-%m-%d')
        delta = end_date - start_date

        for i in range(delta.days + 1):
            delivered_date = start_date + datetime.timedelta(days=i)
            row = {
                "delivered_date": delivered_date.strftime('%Y-%m-%d'),
                "advertiser_id": order['advertiser_id'],
                "advertiser_name": order['advertiser_name'],
                "order_id": order['order_id'],
                "order_name": order['order_name'],
                "line_item_id": line_item['line_item_id'],
                "line_item_name": line_item['line_item_name'],
                "line_item_start_date": line_item['start_date'],
                "line_item_end_date": line_item['end_date'],
                "line_item_delivered_quantity_1": line_item.get('delivered_quantity_1', 0),
                "line_item_unit_type_1": line_item.get('unit_type_1', ''),
                "line_item_delivered_quantity_2": line_item.get('delivered_quantity_2', 0),
                "line_item_unit_type_2": line_item.get('unit_type_2', ''),
                "line_item_delivered_quantity_3": line_item.get('delivered_quantity_3', 0),
                "line_item_unit_type_3": line_item.get('unit_type_3', '')
            }
            rows_to_insert.append(row)

    errors = client.insert_rows_json(table_id, rows_to_insert)
    if errors:
        print(f"Encountered errors while inserting rows: {errors}")
    else:
        print("Rows have been successfully inserted.")
