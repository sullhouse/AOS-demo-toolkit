from google.cloud import bigquery
from datetime import datetime
import delivery
import threading
import time

def delayed_generate_delivery_data(order_id, basic_auth):
    time.sleep(5)  # Wait for 5 seconds
    delivery.generate_delivery_data(order_id, basic_auth)

def upsert_order(name, order_id, oms_id, start_date, end_date, advertiser_id, salesperson_email_id, salesperson_name):
    bigquery_client = bigquery.Client()
    table_id = "aos-demo-toolkit.orders.orders"
    
    order_exists = False

    if order_id > 0:
        # Check if the order_id exists
        query = f"""
        SELECT *
        FROM `aos-demo-toolkit.orders.orders`
        WHERE id = {order_id}
        LIMIT 1
        """

        # Run the query
        query_job = bigquery_client.query(query)
        results = query_job.result()
        for row in results:
            order_exists = True

    # Modify dates to datetime
    start_date_dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M:%S")
    end_date_dt = datetime.strptime(end_date, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M:%S")

    if order_exists:
        # Update the existing row
        query = f"""
            UPDATE `{table_id}`
            SET name = '{name}',
                oms_id = '{oms_id}',
                start_date = '{start_date_dt}',
                end_date = '{end_date_dt}',
                advertiser_id = {advertiser_id},
                salesperson_email_id = '{salesperson_email_id}',
                salesperson_name = '{salesperson_name}'
            WHERE id = {order_id}
        """
        # Run the query
        query_job = bigquery_client.query(query)
        results = query_job.result()
    else:
        # Find the maximum value in the id column
        max_id_query = """
        SELECT MAX(id) as max_id
        FROM `aos-demo-toolkit.orders.orders`
        """
        max_id_job = bigquery_client.query(max_id_query)
        max_id_result = max_id_job.result()
        max_id = next(max_id_result)["max_id"] or 0

        # Insert a new row into the table
        new_id = max_id + 1
        insert_query = f"""
        INSERT INTO `aos-demo-toolkit.orders.orders` (id, name, oms_id, start_date, end_date, advertiser_id, salesperson_email_id, salesperson_name)
        VALUES ({new_id}, '{name}', '{oms_id}', '{start_date_dt}', '{end_date_dt}', CAST('{advertiser_id}' AS INT64), '{salesperson_email_id}', '{salesperson_name}')
        """
        insert_job = bigquery_client.query(insert_query)
        insert_job.result()  # Wait for the insert to complete

        order_id = new_id
        print(f"New order inserted with id {order_id}")

    return order_id

def upsert_lineitem(name, lineitem_id, oms_id, start_date, end_date, cost_type, quantity, unit_cost, order_id, advertiser_id):
    """Checks to see if a lineitem exists and returns that ID.

    Args:
        name of the lineitem from the OMS
        lineitem_id of the lineitem from adsrv
        sourceLineitemId of the lineitem from the OMS
        start_date of the lineitem
        end_date of the lineitem
        cost_method of the lineitem
        quantity of the lineitem
        unit_cost of the lineitem

    Returns:
        lineitemId: The ID of the lineitem in the OMS system. 0 if not found.
    """
    
    # Get a reference to the BigQuery client and dataset
    bigquery_client = bigquery.Client()
    
    # Modify dates
    start_date_dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M:%S")
    end_date_dt = datetime.strptime(end_date, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M:%S")
    
    lineitem_exists = False

    if lineitem_id > 0:
        # Check if the lineitem_id exists
        query = f"""
        SELECT *
        FROM `aos-demo-toolkit.orders.line_items`
        WHERE id = {lineitem_id}
        LIMIT 1
        """

        # Run the query
        query_job = bigquery_client.query(query)
        results = query_job.result()
        for row in results:
            lineitem_exists = True

    if lineitem_exists:
        # Update the existing row
        table_id = "aos-demo-toolkit.orders.line_items"
        query = f"""
            UPDATE `{table_id}`
            SET name = '{name}',
                oms_id = '{oms_id}',
                start_date = '{start_date_dt}',
                end_date = '{end_date_dt}',
                cost_method = '{cost_type}',
                quantity = CAST('{quantity}' AS INT64),
                unit_cost = CAST('{unit_cost}' AS FLOAT64),
                order_id = {order_id},
                advertiser_id = {advertiser_id}
            WHERE id = {lineitem_id}
        """
        # Run the query
        query_job = bigquery_client.query(query)
        results = query_job.result()
        lineitem = {
            "lineitemId": str(lineitem_id),
            "sourceLineitemId": oms_id,
            "name": name,
            "status": "success",
            "errorMessage": None
        }
    else:
        # Lineitem not found
        # Find the maximum value in the id column
        max_id_query = """
        SELECT MAX(id) as max_id
        FROM `aos-demo-toolkit.orders.line_items`
        """
        max_id_job = bigquery_client.query(max_id_query)
        max_id_result = max_id_job.result()
        max_id = next(max_id_result)["max_id"] or 0

        # Insert a new row into the table
        new_id = max_id + 1
        insert_query = f"""
        INSERT INTO `aos-demo-toolkit.orders.line_items` (id, name, oms_id, start_date, end_date, cost_method, quantity, unit_cost, order_id, advertiser_id)
        VALUES ({new_id}, '{name}', '{oms_id}', '{start_date_dt}', '{end_date_dt}', '{cost_type}', CAST('{quantity}' AS INT64), CAST('{unit_cost}' AS FLOAT64), {order_id}, {advertiser_id})
        """
        insert_job = bigquery_client.query(insert_query)
        insert_job.result()  # Wait for the insert to complete

        lineitem_id = new_id
        print(f"New lineitem inserted with id {lineitem_id}")
        lineitem = {
            "lineitemId": str(lineitem_id),
            "sourceLineitemId": oms_id,
            "name": name,
            "status": "success",
            "errorMessage": None
        }
    return lineitem

def main(request):
    if request.is_json:
        # Get the JSON data
        request_json = request.get_json()

        order_id = request_json.get("orderId")
        if not order_id:
            order_id = 0

        order_id = upsert_order(
            request_json.get("name"),
            int(order_id),
            request_json.get("sourceOrderId"),
            request_json.get("startDate"),
            request_json.get("endDate"),
            request_json.get("advertiserId"),
            request_json.get("salesPersonEmailId"),
            request_json.get("salesPersonName")
        )

        advertiser_id = request_json.get("advertiserId")

        lineitems = []
        for lineitem in request_json.get("lineitems"):
            lineitem_id = lineitem.get("lineitemId")
            
            if not lineitem_id:
                lineitem_id = 0
            
            lineitems.append(upsert_lineitem(
                lineitem.get("name"),
                int(lineitem_id),
                lineitem.get("sourceLineitemId"),
                lineitem.get("startDate"),
                lineitem.get("endDate"),
                lineitem.get("costType"),
                int(lineitem.get("quantity")),
                float(lineitem.get("unitCost")),
                order_id,
                advertiser_id
            ))

        # Start the background thread to generate delivery data
        basic_auth = request.headers.get("Authorization")
        threading.Thread(target=delayed_generate_delivery_data, args=(order_id, basic_auth)).start()

        # Replace values in response JSON
        response_json = {
            "orderId": order_id,
            "lineitems": lineitems
        }

        return response_json
    else:
        return {"error": "Invalid request"}, 400