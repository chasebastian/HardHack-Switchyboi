from gpio_96boards import GPIO

#coding: utf-8
import pygatt
import logging
import time
from pygatt.util import uuid16_to_uuid
from pygatt.exceptions import NotConnectedError, NotificationTimeout

# Log configuration
logging.basicConfig()
logging.getLogger('pygatt').setLevel(logging.DEBUG)

global flag
flag = 0
answer = str(data)

GPIO_MDI = GPIO.gpio_id('GPIO_K')
GPIO_BO = GPIO.gpio_id("GPIO_I')

#coding: utf-8
import pygatt
import logging
import time
from pygatt.util import uuid16_to_uuid
from pygatt.exceptions import NotConnectedError, NotificationTimeout

# Log configuration
logging.basicConfig()
logging.getLogger('pygatt').setLevel(logging.DEBUG)

global flag
flag = 0

# List of the adapters there are trying to connect to Bluetooth.
adapters = []

# List of devices.
devices = []

# List of data of the devices to show for user (connected number and MAC).
connected_devices_list = []

# Characteristic to receive data.
uuid_received_data = uuid16_to_uuid(0x0000)    
# Characteristic to sent data.    
uuid_sent_data = uuid16_to_uuid(0x0003)    
# Characteristic used to receive the name of the application.        
uuid_bluetooth_mac = uuid16_to_uuid(0x0004)        

def callback(handle, data):
    
    # The callback function is called just when the characteristic to sent data is subscribed. 
    print "Received data: " + str(data)
    # Sending "exit" string from any connected device, the python program will be closed, 
    # setting the flag. 
    if str(data) == "exit":
        global flag
        flag = 1
    answer = str(data)
    try:
        s =  str(data)    
        data = bytearray (answer)
        data = data[:2] + ": " + data[2:]
        # Interpretation of the communication protocol between App and DB:
        
        # If the first two digits received from Dragonboard are DB, 
        # the board will send the string to all connected devices.
        if s[:2]  == 'DB':
            for device in devices:
                device.char_write(uuid_sent_data, data, False) 
                
        # If the first digits received from Dragonboard are "D" followed by a number less than number of connected devices, 
        # the board will send the string to the device corresponding to that number.
        elif s[0] == 'D' and s[1].isdigit() and int(s[1])<len(devices):
            devices[int(s[1])].char_write(uuid_sent_data, data, False)   
        # If there is no prefix on the received data, the string is just received on Dragonboard.
    except NotificationTimeout as e:
        print e
 
# Function to connect to device.           
def connect_to_device (adapter, MAC):
        connected = 0
        timeout = 5
        try:
            # The program tries to connect to a public MAC Bluetooth
            # (normally used on Android 5 or lower).
            print "Static MAC connection"
            
            # The False parameter ensure that the adapter doesn't restart,
            # disconnecting other previously connected devices.
            adapter.start(False)
            device = adapter.connect(MAC, timeout)
            
            # If the connection is established, the value of connected variable is changed to 1,
            # else the connected variable stills being 0.
            connected = 1
            
            # If the connection doesn't be established with public MAC Bluetooth,
            # the program tries to connect to random MAC Bluetooth.
        except NotConnectedError:
            print NotConnectedError.message
            # Adapter is restarted to try another connection.       
            time.sleep(2)
            adapter.clear_bond(MAC)
            adapter.start(False)
            try:
                # The program tries to connect to random MAC Bluetooth 
                # (normally used on Android 6 or higher).
                # In this case, the pygatt.BLEAddressType.random parameter is used in the connect function.
                print "Random MAC connection"
                device = adapter.connect(MAC, timeout, pygatt.BLEAddressType.random)
                connected = 1
            except NotConnectedError:
                print NotConnectedError.message
                return ("", connected)
        if connected == 1:
            try:
                # If the connection is established with any device, characteristics are discovered
                # and using subscribe function is initiated the communication between application and Dragonboard,
        	# waiting for a message of the application.
                device.discover_characteristics()
                device.subscribe(uuid_sent_data, indication = False)
                device.subscribe(uuid_received_data, callback, False)
                device.subscribe(uuid_bluetooth_mac, indication = False)
                # If the application send its name to Dragonboard using uuid_bluetooth_mac, 
                # the connection is maintained.
        	# In this example, the application name is BLEChat.
                if device.char_read(uuid_bluetooth_mac) == "BLEChat":
                    connected = 1
                    return (device, connected)
                else:
                    # If the application doesn't send its name, the connection with device is stopped.
                    print "\nThe name of the application doesn't match with the characteristic"
                    connected = 0
                    adapter.stop()
                    return ("", connected)
            except pygatt.exceptions.BLEError:
                connected = 0
                return ("", connected)                        
                    
try:   
    # scan_adapter it's a scan used to list all founded devices.    
    scan_adapter = pygatt.GATTToolBackend()
    scan_adapter.start()
    ble_devices = scan_adapter.scan(timeout = 10, run_as_root = True)
    scan_adapter.stop()
    
    # If the program doesn't find any bluetooth device, the program will be closed, 
    # setting the flag.    
    if ble_devices == []:
        print "\nScan didn't find any devices. Finishing program."
        flag = 1
    cont = 0
    
    # Prints all devices founded by scan on Dragonboard.
    for ble_device in ble_devices:
        cont = cont + 1
        print str(cont) + "- " + str(ble_device['name']) + ": " + str(ble_device['address'])     
    
    # All adapters are initialized before the connection is established.      
    for i in xrange(0, len(ble_devices)):
        adapters.append(pygatt.GATTToolBackend())
        time.sleep(1)
    time.sleep(1)
            
    # Connects with all devices that are with opened application.
    cont = 0    
    i = 0
    for device in ble_devices:
        print "\nConnecting to: " + device['address']
        d = connect_to_device(adapters[cont], device['address'])
        if d[1] == 1:
            # List with dictionary including data that will send to application.
            connected_device = {'number':i,'address':device['address']}
            connected_devices_list.append(connected_device)
            i = i + 1
            devices.append(d[0])
        cont = cont + 1 
        time.sleep(2)
    print "Connection to devices finished.\n"

    # Shows a list of connected devices with each number used in the communication protocol. 
    for i in connected_devices_list:
        print "D"+str(i['number'])+"- "+i['address']
    print "\n"
                
    # If none connection was established, the program will be closed,
    # setting the flag.
    if devices == []:
        print "\nNo connection to devices. Finishing program."
        flag = 1

    # Sends to application a list of connected devices.
    for device in devices:
        print device
        s = "Device list: "
        device.char_write(uuid_sent_data, bytearray(s), False)    
        
    for connected_device in connected_devices_list:
        s = "D" + str(connected_device["number"]) +":" + str(connected_device["address"])
        data = bytearray(s)
        for device in devices:
            device.char_write(uuid_sent_data, data, False)
   
except NotConnectedError:
    print NotConnectedError.message
  
finally:
    # Structure to maintain the python program opened, waiting for a message coming from callback function.

    while True:   
        # Stops all adapter, and close python program when the flag is setted.
        if flag == 1:
            scan_adapter.stop()
            for adapter in adapters:   
                adapter.stop()
            break


pins = (
	
	(GPIO_MDI, 'in'),
	(GPIO_BO, 'out')
	
)

def alarm():
	while data:
		
		motionDetected = GPIO_MDI.read(GPIO_MDI)
		if motionDetected:
			GPIO_BO.write(GPIO_BO, 1)
	GPIO_BO.write(GPIO_BO,0)
	time.sleep(10000)
	alarm()
