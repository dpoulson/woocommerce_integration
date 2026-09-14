<p align="center">
  <img src="logo.png" alt="WooCommerce Store for Home Assistant" width="160">
</p>

# Home Assistant WooCommerce Store Integration

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=dpoulson&repository=woocommerce_integration&category=integration)

A modern, read-only Home Assistant custom component that interfaces with the WooCommerce REST API (v3) to monitor store performance, order flow, inventory levels, and sales in real-time.

---

## Features

- **Read-Only API Access**: Uses consumer keys with Read permissions only; cannot modify orders or products.
- **Asynchronous & Non-Blocking**: Built on `aiohttp` and Home Assistant's `DataUpdateCoordinator` for fast, lightweight background polling.
- **UI Configuration Flow**: Setup directly via Home Assistant UI (Settings &rarr; Devices & Services &rarr; Add Integration) with credential validation.
- **Configurable Polling Interval**: Adjust polling rate (default: 300 seconds / 5 minutes) dynamically via Integration Options.
- **Rich Sensor Suite**:
  - **Orders**: Total orders, processing, pending payment, completed, on-hold, cancelled, refunded, failed.
  - **Inventory**: Total products, in stock, low stock, out of stock.
  - **Latest Order**: Detailed sensor exposing order ID, total, currency, customer name, date, item count, and full line item lists as attributes.
  - **Sales Today**: Daily revenue tracker with order, tax, and shipping breakdowns.
- **Manual Refresh Service**: `woocommerce_store.refresh` service to force an immediate update on demand.

---

## Installation

### Method 1: Via HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=dpoulson&repository=woocommerce_integration&category=integration)

1. Click the button above to add this repository directly to HACS.
2. Click **Download**, then restart Home Assistant.

*Manual HACS steps if needed:*
1. Open **HACS** &rarr; **Integrations** &rarr; **Custom repositories** (three dots menu).
2. Add `https://github.com/dpoulson/woocommerce_integration` as category **Integration**.
3. Search for **WooCommerce Store** &rarr; **Download** &rarr; Restart Home Assistant.

### Method 2: Manual Installation
1. Copy the `custom_components/woocommerce_store` directory into your Home Assistant `<config>/custom_components/` directory.
2. The folder structure should look like:
   ```text
   config/
   └── custom_components/
       └── woocommerce_store/
           ├── __init__.py
           ├── api.py
           ├── config_flow.py
           ├── const.py
           ├── coordinator.py
           ├── manifest.json
           ├── sensor.py
           ├── services.yaml
           ├── strings.json
           └── translations/
               └── en.json
   ```
3. Restart Home Assistant.

---

## Configuration

### 1. Generate WooCommerce API Keys
1. In WordPress Admin, navigate to **WooCommerce &rarr; Settings &rarr; Advanced &rarr; REST API**.
2. Click **Add key**.
3. Description: `Home Assistant`.
4. Permissions: `Read`.
5. Click **Generate API key** and copy the **Consumer Key** (`ck_...`) and **Consumer Secret** (`cs_...`).

### 2. Add to Home Assistant
1. In Home Assistant, navigate to **Settings &rarr; Devices & Services**.
2. Click **Add Integration** and search for **WooCommerce Store**.
3. Enter:
   - **Store URL**: `https://your-store.com`
   - **Consumer Key**: `ck_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - **Consumer Secret**: `cs_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - **Verify SSL Certificate**: Checked (default)
4. Submit. The integration will validate credentials with your store and register entities.

---

## Sensors Reference

| Sensor | Entity ID | State Class | Description |
|---|---|---|---|
| Total Orders | `sensor.<store>_total_orders` | Total | Total count across all order statuses |
| Orders Processing | `sensor.<store>_orders_processing` | Measurement | Orders awaiting fulfilment |
| Orders Pending | `sensor.<store>_orders_pending` | Measurement | Orders awaiting payment |
| Orders Completed | `sensor.<store>_orders_completed` | Total | Fulfilled orders |
| Orders On Hold | `sensor.<store>_orders_on_hold` | Measurement | Orders on hold |
| Orders Cancelled | `sensor.<store>_orders_cancelled` | Total | Cancelled orders |
| Orders Refunded | `sensor.<store>_orders_refunded` | Total | Refunded orders |
| Orders Failed | `sensor.<store>_orders_failed` | Total | Failed orders |
| Total Products | `sensor.<store>_total_products` | Measurement | Catalog product count |
| Products In Stock | `sensor.<store>_products_in_stock` | Measurement | In-stock product count |
| Products Low Stock | `sensor.<store>_products_low_stock` | Measurement | Low stock items requiring attention |
| Products Out of Stock | `sensor.<store>_products_out_of_stock` | Measurement | Out-of-stock items |
| Latest Order | `sensor.<store>_latest_order` | String (`#1001`) | Most recent order with item attributes |
| Sales Today | `sensor.<store>_sales_today` | Total | Today's gross sales revenue |

---

## Services

### `woocommerce_store.refresh`
Trigger an immediate data fetch from the WooCommerce REST API.
```yaml
service: woocommerce_store.refresh
```

### `woocommerce_store.get_order`
Fetch real-time details for a specific order on demand (supports response data).
```yaml
service: woocommerce_store.get_order
data:
  order_id: 1024
response_variable: order_details
```

### `woocommerce_store.get_product`
Fetch real-time stock and pricing for a specific product on demand.
```yaml
service: woocommerce_store.get_product
data:
  product_id: 45
response_variable: product_details
```

---

## Example Automation: New Order Notification

Trigger an alert or ESP32 display animation whenever a new order is received:

```yaml
alias: "WooCommerce - New Order Alert"
trigger:
  - platform: state
    entity_id: sensor.mystore_total_orders
condition:
  - condition: template
    value_template: "{{ trigger.to_state.state | int > trigger.from_state.state | int }}"
action:
  - service: notify.persistent_notification
    data:
      title: "🎉 New WooCommerce Order!"
      message: >
        Order {{ states('sensor.mystore_latest_order') }} received.
        Customer: {{ state_attr('sensor.mystore_latest_order', 'customer_name') }}
        Total: {{ state_attr('sensor.mystore_latest_order', 'total') }} {{ state_attr('sensor.mystore_latest_order', 'currency') }}
```
