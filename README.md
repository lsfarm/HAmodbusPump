# HAmodbusPump
mosquitto_sub -h 192.168.1.100 -t "modbus/dxe007r/#"

•	If values look wrong:
	•	Try swapping register order: struct.pack('>HH', regs[1], regs[0])
	•	Try different data types (int16, uint16, etc.) if float32 isn’t right
	•	If read_input_registers() fails:
	•	Make sure Modbus slave ID and wiring are correct
	•	Ensure no other client is locking the port (e.g., Modbus Poll)