import functions_framework
from flask import Response
from google.cloud import storage
import json
import datetime
import uuid

@functions_framework.http
def hello_http(request):
    """Main Cloud Function that saves the request to a file and dispatches requests based on the URL path.

    Args:
        request (flask.Request): The request object.

    Returns:
        str: The response from the called function.
    """

    # Get a reference to the GCS bucket and folder
    bucket_name = "aos-demo-toolkit"  # Replace with your bucket name
    folder_name = "requests"
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    # Extract data from the request and save in readable format
    try:
        # Get the JSON data
        request_json = request.get_json()

        # Generate a timestamp for the filename
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        short_uuid = str(uuid.uuid4())[:8]

        # Create a filename with the timestamp
        filename = f"request_{timestamp}_{short_uuid}.json"

        # Construct the full path within the bucket
        blob = bucket.blob(f"{folder_name}/{filename}")

        # Create a dictionary to hold the entire request data
        request_data = {
            "path": request.path,
            "headers": dict(request.headers),
            "json": request_json
        }

        # Save the request data to the GCS bucket
        blob.upload_from_string(
            data=json.dumps(request_data),
            content_type='application/json'
        )

        # Get the function name from the request URL
        function_name = request.path.split("/")[-1]

        # Define a dictionary mapping function names to modules
        functions = {
            "inventory": "inventory.main",  # Module name and function name
            "advertisers": "advertisers.main",
            "orders": "orders.main"
        }

        # Import the corresponding module dynamically
        if function_name in functions:
            module_name, function_name = functions[function_name].rsplit(".", 1)
            imported_module = __import__(module_name)
            function = getattr(imported_module, function_name)
            # Call the function with the request
            response = function(request)

            folder_name = "responses"

            # Store the response in a file
            try:
                # Create a filename with the timestamp
                filename = f"response_{timestamp}_{short_uuid}.json"

                # Construct the full path within the bucket
                blob = bucket.blob(f"{folder_name}/{filename}")

                # Upload the entire request data in a readable format
                blob.upload_from_string(json.dumps(response, indent=2))
            except Exception as e:
                error_response = Response(json.dumps({"error": str(e)}), status=500, mimetype='application/json')
                return error_response

            # Return the response as JSON
            json_response = Response(json.dumps(response), status=200, mimetype='application/json')
            return json_response
        else:
            error_response = Response(json.dumps({"error": "Function not found"}), status=404, mimetype='application/json')
            return error_response

    except Exception as e:
        error_response = Response(json.dumps({"error": str(e)}), status=500, mimetype='application/json')
        return error_response
