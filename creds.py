import json

def format_credentials(creds):
    """
    Format credentials in the specified format.
    
    Args:
        creds (dict): Credentials dictionary
    
    Returns:
        tuple: (user_string, pass_string) formatted as requested
    """
    try:
        # Format user string: api_user||api_tenant_name||production_system_name||ftp_user||ftp_host||ftp_folder
        user_string = f"{creds['api_user']}||{creds['api_tenant_name']}||{creds['production_system_name']}||{creds['ftp_user']}||{creds['ftp_host']}||{creds['ftp_folder']}"
        
        # Format password string: api_pass||api_key||ftp_pass
        pass_string = f"{creds['api_pass']}||{creds['api_key']}||{creds['ftp_pass']}"
        
        return user_string, pass_string
    except KeyError as e:
        raise Exception(f"Missing required credential field: {str(e)}")

def main(request):
    """
    Main function that processes credentials sent via API request.
    
    Args:
        request (flask.Request): The request object containing credentials in JSON format
    
    Returns:
        dict: Dictionary containing the formatted credentials
    """
    try:
        # Extract credentials from the request JSON
        request_json = request.get_json()
        if not request_json:
            return {
                "error": "No JSON data provided in the request"
            }
        
        # Format the credentials
        user_string, pass_string = format_credentials(request_json)
        
        # Return the formatted credentials in the requested format
        return {
            "username": user_string,
            "password": pass_string
        }
    except Exception as e:
        return {
            "error": str(e)
        }
