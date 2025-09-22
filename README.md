# AOS Demo Toolkit

This toolkit provides various functions to convert requests from AOS or Operative.One into responses, including inventory forecasting, order management, and work order generation.

## Functions

### Inventory
Inventory function to convert an inventory request from AOS or Operative.One into a forecast response based on a dataset built in BigQuery.

### Orders
Order management function that processes order data and stores it in BigQuery, including:
- Order creation and updates
- Line item management
- Automatic delivery data generation
- **Work order HTML generation**

### Work Orders
Automatically generates professional HTML work orders when orders are processed. Features include:
- Dynamic HTML generation from order JSON data
- Professional styling with print support
- Automatic saving to Google Cloud Storage
- Unique timestamped filenames
- Integration with the orders processing workflow

#### Work Order Flow
1. When an order is processed through `orders.py`, the system automatically generates a work order
2. The work order HTML is created using the same JSON data format as `order_sample.json`
3. The HTML file is saved to the `aos-demo-toolkit` bucket in the `responses` folder
4. Filename format: `work_order_{order_name}_{timestamp}.html`

#### Manual Work Order Generation
You can also generate work orders directly by calling the `/work_order` endpoint with order JSON data.

### Advertisers
Function to manage advertiser data.

### Credentials
Function to manage API credentials and authentication.

## Testing

Run `test_work_order.py` to test work order generation functionality with sample data. 