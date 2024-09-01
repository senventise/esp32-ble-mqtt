"""The ESP32 BLE MQTT Gateway integration."""

from __future__ import annotations

import voluptuous as vol
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.components import bluetooth, mqtt
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from habluetooth import BaseHaScanner
from bluetooth_data_tools import parse_advertisement_data
from bluetooth_data_tools.gap import BLEGAPAdvertisement

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = []

# TODO Create ConfigEntry type alias with API object
# TODO Rename type alias and update all entry annotations
type New_NameConfigEntry = ConfigEntry[MyApi]  # noqa: F821

_LOGGER = logging.getLogger(__name__)

# The domain of your component. Should be equal to the name of your component.
DOMAIN = "esp32_ble_mqtt"

CONF_TOPIC = 'topic'
DEFAULT_TOPIC = 'hatest'

# Schema to validate the configured MQTT topic
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(
                    CONF_TOPIC, default=DEFAULT_TOPIC
                ): mqtt.valid_subscribe_topic
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


# TODO Update entry annotation
async def async_setup_entry(hass: HomeAssistant, entry: New_NameConfigEntry) -> bool:
    """Set up ESP32 BLE MQTT Gateway from a config entry."""

    # TODO 1. Create API instance
    # TODO 2. Validate the API connection (and authentication)
    # TODO 3. Store an API object for your platforms to access
    # entry.runtime_data = MyAPI(...)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


# TODO Update entry annotation
async def async_unload_entry(hass: HomeAssistant, entry: New_NameConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    from bleak.backends.scanner import AdvertisementData
    from bleak.backends.device import BLEDevice
    import time
    import json
    import base64
    
    print(config)
    
    topic = '/topic/adv' # config[DOMAIN][CONF_TOPIC]
    adv_callback = bluetooth.async_get_advertisement_callback(hass)
    
    @callback
    def message_received(msg: mqtt.models.ReceiveMessage) -> None:
        """A new MQTT message has been received."""
        adv_data = json.loads(msg.payload)
        addr = adv_data['a']
        payload: bytes = base64.b64decode(adv_data['p'])
        rssi = adv_data['r']
        adv_data: BLEGAPAdvertisement = parse_advertisement_data([payload])
        
        data = AdvertisementData(
            local_name = adv_data.local_name,
            manufacturer_data = adv_data.manufacturer_data,
            service_data = adv_data.service_data,
            service_uuids = adv_data.service_uuids,
            tx_power = adv_data.tx_power,
            rssi = rssi,
            platform_data = ()
        )
        _LOGGER.info(data)
        
        device = BLEDevice(
            address=addr,
            name = adv_data.local_name,
            details= None,
            rssi = rssi
        )
        info = BluetoothServiceInfoBleak.from_device_and_advertisement_data(device, data, 'mqtt', time.time(), False)
        adv_callback(info)
    
    await mqtt.async_subscribe(hass, topic, message_received)
        
    return True
