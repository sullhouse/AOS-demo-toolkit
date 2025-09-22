
from google.cloud import storage
import json
import datetime
from decimal import Decimal
from weasyprint import HTML

def generate_work_order_html(order_data):
    """Generate HTML work order from order JSON data.
    
    Args:
        order_data (dict): Order data in the format of order_sample.json
        
    Returns:
        str: Generated HTML content
    """
    
    # Calculate totals
    total_quantity = sum(item['quantity'] for item in order_data['lineitems'])
    total_cost = sum(item['quantity'] * item['unitCost'] / 1000 for item in order_data['lineitems'])  # CPM calculation
    
    # Generate line items HTML
    line_items_html = ""
    for item in order_data['lineitems']:
        item_cost = item['quantity'] * item['unitCost'] / 1000  # CPM calculation
        line_items_html += f"""
            <tr>
                <td>{item['name']}</td>
                <td>{item['productName']}</td>
                <td>{item['quantity']:,}</td>
                <td>{item['costType']}</td>
                <td>${item['unitCost']:.2f}</td>
                <td class="cost-info">${item_cost:,.2f}</td>
                <td>{item['startDate']} - {item['endDate']}</td>
            </tr>"""
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{order_data['name']} Work Order</title>
    <style>
        @media print {{
            body {{ margin: 0; }}
            .no-print {{ display: none; }}
        }}
        
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.4;
            margin: 20px;
            color: #333;
        }}
        
        .header {{
            text-align: center;
            border-bottom: 3px solid #2c5aa0;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        
        .company-name {{
            font-size: 28px;
            font-weight: bold;
            color: #2c5aa0;
            margin-bottom: 5px;
        }}
        
        .work-order-title {{
            font-size: 20px;
            color: #666;
            margin-bottom: 10px;
        }}
        
        .campaign-name {{
            font-size: 24px;
            color: #2c5aa0;
            font-weight: bold;
            margin: 10px 0;
        }}
        
        .order-info {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
        }}
        
        .order-details, .production-details {{
            flex: 1;
        }}
        
        .order-details h3, .production-details h3 {{
            margin: 0 0 10px 0;
            color: #2c5aa0;
            font-size: 16px;
        }}
        
        .detail-item {{
            margin-bottom: 5px;
        }}
        
        .label {{
            font-weight: bold;
            display: inline-block;
            width: 120px;
        }}
        
        .items-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }}
        
        .items-table th,
        .items-table td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        
        .items-table th {{
            background-color: #2c5aa0;
            color: white;
            font-weight: bold;
        }}
        
        .items-table tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        
        .cost-info {{
            text-align: right;
            font-weight: bold;
            color: #2c5aa0;
        }}
        
        .total-section {{
            border-top: 2px solid #2c5aa0;
            padding-top: 15px;
            text-align: right;
        }}
        
        .total-amount {{
            font-size: 18px;
            font-weight: bold;
            color: #2c5aa0;
        }}
        
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }}
        
        .signature-section {{
            display: flex;
            justify-content: space-between;
            margin-top: 30px;
        }}
        
        .signature-box {{
            width: 30%;
            border-bottom: 1px solid #333;
            padding-bottom: 5px;
            text-align: center;
        }}
        
        .print-btn {{
            background-color: #2c5aa0;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin-bottom: 20px;
        }}
        
        .print-btn:hover {{
            background-color: #1e4080;
        }}
        
        .status-badge {{
            background-color: #4caf50;
            color: white;
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 12px;
        }}
        
        .disney-highlight {{
            background: linear-gradient(135deg, #1e3a8a, #3b82f6);
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 20px;
            font-size: 16px;
        }}
    </style>
</head>
<body>
    <button class="print-btn no-print" onclick="window.print()">🖨️ Print Work Order</button>
    
    <div class="header">
        <div class="company-name">VINYL SIGNAGE WORK ORDER</div>
        <div class="work-order-title">DOOH Field Advertising Production Request</div>
        <div class="campaign-name">{order_data['name']}</div>
    </div>
    
    <div class="disney-highlight">
        <strong>🏰 Premium Client Campaign - {order_data['name']} 🏰</strong><br>
        Digital Out-of-Home (DOOH) Field Signage Production
    </div>
    
    <div class="order-info">
        <div class="order-details">
            <h3>Order Information</h3>
            <div class="detail-item"><span class="label">Order ID:</span> {order_data['sourceOrderId']}</div>
            <div class="detail-item"><span class="label">Campaign:</span> {order_data['name']}</div>
            <div class="detail-item"><span class="label">Start Date:</span> {order_data['startDate']}</div>
            <div class="detail-item"><span class="label">End Date:</span> {order_data['endDate']}</div>
            <div class="detail-item"><span class="label">Advertiser ID:</span> {order_data['advertiserId']}</div>
        </div>
        <div class="production-details">
            <h3>Production Timeline</h3>
            <div class="detail-item"><span class="label">Created:</span> {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
            <div class="detail-item"><span class="label">Status:</span> <span class="status-badge">PENDING</span></div>
            <div class="detail-item"><span class="label">Priority:</span> High</div>
            <div class="detail-item"><span class="label">Deadline:</span> {order_data['startDate']}</div>
        </div>
    </div>
    
    <div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
        <h3 style="color: #1565c0; margin-top: 0;">Sales Contact Information</h3>
        <div class="detail-item"><span class="label">Sales Person:</span> {order_data['salesPersonName']}</div>
        <div class="detail-item"><span class="label">Email:</span> {order_data['salesPersonEmailId']}</div>
        <div class="detail-item"><span class="label">Trafficker:</span> {order_data.get('traffickerName', 'To be assigned')}</div>
    </div>
    
    <table class="items-table">
        <thead>
            <tr>
                <th>Line Item Name</th>
                <th>Product</th>
                <th>Quantity</th>
                <th>Cost Type</th>
                <th>Unit Cost</th>
                <th>Total Cost</th>
                <th>Flight Dates</th>
            </tr>
        </thead>
        <tbody>
            {line_items_html}
        </tbody>
    </table>
    
    <div class="total-section">
        <div style="margin-bottom: 10px;">
            <strong>Total Impressions: {total_quantity:,}</strong>
        </div>
        <div style="margin-bottom: 10px;">
            <strong>Total Line Items: {len(order_data['lineitems'])}</strong>
        </div>
        <div class="total-amount">
            <strong>Campaign Total: ${total_cost:,.2f}</strong>
        </div>
    </div>
    
    <div style="margin-top: 30px; background-color: #fff3e0; padding: 15px; border-radius: 5px; border-left: 4px solid #ff9800;">
        <h3 style="color: #e65100; margin-top: 0;">🎯 DOOH Production Requirements:</h3>
        <ul style="margin: 10px 0;">
            <li>High-resolution graphics suitable for outdoor viewing</li>
            <li>Weather-resistant vinyl material</li>
            <li>UV-resistant inks for extended outdoor exposure</li>
            <li>Professional installation and mounting hardware</li>
            <li>Compliance with venue signage specifications</li>
        </ul>
    </div>
    
    <div style="margin-top: 20px; background-color: #f3e5f5; padding: 15px; border-radius: 5px;">
        <h4 style="color: #7b1fa2; margin-top: 0;">⚠️ Special Production Notes:</h4>
        <ul style="margin: 5px 0;">
            <li>Coordinate with venue management for installation timing</li>
            <li>Ensure all designs meet brand guidelines</li>
            <li>Schedule quality control inspection before installation</li>
            <li>Provide installation photography for campaign verification</li>
        </ul>
    </div>
    
    <div class="signature-section">
        <div class="signature-box">
            <div style="margin-top: 20px;">Production Manager</div>
        </div>
        <div class="signature-box">
            <div style="margin-top: 20px;">Sales Representative</div>
        </div>
        <div class="signature-box">
            <div style="margin-top: 20px;">Client Approval</div>
        </div>
    </div>
    
    <div class="footer">
        <p><strong>{order_data['name']} - Work Order Details:</strong></p>
        <ul style="margin: 5px 0; padding-left: 20px;">
            <li>Order generated on {datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S")}</li>
            <li>Campaign duration: {order_data['startDate']} to {order_data['endDate']}</li>
            <li>Total line items: {len(order_data['lineitems'])}</li>
            <li>Production priority: High</li>
        </ul>
        <p style="margin-top: 15px; font-style: italic;">
            This work order is automatically generated from the campaign management system. 
            Please verify all details before proceeding with production.
        </p>
    </div>
</body>
</html>"""
    
    return html_content

def save_work_order_to_gcs(html_content, order_name):
    """Save the generated HTML and PDF work order to Google Cloud Storage.
    
    Args:
        html_content (str): The generated HTML content
        order_name (str): Name of the order for the filename
        
    Returns:
        dict: Filenames of the saved work order (HTML and PDF)
    """
    # Get a reference to the GCS bucket
    bucket_name = "aos-demo-toolkit"
    folder_name = "responses"
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    # Generate timestamp for filename
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Create filename
    safe_order_name = "".join(c for c in order_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_order_name = safe_order_name.replace(' ', '_')
    html_filename = f"work_order_{safe_order_name}_{timestamp}.html"
    pdf_filename = f"work_order_{safe_order_name}_{timestamp}.pdf"
    
    # Construct the full path within the bucket
    html_blob = bucket.blob(f"{folder_name}/{html_filename}")
    pdf_blob = bucket.blob(f"{folder_name}/{pdf_filename}")
    
    # Upload the HTML content
    html_blob.upload_from_string(
        data=html_content,
        content_type='text/html'
    )
    
    # Generate PDF from HTML and upload
    pdf_bytes = HTML(string=html_content).write_pdf()
    pdf_blob.upload_from_string(
        data=pdf_bytes,
        content_type='application/pdf'
    )
    
    return {"html": html_filename, "pdf": pdf_filename}

def generate_work_order(order_data):
    """Main function to generate work order HTML and PDF, and save to GCS.
    
    Args:
        order_data (dict): Order data in the format of order_sample.json
        
    Returns:
        dict: Response with status and filenames
    """
    try:
        # Generate HTML content
        html_content = generate_work_order_html(order_data)
        
        # Save to GCS (HTML and PDF)
        filenames = save_work_order_to_gcs(html_content, order_data['name'])
        
        return {
            "status": "success",
            "message": "Work order generated successfully",
            "html_filename": filenames["html"],
            "pdf_filename": filenames["pdf"],
            "order_name": order_data['name'],
            "order_id": order_data['sourceOrderId']
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to generate work order: {str(e)}",
            "order_name": order_data.get('name', 'Unknown'),
            "order_id": order_data.get('sourceOrderId', 'Unknown')
        }

def main(request):
    """Main function called from orders.py or main.py.
    
    Args:
        request: Flask request object containing the order JSON data
        
    Returns:
        dict: Response with work order generation status
    """
    if request.is_json:
        order_data = request.get_json()
        return generate_work_order(order_data)
    else:
        return {
            "status": "error",
            "message": "Request must contain JSON data"
        }