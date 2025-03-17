# Credentials API Documentation

## Overview

The Credentials API provides a service for transforming JSON-formatted credentials into a standardized string format to be entered as the username and password in Named Credentials for an External System using Adsrv. It takes a JSON payload containing the API and FTP credential information for that tenant and External System and converts it into concatenated strings suitable for authentication. 

The FTP credentials should match an FTP folder to be used to process primary delivery after order pushes. The same credentials should be entered in a Named Credential and set as the Named Credentials for the Delivery Pull Operation on the External System > Operation Settings.

The API credentials should match an active user for the tenant that has API access and sufficient access to AOS to get External System information and trigger Integration Manager jobs. Recommended roles for the user are Administrator and API Manager.

The Production System Name should match the name of the External System set up for Adsrv (case sensitive).

The resulting username and password should be entered exactly (copy and paste) into an API JSON Named Credential as the User ID and Password. This Named Credential is to be set as the Default Named Credentials in the Default Connection Setting of the Adsrv External System.

## Endpoint

```
POST /creds
```

## Request Format

Send a POST request with a JSON body containing all required credential fields:

```json
{
  "api_user": "username@example.com",
  "api_pass": "your_api_password",
  "api_key": "your-api-key-uuid",
  "api_tenant_name": "tenant_name",
  "production_system_name": "system_name",
  "ftp_user": "ftp_username",
  "ftp_pass": "ftp_password",
  "ftp_host": "ftp.example.com",
  "ftp_folder": "/path/to/folder"
}
```

### Required Fields

| Field | Description |
|-------|-------------|
| api_user | API username |
| api_pass | API password |
| api_key | API key or token |
| api_tenant_name | Tenant name |
| production_system_name | Name of the external system (case sensitive) |
| ftp_user | FTP username |
| ftp_pass | FTP password |
| ftp_host | FTP host address |
| ftp_folder | FTP folder path |

## Response Format

Upon successful processing, the API returns a JSON response with the formatted credentials:

```json
{
  "username": "api_user||api_tenant_name||production_system_name||ftp_user||ftp_host||ftp_folder",
  "password": "api_pass||api_key||ftp_pass"
}
```

## Examples

### Example Request

```bash
curl -X POST https://your-cloud-function-url/creds \
  -H "Content-Type: application/json" \
  -d '{
    "ftp_user": "fs_mm_dj.s",
    "ftp_pass": "CFCsMVkVljCTGA==",
    "ftp_host": "ftp.operativeone.com",
    "ftp_folder": "/adsrv_delivery",
    "api_user": "external_system@digitalsandbox04.com",
    "api_pass": "xzt*ykq2BAM.hbg2uem",
    "api_key": "613169f8-9634-41da-a007-13b6e45d99bb",
    "api_tenant_name": "digitalsandbox04",
    "production_system_name": "Adsrv"
  }'
```

### Example Response

```json
{
  "username": "external_system@digitalsandbox04.com||digitalsandbox04||Adsrv||fs_mm_dj.s||ftp.operativeone.com||/adsrv_delivery",
  "password": "xzt*ykq2BAM.hbg2uem||613169f8-9634-41da-a007-13b6e45d99bb||CFCsMVkVljCTGA=="
}
```

## Error Handling

If an error occurs, the API will return a JSON response with an error message:

```json
{
  "error": "Error message details"
}
```

### Common Errors

| Error | Description |
|-------|-------------|
| Missing required credential field | One or more required fields are missing from the request |
| No JSON data provided in the request | The request body is empty or not valid JSON |

## Usage Notes

- All fields are required. Missing fields will result in an error.
- The API preserves the original values but formats them into concatenated strings.
- Special characters in credentials are preserved.
- The formatted strings use double pipe symbols (`||`) as separators. Double pipes must be avoided in all values, including passwords.
