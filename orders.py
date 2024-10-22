from google.cloud import bigquery
import json
from datetime import datetime

def upsert_order(name, sourceOrderId, start_date, end_date, advertiser_id, salesperson_email_id, salesperson_name):
    """Checks to see if an order exists and returns that ID.

    Args:
        name of the order from the OMS
        sourceOrderId of the order from the OMS
        start_date of the order
        end_date of the order
        advertiser_id of the order
        salesperson_email_id of the order

    Returns:
        orderId: The ID of the order in the OMS system. 0 if not found.
    """
    order_id = 0

    # Get a reference to the BigQuery client and dataset
    bigquery_client = bigquery.Client()

    # Construct the BigQuery query
    query = f"""
    SELECT id, name
    FROM `aos-demo-toolkit.orders.orders`
    WHERE oms_id = '{sourceOrderId}'
    LIMIT 1
    """

    # Run the query
    query_job = bigquery_client.query(query)
    results = query_job.result()
    try:
        first_row = next(results)
        order_id = int(first_row[0])
        if first_row[1] != name:
            print(f"Order name mismatch, updating in database: {first_row[1]} != {name}")
            # Update the order name in BigQuery
            update_query = f"""
            UPDATE `aos-demo-toolkit.orders.orders`
            SET name = '{name}'
            WHERE id = {order_id}
            """
            update_job = bigquery_client.query(update_query)
            update_job.result()  # Wait for the update to complete
        print(f"Order found with id {order_id}")
    except StopIteration:
        # Order not found
        # Find the maximum value in the id column
        max_id_query = """
        SELECT MAX(id) as max_id
        FROM `aos-demo-toolkit.orders.orders`
        """
        max_id_job = bigquery_client.query(max_id_query)
        max_id_result = max_id_job.result()
        max_id = next(max_id_result)["max_id"] or 0

        # Modify dates to datetime
        start_date_dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M:%S")
        end_date_dt = datetime.strptime(end_date, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M:%S")

        # Insert a new row into the table
        new_id = max_id + 1
        insert_query = f"""
        INSERT INTO `aos-demo-toolkit.orders.orders` (id, name, oms_id, start_date, end_date, advertiser_id, salesperson_email_id, salesperson_name)
        VALUES ({new_id}, '{name}', '{sourceOrderId}', '{start_date_dt}', '{end_date_dt}', CAST('{advertiser_id}' AS INT64), '{salesperson_email_id}', '{salesperson_name}')
        """
        insert_job = bigquery_client.query(insert_query)
        insert_job.result()  # Wait for the insert to complete

        order_id = new_id
        print(f"New order inserted with id {order_id}")
    return order_id

def upsert_lineitem(name, sourceLineitemId, start_date, end_date, cost_method, quantity, unit_cost):
    """Checks to see if a lineitem exists and returns that ID.

    Args:
        name of the lineitem from the OMS
        sourceLineitemId of the lineitem from the OMS
        start_date of the lineitem
        end_date of the lineitem
        cost_method of the lineitem
        quantity of the lineitem
        unit_cost of the lineitem

    Returns:
        lineitemId: The ID of the lineitem in the OMS system. 0 if not found.
    """
    lineitem_id = 0

    # Get a reference to the BigQuery client and dataset
    bigquery_client = bigquery.Client()

    # Construct the BigQuery query
    query = f"""
    SELECT id, name
    FROM `aos-demo-toolkit.orders.line_items`
    WHERE oms_id = '{sourceLineitemId}'
    LIMIT 1
    """

    # Run the query
    query_job = bigquery_client.query(query)
    results = query_job.result()
    try:
        first_row = next(results)
        lineitem_id = int(first_row[0])
        if first_row[1] != name:
            print(f"Lineitem name mismatch, updating in database: {first_row[1]} != {name}")
            # Update the lineitem name in BigQuery
            update_query = f"""
            UPDATE `aos-demo-toolkit.orders.line_items`
            SET name = '{name}'
            WHERE id = {lineitem_id}
            """
            update_job = bigquery_client.query(update_query)
            update_job.result()  # Wait for the update to complete
        print(f"Lineitem found with id {lineitem_id}")
        lineitem = {
            "lineitemId": str(lineitem_id),
            "sourceLineitemId": sourceLineitemId,
            "status": "success",
            "errorMessage": None
        }
    except StopIteration:
        # Lineitem not found
        # Find the maximum value in the id column
        max_id_query = """
        SELECT MAX(id) as max_id
        FROM `aos-demo-toolkit.orders.line_items`
        """
        max_id_job = bigquery_client.query(max_id_query)
        max_id_result = max_id_job.result()
        max_id = next(max_id_result)["max_id"] or 0

        # Modify dates
        start_date_dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M:%S")
        end_date_dt = datetime.strptime(end_date, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M:%S")

        # Insert a new row into the table
        new_id = max_id + 1
        insert_query = f"""
        INSERT INTO `aos-demo-toolkit.orders.line_items` (id, name, oms_id, start_date, end_date, cost_method, quantity, unit_cost)
        VALUES ({new_id}, '{name}', '{sourceLineitemId}', '{start_date_dt}', '{end_date_dt}', '{cost_method}', CAST('{quantity}' AS INT64), CAST('{unit_cost}' AS FLOAT64))
        """
        insert_job = bigquery_client.query(insert_query)
        insert_job.result()  # Wait for the insert to complete

        lineitem_id = new_id
        print(f"New lineitem inserted with id {lineitem_id}")
        lineitem = {
            "lineitemId": str(lineitem_id),
            "sourceLineitemId": sourceLineitemId,
            "name": name,
            "status": "success",
            "errorMessage": None
        }
    return lineitem

def main(request):

    if request.is_json:
        # Get the JSON data
        request_json = request.get_json()

        order_id = upsert_order(request_json.get("name"), request_json.get("sourceOrderId"), request_json.get("startDate"), request_json.get("endDate"), request_json.get("advertiserId"), request_json.get("salesPersonEmailId"), request_json.get("salesPersonName"))
        
        lineitems = []
        for lineitem in request_json.get("lineitems"):
            lineitems.append(upsert_lineitem(lineitem.get("name"), lineitem.get("sourceLineitemId"), lineitem.get("startDate"), lineitem.get("endDate"), lineitem.get("costType"), int(lineitem.get("quantity")), float(lineitem.get("unitCost"))))


        # Replace values in response JSON
        response_json = {
            "orderId": order_id,
            "sourceOrderId": request_json.get("sourceOrderId"),
            "lineitems": lineitems
        }


        return response_json
    else:
        # Handle non-JSON requests (optional)
        return "Request is not a JSON object"