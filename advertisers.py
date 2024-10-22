from google.cloud import bigquery
import json

def upsert_advertiser(name, sourceAdvertiserId):
    """Checks to see if an advertiser exists and returns that ID.

    Args:
        name of the advertiser from the OMS
        sourceAdvertiserId of the advertiser from the OMS

    Returns:
        advertiserId: The ID of the advertiser in the OMS system. 0 if not found.
    """
    advertiser_id = 0

    # Get a reference to the BigQuery client and dataset
    bigquery_client = bigquery.Client()

    # Construct the BigQuery query
    query = f"""
    SELECT id, name
    FROM `aos-demo-toolkit.orders.advertisers`
    WHERE oms_id = '{sourceAdvertiserId}'
    LIMIT 1
    """

    # Run the query
    query_job = bigquery_client.query(query)
    results = query_job.result()
    try:
        first_row = next(results)
        advertiser_id = int(first_row[0])
        if first_row[1] != name:
            print(f"Advertiser name mismatch, updating in database: {first_row[1]} != {name}")
            # Update the advertiser name in BigQuery
            update_query = f"""
            UPDATE `aos-demo-toolkit.orders.advertisers`
            SET name = '{name}'
            WHERE id = {advertiser_id}
            """
            update_job = bigquery_client.query(update_query)
            update_job.result()  # Wait for the update to complete
        print(f"Advertiser found with id {advertiser_id}")
    except StopIteration:
        # Advertiser not found
        # Find the maximum value in the id column
        max_id_query = """
        SELECT MAX(id) as max_id
        FROM `aos-demo-toolkit.orders.advertisers`
        """
        max_id_job = bigquery_client.query(max_id_query)
        max_id_result = max_id_job.result()
        max_id = next(max_id_result)["max_id"] or 0

        # Insert a new row into the table
        new_id = max_id + 1
        insert_query = f"""
        INSERT INTO `aos-demo-toolkit.orders.advertisers` (id, name, oms_id)
        VALUES ({new_id}, '{name}', '{sourceAdvertiserId}')
        """
        insert_job = bigquery_client.query(insert_query)
        insert_job.result()  # Wait for the insert to complete

        advertiser_id = new_id
        print(f"New advertiser inserted with id {advertiser_id}")
    return advertiser_id

def main(request):

    if request.is_json:
        # Get the JSON data
        request_json = request.get_json()

        advertiser_id = upsert_advertiser(request_json.get("name"), request_json.get("sourceAdvertiserId"))

        # Replace values in response JSON
        response_json = {
            "advertiserId": advertiser_id,
            "sourceAdvertiserId": request_json.get("sourceAdvertiserId"),
        }

        return response_json
    else:
        # Handle non-JSON requests (optional)
        return "Request is not a JSON object"