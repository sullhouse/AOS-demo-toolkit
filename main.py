import functions_framework
from google.cloud import storage
import json
import datetime

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

        # Create a filename with the timestamp
        filename = f"request_{timestamp}.json"

        # Construct the full path within the bucket
        blob = bucket.blob(f"{folder_name}/{filename}")

        # Create a dictionary to hold the entire request data
        request_data = {
            "path": request.path,
            "headers": dict(request.headers),
            "json": request_json
        }

        # Upload the entire request data in a readable format
        blob.upload_from_string(json.dumps(request_data, indent=2))
    except Exception as e: 
        return f"An error occurred while trying to save request to GCS: {e}"
    
    # Get the function name from the request URL
    function_name = request.path.split("/")[-1]

    # Define a dictionary mapping function names to modules
    functions = {
        "inventory": "inventory.main",  # Module name and function name
        "advertisers": "advertisers.main",  # Module name and function name
        # Add more functions as needed (e.g., "orders": "orders.handle_order")
    }

    # Import the corresponding module dynamically
    if function_name in functions:
        module_name, function_name = functions[function_name].rsplit(".", 1)
        imported_module = __import__(module_name)
        function = getattr(imported_module, function_name)
        # Call the function with the request
        return function(request)
    else:
        return f"Function '{function_name}' not found"