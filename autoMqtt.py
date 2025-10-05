# modbus_to_mqtt_autodiscovery.py

from pymodbus.client import ModbusSerialClient
import paho.mqtt.client as mqtt
import time
import struct
import json

# ------------------------
# Configuration
# ------------------------

MODBUS_PORT = '/dev/ttyUSB0'
MODBUS_BAUDRATE = 9600
MODBUS_SLAVE_ID = 1

MQTT_BROKER = '192.168.1.100'
MQTT_BASE_TOPIC = 'modbus/dxe007r'
MQTT_DISCOVERY_PREFIX = 'homeassistant'

DEVICE_INFO = {
    "identifiers": ["dxe007r_modbus"],
    "name": "DXE007R VFD",
    "manufacturer": "Phase Technologies",
    "model": "DXE007R",
}

# Register definitions
REGISTERS = [
    {"name": "measured_psi",  "address": 33, "unit": "psi", "device_class": "pressure"},
    {"name": "measured_gpm",  "address": 34, "unit": "gpm"},
    {"name": "measured_ft",   "address": 35, "unit": "ft"},
    {"name": "target_hz",     "address": 36, "unit": "Hz", "device_class": "frequency"},
    {"name": "target_psi",    "address": 37, "unit": "psi"},
    {"name": "target_gpm",    "address": 38, "unit": "gpm"},
]

# ------------------------
# Helpers
# ------------------------

def read_float32(client, address):
    result = client.read_input_registers(address=address, count=2, slave=MODBUS_SLAVE_ID)
    if result.isError():
        print(f"Error reading address {address}")
        return None
    regs = result.registers
    packed = struct.pack('>HH', regs[0], regs[1])  # Adjust byte order if needed
    return struct.unpack('>f', packed)[0]

def publish_discovery(mqtt_client, reg):
    sensor_id = f"dxe007r_{reg['name']}"
    discovery_topic = f"{MQTT_DISCOVERY_PREFIX}/sensor/{sensor_id}/config"
    state_topic = f"{MQTT_BASE_TOPIC}/{reg['name']}"
    
    payload = {
        "name": reg['name'].replace('_', ' ').title(),
        "unique_id": sensor_id,
        "state_topic": state_topic,
        "unit_of_measurement": reg.get("unit"),
        "device_class": reg.get("device_class"),
        "device": DEVICE_INFO,
    }
    
    mqtt_client.publish(discovery_topic, json.dumps(payload), retain=True)
    print(f"Published discovery for {reg['name']}")

# ------------------------
# Main
# ------------------------

modbus_client = ModbusSerialClient(
    method='rtu',
    port=MODBUS_PORT,
    baudrate=MODBUS_BAUDRATE,
    stopbits=1,
    bytesize=8,
    parity='N',
    timeout=1
)

mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, 1883, 60)

# Publish discovery configs once
for reg in REGISTERS:
    publish_discovery(mqtt_client, reg)

print("Starting Modbus to MQTT loop...")

while True:
    if modbus_client.connect():
        for reg in REGISTERS:
            value = read_float32(modbus_client, reg["address"])
            if value is not None:
                topic = f"{MQTT_BASE_TOPIC}/{reg['name']}"
                mqtt_client.publish(topic, round(value, 2))
                print(f"{reg['name']}: {value:.2f}")
        modbus_client.close()
    else:
        print("Modbus connection failed")

    time.sleep(10)
