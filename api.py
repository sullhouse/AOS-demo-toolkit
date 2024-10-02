import functions_framework

@functions_framework.http
def hello_http(request):
  """Main Cloud Function that dispatches requests based on the URL path.

  Args:
      request (flask.Request): The request object.

  Returns:
      str: The response from the called function.
  """

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