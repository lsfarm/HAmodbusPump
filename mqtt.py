# modbus_to_mqtt.py
from pymodbus.client import ModbusSerialClient
import paho.mqtt.client as mqtt
import time

# ---- Modbus Config ----
MODBUS_PORT = '/dev/ttyUSB0'
MODBUS_BAUDRATE = 9600
MODBUS_SLAVE_ID = 1
REGISTER_ADDRESS = 0  # e.g., 40001 = 0
REGISTER_COUNT = 1

# ---- MQTT Config ----
MQTT_BROKER = '192.168.1.100'  # IP of Home Assistant or MQTT broker
MQTT_TOPIC = 'modbus/dxe007r/voltage'

# ---- Create clients ----
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

# ---- Main Loop ----
while True:
    if modbus_client.connect():
        result = modbus_client.read_holding_registers(
            address=REGISTER_ADDRESS,
            count=REGISTER_COUNT,
            slave=MODBUS_SLAVE_ID
        )
        if result.isError():
            print("Modbus read error:", result)
        else:
            value = result.registers[0]
            print("Read value:", value)
            mqtt_client.publish(MQTT_TOPIC, value)
        modbus_client.close()
    else:
        print("Modbus connection failed")

    time.sleep(5)  # Read every 5 seconds
