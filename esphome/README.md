# ESPHome WooCommerce Order Display

A companion round desktop display for your WooCommerce store built with ESPHome and Home Assistant.

<p align="center">
  <img src="https://ae-pic-a1.aliexpress-media.com/kf/Scf21ca3c86524144bc59143335c689beM.jpg" alt="Waveshare ESP32-S3-Touch-LCD-1.28" width="300">
</p>

## Supported Hardware
- **Board**: **Waveshare / Spotpear ESP32-S3-Touch-LCD-1.28** (ESP32-S3 with 2MB PSRAM)
- **Panel**: 1.28" Round IPS LCD (240x240, GC9A01 driver)
- **Touch**: Capacitive Touch Controller (CST816 via I2C)

### Pinout Mapping
| Component | Function | GPIO Pin | Notes |
|---|---|---|---|
| **LCD** | SCLK (Clock) | `GPIO10` | Hardware SPI (`SPI2_HOST`) |
| **LCD** | MOSI (Data) | `GPIO11` | Hardware SPI |
| **LCD** | CS (Chip Select) | `GPIO9` | Active Low |
| **LCD** | DC (Data/Command) | `GPIO8` | Data / Command Selection |
| **LCD** | RST (Reset) | `GPIO14` | Hardware Reset |
| **Backlight** | BL (PWM) | `GPIO2` | Monochromatic light component |
| **Touch** | SDA | `GPIO6` | I2C Data (shared with IMU) |
| **Touch** | SCL | `GPIO7` | I2C Clock (shared with IMU) |
| **Touch** | INT | `GPIO5` | Touch Interrupt |
| **Touch** | RST | `GPIO13` | Touch Reset |

---

## Display Features & UI Layout

1. **Processing-Centric Dashboard**:
   - Displays a prominent, high-visibility 2-digit number (84pt font) in the center showing active orders waiting for fulfillment.
   - Text header label `PROCESSING` in sleek muted typography.
2. **Top Notification Status Dot**:
   - 🟢 **Green**: Connected to both local Wi-Fi and the Home Assistant API.
   - 🟡 **Amber**: Connected to local Wi-Fi, waiting for Home Assistant API connection.
   - 🔴 **Red**: Disconnected from Wi-Fi.
3. **Bottom Alert Warning**:
   - Hidden during normal operation.
   - Automatically renders a red alert badge with the failed order count if any orders have failed (`orders_failed > 0`).
4. **Touch to Refresh**:
   - Tap anywhere on the capacitive touchscreen to immediately trigger `homeassistant.update_entity` on Home Assistant for real-time order synchronization.
   - Pulses a gold outer ring as tactile visual confirmation.
5. **Celebratory Fireworks Animation**:
   - Triggers a full-screen colorful starburst animation whenever a new order is received, or on demand via the Home Assistant service `esphome.woocommerce_display_trigger_fireworks`.

---

## Getting Started

### 1. Configure Secrets
Copy `secrets.yaml.example` to `secrets.yaml`:
```bash
cp esphome/secrets.yaml.example esphome/secrets.yaml
```
Open `esphome/secrets.yaml` and set your local Wi-Fi credentials:
```yaml
wifi_ssid: "Your_WiFi_SSID"
wifi_password: "Your_WiFi_Password"
ap_fallback_password: "Your_AP_Fallback_Password"
```

### 2. Configure Sensor Entity Substitutions
Open `esphome/woocommerce_display.yaml` and adjust the substitution lines at the top to match your WooCommerce Store entity IDs in Home Assistant:
```yaml
substitutions:
  device_name: "woocommerce-display"
  friendly_name: "WooCommerce Order Display"
  ha_orders_processing_sensor: "sensor.<your_store>_orders_processing"
  ha_orders_failed_sensor: "sensor.<your_store>_orders_failed"
  ha_order_count_sensor: "sensor.<your_store>_total_orders"
```

### 3. Flash the Device

#### Initial Flash (via USB):
Connect the board via USB (detected as `/dev/ttyACM0` or `COMx` on Windows):
```bash
esphome run esphome/woocommerce_display.yaml --device /dev/ttyACM0
```

#### Wireless Updates (OTA):
Once connected to your Wi-Fi network, flash future updates wirelessly:
```bash
esphome run esphome/woocommerce_display.yaml --device <device_ip_or_hostname>
```

### 4. Add to Home Assistant
Home Assistant will automatically discover the display under **Settings &rarr; Devices & Services**. Click **Configure** to finalize the integration.

### 5. Enable Touchscreen Refresh Permission
To allow the touchscreen tap to refresh Home Assistant entities:
1. In Home Assistant, go to **Settings &rarr; Devices & Services &rarr; ESPHome**.
2. Click **Configure** on the **WooCommerce Order Display** entry.
3. Check **Allow the device to perform Home Assistant actions**.
4. Click **Submit**.

