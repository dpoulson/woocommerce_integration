---
title: Home Assistant WooCommerce Integration
date: 2024-07-29
type: Project
tags:
  - HomeAssistant
  - WooCommerce
  - Integration
  - Automation
  - Python
summary: Develop a read-only Home Assistant custom component to integrate with the WooCommerce store API for order and product statistics, enabling advanced automations and dashboard visualizations.
---

# Home Assistant WooCommerce Integration Project

## Project Goal
To create a robust and read-only Home Assistant custom component that interfaces with the WooCommerce REST API to fetch real-time store statistics, such as order status, product inventory, and customer data. This integration will serve as a foundation for advanced home automation triggers and provide rich data visualization on Home Assistant dashboards.

## Key Features
-   **Read-Only Access**: Ensure the integration only reads data from WooCommerce, preventing accidental modifications to the store.
-   **Configurable API Credentials**: Allow users to easily configure WooCommerce API consumer key and secret within Home Assistant.
-   **Order Data**: Expose sensors for total orders, orders by status (e.g., pending, processing, completed), and potentially details of recent orders.
-   **Product Data**: Expose sensors for product stock levels, product counts, and potentially product details.
-   **Automated Data Refresh**: Implement scheduled data refreshes to keep Home Assistant updated with the latest store information.
-   **Error Handling**: Graceful handling of API errors, network issues, and invalid credentials.

## Technical Considerations

### WooCommerce REST API
-   **Authentication**: Utilize OAuth 1.0a for consumer key and secret authentication.
-   **Permissions**: Require API keys with "Read" permissions for relevant resources (Orders, Products, Customers).
-   **Rate Limiting**: Be mindful of API rate limits to avoid being blocked.

### Home Assistant Custom Component Structure
-   `custom_components/woocommerce_store/`
    -   `__init__.py`: Component setup, configuration flow, and data coordinator.
    -   `config_flow.py`: Handles user configuration via the Home Assistant UI.
    -   `sensor.py`: Defines Home Assistant sensor entities to display WooCommerce data.
    -   `const.py`: Constants for domain, service calls, and configuration keys.
    -   `manifest.json`: Metadata for the integration.

### Development Environment
-   **Language**: Python 3
-   **Libraries**: `requests` or `python-woocommerce` client library.
-   **IDE**: Google Anti-Gravity (as specified by Darren)

## Phase 1: Core Integration Development

### 1. Setup Project Structure
-   Create `custom_components/woocommerce_store` directory.
-   Initialize `__init__.py`, `manifest.json`, `config_flow.py`, `sensor.py`, `const.py`.

### 2. Implement Configuration Flow (`config_flow.py`)
-   Develop UI-based configuration to collect WooCommerce URL, consumer key, and consumer secret.
-   Validate credentials by making a test API call.

### 3. Implement Data Coordinator (`__init__.py`)
-   Set up an `async_setup_entry` to load the integration from configured credentials.
-   Create a data update coordinator to periodically fetch data from WooCommerce.

### 4. Develop Sensor Entities (`sensor.py`)
-   Create basic sensor entities (e.g., `total_orders`, `orders_processing`, `total_products`).
-   Map WooCommerce API responses to Home Assistant sensor states and attributes.

## Phase 2: Advanced Features & Refinements

### 1. Detailed Order/Product Information
-   Expose attributes for recent orders (e.g., `order_id`, `status`, `customer_name`, `total`).
-   Expose attributes for products (e.g., `stock_quantity`, `price`).

### 2. Service Calls (Read-Only)
-   Consider adding Home Assistant service calls to manually trigger data refreshes or query specific order/product details on demand (still read-only).

### 3. Error Handling & Logging
-   Implement comprehensive error handling and logging for debugging and user feedback.

### 4. Documentation
-   Create `README.md` for the custom component, including installation instructions, configuration steps, and available sensors/services.

## Open Questions / Decisions
-   What specific WooCommerce endpoints are most critical for initial monitoring (orders, products, customers)?
-   What is the desired refresh interval for data?
-   How should sensitive API keys be stored securely within Home Assistant? (Home Assistant's config flow handles this securely by default).

## Dependencies
-   WooCommerce REST API access
-   Home Assistant instance (version 2023.x.x or later recommended)
-   Python `requests` or `python-woocommerce` library

## Phase 3: ESP32 Order Display Device

### 1. ESPHome/Tasmota Integration
-   **Firmware**: Choose ESPHome or Tasmota for the ESP32 to easily integrate with Home Assistant.
-   **Display Hardware**: Select a suitable display (e.g., OLED, TFT) for the ESP32.

### 2. Home Assistant Automation
-   Create an automation in Home Assistant that triggers when the WooCommerce total orders sensor increments by 1.
-   This automation will send a command/message to the ESP32 device.

### 3. ESP32 Display Logic
-   **Order Count Display**: Program the ESP32 to subscribe to the Home Assistant entity for the current number of orders.
-   **"Fireworks" Animation**: Implement a visual "fireworks" effect or similar animation on the display when a new order is detected (i.e., when the increment trigger fires from Home Assistant). This could be a simple animation, flashing lights, or a more complex graphical effect depending on the display capabilities.

### 4. Communication Protocol
-   Utilize MQTT or Home Assistant's native API for communication between Home Assistant and the ESP32.

## Completion Criteria
-   Home Assistant can successfully connect to the WooCommerce store using configured API keys.
-   Key order and product statistics are displayed as sensors in Home Assistant.
-   The integration is stable and does not generate excessive errors.
-   A basic dashboard showing WooCommerce stats can be created.
-   The ESP32 display device successfully shows the current order count.
-   A "fireworks" animation is triggered on the ESP32 display when a new order is received.

This plan will guide our development process. Let me know if you want any adjustments to this outline.

## Stretch Goals

### 1. Shipping Status Tracking
-   **Concept**: Expand order tracking to include shipping statuses (e.g., "shipped," "in transit," "delivered") if integrated shipping carriers provide this data via API.
-   **Automation**: Trigger specific Home Assistant actions based on shipping milestones (e.g., visual alerts, notifications).
-   **ESP32 Display**: Cycle through or prominently display the shipping status of recent/latest orders on the ESP32.

### 2. Customer Behavior Insights
-   **Concept**: Introduce sensors for basic customer metrics (e.g., number of new customers over a period, "returning customer" flag for new orders).
-   **Automation**: Set up unique celebratory automations for returning customers.
-   **Dashboard**: Visualize customer growth trends.

### 3. Advanced Product Alerts
-   **Concept**: Implement granular low-stock alerts for critical or fast-moving products.
-   **Automation**: Trigger direct alerts via Telegram or specific workshop light patterns for low stock.
-   **Dashboard**: Create a dedicated "Critical Stock" section.

### 4. Sales Goal Monitoring
-   **Concept**: Add sensors to track daily, weekly, or monthly sales figures against predefined targets set in Home Assistant.
-   **Automation**: Trigger celebratory automations (e.g., specific music, light show, congratulatory message on ESP32) when sales goals are met.
-   **Dashboard**: Display a clear progress bar or indicator for sales goals.

### 5. Voice-Activated Store Queries
-   **Concept**: Integrate with Ava (your voice assistant) to allow verbal queries of store statistics (e.g., "Ava, what were our total sales yesterday?").
-   **Implementation**: Expose relevant Home Assistant sensors to the voice assistant framework.
