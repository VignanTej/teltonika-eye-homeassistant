# Changelog

All notable changes to the Teltonika EYE Sensors Home Assistant integration will be documented in this file.

## [1.1.0] - 2024-11-15

### 🎉 Major Improvements

#### ✅ Bluetooth Proxy Support
- **BREAKING**: Replaced direct `bleak` scanning with Home Assistant Bluetooth integration
- **NEW**: Full compatibility with ESP32 Bluetooth proxies
- **NEW**: Extended range through distributed Bluetooth proxy network
- **NEW**: Better reliability and performance via Home Assistant's Bluetooth stack

#### ✅ Enhanced Device Discovery Flow
- **NEW**: Device discovery notifications when new sensors are found
- **NEW**: User control over device onboarding (approve/ignore devices)
- **NEW**: Device selection during initial setup
- **NEW**: Device management in integration options
- **NEW**: Persistent storage of user device preferences

#### ✅ Bug Fixes
- **FIXED**: Magnetic sensor open/closed logic was reversed
- **FIXED**: Now correctly reports "closed" when magnetic field detected, "open" when not detected

### 🔧 Technical Changes

#### Dependencies
- **REMOVED**: Direct `bleak` dependency (now uses HA Bluetooth integration)
- **ADDED**: `bluetooth` dependency for Home Assistant Bluetooth integration
- **CHANGED**: IoT class from `local_polling` to `local_push` (real-time updates)

#### Architecture
- **NEW**: Real-time advertisement tracking via HA Bluetooth callbacks
- **NEW**: Automatic discovery of existing Bluetooth devices
- **NEW**: Notification system for new device discoveries
- **NEW**: Device approval/ignore workflow

### 🏠 Home Assistant Integration Improvements

#### User Experience
- **NEW**: Device selection during setup with live sensor readings
- **NEW**: Notifications when new sensors are discovered
- **NEW**: Options flow for managing devices after setup
- **NEW**: Descriptive device labels with current sensor values

#### Compatibility
- **NEW**: Works with all Home Assistant Bluetooth proxy setups
- **NEW**: Compatible with ESP32 Bluetooth proxies
- **NEW**: Supports Home Assistant OS, Supervised, Container, and Core
- **NEW**: Automatic detection of existing discovered devices

### 📱 User Interface

#### Setup Flow
1. **Initial Setup**: Configure integration settings
2. **Device Discovery**: Automatic discovery of available sensors
3. **Device Selection**: Choose which sensors to monitor
4. **Confirmation**: Integration ready with selected devices

#### Device Management
- **Options Flow**: Manage devices after initial setup
- **Approve New**: Add newly discovered devices
- **Ignore Devices**: Permanently ignore unwanted devices
- **Live Data**: See current sensor readings during selection

### 🔄 Migration from v1.0.0

#### Automatic Migration
- Existing installations will automatically migrate to v1.1.0
- All previously monitored devices will continue working
- New discovery features will be available immediately

#### Manual Steps (Optional)
- Go to **Settings** → **Devices & Services** → **Teltonika EYE Sensors** → **Configure**
- Use "Manage Devices" to review and organize your sensors

### 🚀 Performance Improvements

#### Bluetooth Proxy Benefits
- **Extended Range**: Sensors can be anywhere in your Bluetooth proxy network
- **Better Reliability**: Multiple proxies provide redundant coverage
- **Reduced Load**: Distributed scanning across proxy devices
- **Real-time Updates**: Immediate sensor data updates via callbacks

#### Resource Usage
- **Lower CPU**: No active scanning loops
- **Lower Memory**: Event-driven architecture
- **Better Battery**: Reduced Bluetooth adapter usage on HA host

### 🐛 Bug Fixes

#### Magnetic Sensor Logic
- **Issue**: Magnetic sensor reported "open" when magnetic field was detected
- **Fix**: Corrected logic - now reports "closed" when magnetic field detected
- **Impact**: Door/window sensors now work correctly

#### Device Management
- **Issue**: All discovered devices were automatically added
- **Fix**: User now controls which devices to monitor
- **Impact**: Better control over Home Assistant entity management

### 📚 Documentation Updates

#### New Guides
- **Bluetooth Proxy Setup**: How to configure ESP32 proxies
- **Device Management**: How to approve/ignore devices
- **Migration Guide**: Upgrading from v1.0.0
- **Troubleshooting**: Common issues and solutions

#### Updated Documentation
- **README**: Updated with Bluetooth proxy information
- **Installation**: New setup flow documentation
- **Configuration**: Device selection and management

---

## [1.0.0] - 2024-11-15

### 🎉 Initial Release

#### Core Features
- **Temperature Monitoring**: Real-time temperature readings in °C
- **Humidity Monitoring**: Relative humidity percentage
- **Movement Detection**: Motion detection and event counting
- **Magnetic Field Detection**: Magnetic field presence detection
- **Battery Monitoring**: Voltage monitoring and low battery alerts
- **Orientation Sensors**: Pitch and roll angle measurements
- **Signal Strength**: Bluetooth RSSI monitoring

#### Home Assistant Integration
- **Native Integration**: Full Home Assistant custom component
- **Auto-Discovery**: Automatic sensor discovery via Bluetooth LE
- **Device Classes**: Proper Home Assistant device classes for all sensors
- **Configuration Flow**: UI-based setup, no YAML required
- **Entity Management**: Proper device information and entity organization

#### Technical Implementation
- **Protocol Support**: Complete Teltonika EYE sensor BLE protocol
- **Data Parsing**: Flag-based sensor data extraction
- **Error Handling**: Robust error handling and recovery
- **Performance**: Efficient scanning and data processing

#### HACS Support
- **HACS Compatible**: Ready for Home Assistant Community Store
- **Auto-Updates**: Automatic update notifications via HACS
- **Easy Installation**: One-click installation through HACS UI

#### Developer
- **Created by**: Vignan Tej, Tez Solutions
- **License**: MIT License
- **Repository**: https://github.com/VignanTej/teltonika-eye-homeassistant