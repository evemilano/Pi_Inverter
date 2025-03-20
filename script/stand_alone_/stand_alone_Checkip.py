from pymodbus.client import ModbusTcpClient

# Imposta l'IP dell'inverter (dopo averlo trovato con nmap)
inverter_ip = "192.168.1.11"  # Sostituiscilo con l'IP corretto
port = 502  # Porta Modbus TCP

# Crea il client Modbus TCP
client = ModbusTcpClient(inverter_ip, port=port)
client.connect()

if not client.is_socket_open():
    print(f"Nessuna connessione Modbus aperta su {inverter_ip}.")
    client.close()
else:
    try:
        print(f"🔍 Connessione riuscita a {inverter_ip}!")

        # Proviamo a leggere la potenza attuale (registro 32080)
        response = client.read_holding_registers(address=32080, count=2, slave=1)

        if response and not response.isError():
            power = response.registers[0] / 10  # Conversione potenza in W
            print(f"✅ Potenza attuale dell'inverter: {power} W")
        else:
            print(f"Nessuna risposta Modbus dal dispositivo.")

    except Exception as e:
        print(f"Errore nella lettura Modbus: {e}")

    client.close()
