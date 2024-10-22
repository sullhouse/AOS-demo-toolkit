from google.cloud import bigquery
import json
import datetime
import random


def get_inventory_data(start_date, end_date, targets):
    """Generates capacityCount, bookedCount, and availableCount for a date range.

    Args:
        start_date (str): The start date in YYYY-MM-DD format.
        end_date (str): The end date in YYYY-MM-DD format.

    Returns:
        tuple: A tuple containing capacityCount, bookedCount, and availableCount.
    """

    capacity_count = 0
    booked_count = 0

    # Get a reference to the BigQuery client and dataset
    bigquery_client = bigquery.Client()
    
    # Initialize variables
    unit_length = 30
    genres = []
    program_types = []

    # Iterate through the targets
    for target in targets:
        target_name = target.get("targetName")
        target_values = target.get("targetValues")

        if target_name == "Unit Length" and target_values:
            # Assuming "Unit Length" has only one value
            unit_length = int(target_values[0]) 
        elif target_name == "Genre":
            # Extend the genres list with targetValues
            genres.extend(target_values)
        elif target_name == "Program Type":
            # Extend the program_types list with targetValues
            program_types.extend(target_values)

    # Now you have unit_length and genres extracted
    print("Querying Inventory for the following parameters:")
    print("Start Date:", start_date)
    print("End Date:", end_date)
    print("Unit Length:", unit_length)
    print("Genres:", genres)
    print("Program Types:", program_types)

    # Construct the genre string for the WHERE clause
    if genres:
        genre_string = ', '.join([f"'{genre}'" for genre in genres])
        genre_query_string = f"""AND EXISTS (
        SELECT 1
        FROM UNNEST(SPLIT(content_library.genre, ',')) AS genre
        WHERE genre IN ({genre_string})
        )"""
    else:
        genre_query_string = ""

    # Construct the program_type string for the WHERE clause

    if program_types:
        program_type_string = ', '.join([f"'{program_type}'" for program_type in program_types])
        program_type_query_string = f"""AND content_library.program_type = {program_type_string}"""
    else:
        program_type_query_string = ""

    # Construct the BigQuery query
    query = f"""
    SELECT
    CAST(sum(view_factor) * (
        SELECT
            sum(daily_viewership_forecast.viewers)
        FROM
            `aos-demo-toolkit.inventory.daily_viewership_forecast` AS daily_viewership_forecast
        WHERE daily_viewership_forecast.date BETWEEN '{start_date}' AND '{end_date}'
    ) AS INT64) AS total_viewers

    FROM (
    SELECT
        (
        SELECT
            time_viewership_distribution.portion_of_daily_viewers_watching * CAST(block_schedule.air_length / {unit_length} AS INT64)
            FROM
            `aos-demo-toolkit.inventory.time_viewership_distribution` AS time_viewership_distribution
            WHERE time_viewership_distribution.hour = CAST(block_schedule.air_hour AS BIGNUMERIC)
        ) AS view_factor
    FROM
        `aos-demo-toolkit.inventory.block_schedule` AS block_schedule
        INNER JOIN `aos-demo-toolkit.inventory.content_library` AS content_library ON block_schedule.content_id = content_library.content_id
    WHERE block_schedule.block_type = 'Break'
        {genre_query_string}
        {program_type_query_string}
    );
    """

    # Run the query
    query_job = bigquery_client.query(query)
    results = query_job.result()
    try:
        first_row = next(results)
        capacity_count = int(first_row[0])
    except StopIteration:
        capacity_count = 0  # Or handle the case of no results

    # Calculate bookedCount and availableCount
    booked_count = random.randint(int(capacity_count * 0.2), capacity_count) 

    available_count = capacity_count - booked_count

    return capacity_count, booked_count, available_count

def main(request):

    if request.is_json:
        # Get the JSON data
        request_json = request.get_json()

        # Generate a timestamp for the filename
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Create a filename with the timestamp
        filename = f"request_{timestamp}.json"

        # Extract startDate and endDate
        start_date_str = request_json.get("startDate")
        end_date_str = request_json.get("endDate")
        start_date = start_date_str[:10]  # Extract the first 10 characters for the date
        end_date = end_date_str[:10]  # Extract the first 10 characters for the date
       
        # Access the targets array
        targets = request_json.get("targets", [])

        # Generate numbers
        (
            capacity_count,
            booked_count,
            available_count,
        ) = get_inventory_data(start_date, end_date, targets)

        # Replace values in response JSON
        response_json = {
            "inventoryRequestId": request_json.get(
                "inventoryRequestId"
            ),
            "queryType": "SUMMARY",
            "inventorySummary": [
                {
                    "date": None,
                    "capacityCount": capacity_count,
                    "bookedCount": booked_count,
                    "availableCount": available_count,
                }
            ],
            "contenders": None,
        }

        return response_json
    else:
        # Handle non-JSON requests (optional)
        return "Request is not a JSON object"