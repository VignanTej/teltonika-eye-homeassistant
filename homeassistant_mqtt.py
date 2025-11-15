#!/usr/bin/env python3
"""
Teltonika EYE Sensor to Home Assistant MQTT Bridge

Scans for Teltonika EYE sensors and publishes data to MQTT with Home Assistant
auto-discovery support. No logging - Home Assistant handles all logging.
"""

import asyncio
import json
import signal
import sys
import time
from typing import Dict, Optional, Set

import paho.mqtt.client as mqtt
from teltonika_eye_scanner import TeltonikaEYEScanner


class HomeAssistantMQTT:
    """Home Assistant MQTT bridge for Teltonika EYE sensors."""
    
    def __init__(
        self,
        mqtt_host: str = "localhost",
        mqtt_port: int = 1883,
        mqtt_username: Optional[str] = None,
        mqtt_password: Optional[str] = None,
        scan_duration: float = 5.0,
        scan_interval: float = 30.0,
        discovery_prefix: str = "homeassistant"
    ):
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.mqtt_username = mqtt_username
        self.mqtt_password = mqtt_password
        self.scan_duration = scan_duration
        self.scan_interval = scan_interval
        self.discovery_prefix = discovery_prefix
        
        self.running = True
        self.mqtt_client = None
        self.scanner = TeltonikaEYEScanner(scan_duration=scan_duration, output_format="json")
        self.discovered_sensors: Set[str] = set()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.running = False
        if self.mqtt_client:
            self.mqtt_client.disconnect()
    
    def _setup_mqtt(self):
        """Setup MQTT client connection."""
        self.mqtt_client = mqtt.Client()
        
        if self.mqtt_username and self.mqtt_password:
            self.mqtt_client.username_pw_set(self.mqtt_username, self.mqtt_password)
        
        # Connect to MQTT broker
        try:
            self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            return True
        except Exception as e:
            print(f"Failed to connect to MQTT broker: {e}", file=sys.stderr)
            return False
    
    def _get_device_id(self, device_address: str) -> str:
        """Generate a clean device ID for Home Assistant."""
        return device_address.replace(":", "").lower()
    
    def _get_device_name(self, device_data: Dict) -> str:
        """Get a friendly device name."""
        device_name = device_data.get("device", {}).get("name", "Unknown")
        device_address = device_data.get("device", {}).get("address", "")
        
        if device_name == "Unknown" or not device_name:
            return f"Teltonika EYE {device_address[-8:].replace(':', '')}"
        return device_name
    
    def _publish_discovery_config(self, device_data: Dict):
        """Publish Home Assistant auto-discovery configuration."""
        device_address = device_data["device"]["address"]
        device_id = self._get_device_id(device_address)
        device_name = self._get_device_name(device_data)
        sensors = device_data["data"]["sensors"]
        
        # Base device configuration
        device_config = {
            "identifiers": [f"teltonika_eye_{device_id}"],
            "name": device_name,
            "model": "EYE Sensor",
            "manufacturer": "Teltonika",
            "sw_version": str(device_data["data"]["protocol_version"]),
            "via_device": "teltonika_ble_scanner"
        }
        
        # Publish sensor configurations
        if "temperature" in sensors:
            temp_config = {
                "name": f"{device_name} Temperature",
                "unique_id": f"teltonika_eye_{device_id}_temperature",
                "state_topic": f"teltonika_eye/{device_id}/temperature",
                "unit_of_measurement": "°C",
                "device_class": "temperature",
                "state_class": "measurement",
                "device": device_config
            }
            self.mqtt_client.publish(
                f"{self.discovery_prefix}/sensor/teltonika_eye_{device_id}/temperature/config",
                json.dumps(temp_config),
                retain=True
            )
        
        if "humidity" in sensors:
            humidity_config = {
                "name": f"{device_name} Humidity",
                "unique_id": f"teltonika_eye_{device_id}_humidity",
                "state_topic": f"teltonika_eye/{device_id}/humidity",
                "unit_of_measurement": "%",
                "device_class": "humidity",
                "state_class": "measurement",
                "device": device_config
            }
            self.mqtt_client.publish(
                f"{self.discovery_prefix}/sensor/teltonika_eye_{device_id}/humidity/config",
                json.dumps(humidity_config),
                retain=True
            )
        
        if "battery_voltage" in sensors:
            battery_config = {
                "name": f"{device_name} Battery",
                "unique_id": f"teltonika_eye_{device_id}_battery",
                "state_topic": f"teltonika_eye/{device_id}/battery",
                "unit_of_measurement": "V",
                "device_class": "voltage",
                "state_class": "measurement",
                "device": device_config
            }
            self.mqtt_client.publish(
                f"{self.discovery_prefix}/sensor/teltonika_eye_{device_id}/battery/config",
                json.dumps(battery_config),
                retain=True
            )
        
        if "movement" in sensors:
            movement_config = {
                "name": f"{device_name} Movement Count",
                "unique_id": f"teltonika_eye_{device_id}_movement_count",
                "state_topic": f"teltonika_eye/{device_id}/movement_count",
                "state_class": "total_increasing",
                "icon": "mdi:motion-sensor",
                "device": device_config
            }
            self.mqtt_client.publish(
                f"{self.discovery_prefix}/sensor/teltonika_eye_{device_id}/movement_count/config",
                json.dumps(movement_config),
                retain=True
            )
            
            movement_state_config = {
                "name": f"{device_name} Movement State",
                "unique_id": f"teltonika_eye_{device_id}_movement_state",
                "state_topic": f"teltonika_eye/{device_id}/movement_state",
                "icon": "mdi:motion-sensor",
                "device": device_config
            }
            self.mqtt_client.publish(
                f"{self.discovery_prefix}/binary_sensor/teltonika_eye_{device_id}/movement_state/config",
                json.dumps(movement_state_config),
                retain=True
            )
        
        if "magnetic" in sensors:
            magnetic_config = {
                "name": f"{device_name} Magnetic Field",
                "unique_id": f"teltonika_eye_{device_id}_magnetic",
                "state_topic": f"teltonika_eye/{device_id}/magnetic",
                "payload_on": "true",
                "payload_off": "false",
                "device_class": "opening",
                "icon": "mdi:magnet",
                "device": device_config
            }
            self.mqtt_client.publish(
                f"{self.discovery_prefix}/binary_sensor/teltonika_eye_{device_id}/magnetic/config",
                json.dumps(magnetic_config),
                retain=True
            )
        
        if "angle" in sensors:
            pitch_config = {
                "name": f"{device_name} Pitch",
                "unique_id": f"teltonika_eye_{device_id}_pitch",
                "state_topic": f"teltonika_eye/{device_id}/pitch",
                "unit_of_measurement": "°",
                "icon": "mdi:angle-acute",
                "state_class": "measurement",
                "device": device_config
            }
            self.mqtt_client.publish(
                f"{self.discovery_prefix}/sensor/teltonika_eye_{device_id}/pitch/config",
                json.dumps(pitch_config),
                retain=True
            )
            
            roll_config = {
                "name": f"{device_name} Roll",
                "unique_id": f"teltonika_eye_{device_id}_roll",
                "state_topic": f"teltonika_eye/{device_id}/roll",
                "unit_of_measurement": "°",
                "icon": "mdi:angle-acute",
                "state_class": "measurement",
                "device": device_config
            }
            self.mqtt_client.publish(
                f"{self.discovery_prefix}/sensor/teltonika_eye_{device_id}/roll/config",
                json.dumps(roll_config),
                retain=True
            )
        
        # RSSI sensor
        rssi_config = {
            "name": f"{device_name} Signal Strength",
            "unique_id": f"teltonika_eye_{device_id}_rssi",
            "state_topic": f"teltonika_eye/{device_id}/rssi",
            "unit_of_measurement": "dBm",
            "device_class": "signal_strength",
            "state_class": "measurement",
            "entity_category": "diagnostic",
            "device": device_config
        }
        self.mqtt_client.publish(
            f"{self.discovery_prefix}/sensor/teltonika_eye_{device_id}/rssi/config",
            json.dumps(rssi_config),
            retain=True
        )
        
        # Battery status (low battery indicator)
        battery_status_config = {
            "name": f"{device_name} Low Battery",
            "unique_id": f"teltonika_eye_{device_id}_low_battery",
            "state_topic": f"teltonika_eye/{device_id}/low_battery",
            "payload_on": "true",
            "payload_off": "false",
            "device_class": "battery",
            "entity_category": "diagnostic",
            "device": device_config
        }
        self.mqtt_client.publish(
            f"{self.discovery_prefix}/binary_sensor/teltonika_eye_{device_id}/low_battery/config",
            json.dumps(battery_status_config),
            retain=True
        )
    
    def _publish_sensor_data(self, device_data: Dict):
        """Publish sensor data to MQTT topics."""
        device_address = device_data["device"]["address"]
        device_id = self._get_device_id(device_address)
        sensors = device_data["data"]["sensors"]
        
        # Publish individual sensor values
        if "temperature" in sensors:
            self.mqtt_client.publish(
                f"teltonika_eye/{device_id}/temperature",
                sensors["temperature"]["value"]
            )
        
        if "humidity" in sensors:
            self.mqtt_client.publish(
                f"teltonika_eye/{device_id}/humidity",
                sensors["humidity"]["value"]
            )
        
        if "battery_voltage" in sensors:
            self.mqtt_client.publish(
                f"teltonika_eye/{device_id}/battery",
                sensors["battery_voltage"]["value"]
            )
        
        if "movement" in sensors:
            self.mqtt_client.publish(
                f"teltonika_eye/{device_id}/movement_count",
                sensors["movement"]["count"]
            )
            self.mqtt_client.publish(
                f"teltonika_eye/{device_id}/movement_state",
                "ON" if sensors["movement"]["state"] == "moving" else "OFF"
            )
        
        if "magnetic" in sensors:
            self.mqtt_client.publish(
                f"teltonika_eye/{device_id}/magnetic",
                "true" if sensors["magnetic"]["detected"] else "false"
            )
        
        if "angle" in sensors:
            self.mqtt_client.publish(
                f"teltonika_eye/{device_id}/pitch",
                sensors["angle"]["pitch"]
            )
            self.mqtt_client.publish(
                f"teltonika_eye/{device_id}/roll",
                sensors["angle"]["roll"]
            )
        
        # Always publish RSSI and battery status
        self.mqtt_client.publish(
            f"teltonika_eye/{device_id}/rssi",
            device_data["device"]["rssi"]
        )
        
        self.mqtt_client.publish(
            f"teltonika_eye/{device_id}/low_battery",
            "true" if device_data["data"]["battery"]["low"] else "false"
        )
        
        # Publish complete device state as JSON for advanced users
        self.mqtt_client.publish(
            f"teltonika_eye/{device_id}/state",
            json.dumps(device_data)
        )
    
    async def _scan_cycle(self):
        """Perform a single scan cycle."""
        try:
            devices = await self.scanner.scan()
            
            for device_data in devices:
                device_address = device_data["device"]["address"]
                
                # Setup auto-discovery for new sensors
                if device_address not in self.discovered_sensors:
                    self._publish_discovery_config(device_data)
                    self.discovered_sensors.add(device_address)
                
                # Publish sensor data
                self._publish_sensor_data(device_data)
                
        except Exception as e:
            print(f"Error during scan: {e}", file=sys.stderr)
    
    async def run(self):
        """Run the MQTT bridge."""
        if not self._setup_mqtt():
            return
        
        while self.running:
            cycle_start = time.time()
            
            await self._scan_cycle()
            
            # Calculate sleep time
            cycle_duration = time.time() - cycle_start
            sleep_time = max(0, self.scan_interval - cycle_duration)
            
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        # Cleanup
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Teltonika EYE Sensor to Home Assistant MQTT Bridge"
    )
    parser.add_argument(
        "--mqtt-host",
        default="localhost",
        help="MQTT broker hostname (default: localhost)"
    )
    parser.add_argument(
        "--mqtt-port",
        type=int,
        default=1883,
        help="MQTT broker port (default: 1883)"
    )
    parser.add_argument(
        "--mqtt-username",
        help="MQTT username (optional)"
    )
    parser.add_argument(
        "--mqtt-password",
        help="MQTT password (optional)"
    )
    parser.add_argument(
        "--scan-duration",
        type=float,
        default=5.0,
        help="BLE scan duration in seconds (default: 5.0)"
    )
    parser.add_argument(
        "--scan-interval",
        type=float,
        default=30.0,
        help="Interval between scans in seconds (default: 30.0)"
    )
    parser.add_argument(
        "--discovery-prefix",
        default="homeassistant",
        help="Home Assistant discovery prefix (default: homeassistant)"
    )
    
    args = parser.parse_args()
    
    # Create and run bridge
    bridge = HomeAssistantMQTT(
        mqtt_host=args.mqtt_host,
        mqtt_port=args.mqtt_port,
        mqtt_username=args.mqtt_username,
        mqtt_password=args.mqtt_password,
        scan_duration=args.scan_duration,
        scan_interval=args.scan_interval,
        discovery_prefix=args.discovery_prefix
    )
    
    try:
        await bridge.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())