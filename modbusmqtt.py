from pymodbus.client import ModbusSerialClient
import paho.mqtt.client as mqtt
import time
import struct

# ------------------------
# Configuration
# ------------------------

MODBUS_PORT = '/dev/ttyUSB0'
MODBUS_BAUDRATE = 9600
MODBUS_SLAVE_ID = 1

MQTT_BROKER = '192.168.1.100'  # ← your MQTT broker / Home Assistant IP
MQTT_BASE_TOPIC = 'modbus/dxe007r'

# Register definitions
REGISTERS = [
    {"name": "measured_psi",  "address": 33},  # 30034
    {"name": "measured_gpm",  "address": 34},  # 30035
    {"name": "measured_ft",   "address": 35},  # 30036
    {"name": "target_hz",     "address": 36},  # 30037
    {"name": "target_psi",    "address": 37},  # 30038
    {"name": "target_gpm",    "address": 38},  # 30039
]

# ------------------------
# Helpers
# ------------------------

def read_float32(client, address):
    # Read 2 registers (32-bit float), Input Register = Function Code 0x04
    result = client.read_input_registers(address=address, count=2, slave=MODBUS_SLAVE_ID)
    if result.isError():
        print(f"Error reading address {address}")
        return None
    # Combine two 16-bit registers into float32 (big endian)
    regs = result.registers
    packed = struct.pack('>HH', regs[0], regs[1])
    value = struct.unpack('>f', packed)[0]
    return value

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

print("Starting Modbus to MQTT loop...")

while True:
    if modbus_client.connect():
        for reg in REGISTERS:
            value = read_float32(modbus_client, reg["address"])
            if value is not None:
                topic = f"{MQTT_BASE_TOPIC}/{reg['name']}"
                print(f"{topic}: {value:.2f}")
                mqtt_client.publish(topic, round(value, 2))
        modbus_client.close()
    else:
        print("Modbus connection failed")
    
    time.sleep(10)  # Poll every 10 seconds