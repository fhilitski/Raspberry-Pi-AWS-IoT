'''
/*
 * Temperature sensors TMP006 and TMP102 - publish readings to AWS IoT
 *
 * AWS SDK Code:
 Copyright 2010-2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 */
 '''
#fix for the imports
import os
import sys
import AWSIoTPythonSDK
sys.path.insert(0, os.path.dirname(AWSIoTPythonSDK.__file__))
# Now the import statement should work
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

#old imports
#from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
#import sys

import logging
import time
import getopt
import datetime
#--------------------

#Define device parameters
loopCount = 0 # counter of published messages
command_str = '' #
topic = "myrpi/livingroom" # IoT topic
delay_s = 300 # delay between publishing messages
sensor_sn = 'dev_r00000003' # sensor serial numbers

#--------------------
#for I2C bus
import pigpio
import tmp_sensors
#i2c bus of the Raspberry Pi 3
i2c_bus = 1
#TMP 102 address on the i2c bus
addr_102 = 0x48
#TMP 006 address
addr_006 = 0x40
#for TMP006 read from register 0x0
reg006 = 1
#for TMP102 register is 0x1
reg102 = 0

dev_pi = pigpio.pi()
tmp006 = dev_pi.i2c_open(i2c_bus, addr_006, 0)
tmp102 = dev_pi.i2c_open(i2c_bus, addr_102, 0)

# Custom MQTT message callback
def customCallback(client, userdata, message):
	print("Received a new message: ")
	print(message.payload)
	print("from topic: ")
	print(message.topic)
	print("--------------\n\n")

# Usage
usageInfo = """Usage:

Use certificate based mutual authentication:
python basicPubSub.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath>

Use MQTT over WebSocket:
python basicPubSub.py -e <endpoint> -r <rootCAFilePath> -w

Type "python basicPubSub.py -h" for available options.
"""
# Help info
helpInfo = """-e, --endpoint
	Your AWS IoT custom endpoint
-r, --rootCA
	Root CA file path
-c, --cert
	Certificate file path
-k, --key
	Private key file path
-w, --websocket
	Use MQTT over WebSocket
-h, --help
	Help information
"""

# Read in command-line parameters
useWebsocket = False
host = ""
rootCAPath = ""
certificatePath = ""
privateKeyPath = ""
try:
	opts, args = getopt.getopt(sys.argv[1:], "hwe:k:c:r:", ["help", "endpoint=", "key=","cert=","rootCA=", "websocket"])
	if len(opts) == 0:
		raise getopt.GetoptError("No input parameters!")
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			print(helpInfo)
			exit(0)
		if opt in ("-e", "--endpoint"):
			host = arg
		if opt in ("-r", "--rootCA"):
			rootCAPath = arg
		if opt in ("-c", "--cert"):
			certificatePath = arg
		if opt in ("-k", "--key"):
			privateKeyPath = arg
		if opt in ("-w", "--websocket"):
			useWebsocket = True
except getopt.GetoptError:
	print(usageInfo)
	exit(1)

# Missing configuration notification
missingConfiguration = False
if not host:
	print("Missing '-e' or '--endpoint'")
	missingConfiguration = True
if not rootCAPath:
	print("Missing '-r' or '--rootCA'")
	missingConfiguration = True
if not useWebsocket:
	if not certificatePath:
		print("Missing '-c' or '--cert'")
		missingConfiguration = True
	if not privateKeyPath:
		print("Missing '-k' or '--key'")
		missingConfiguration = True
if missingConfiguration:
	exit(2)

# Configure logging
logger = None
if sys.version_info[0] == 3:
	logger = logging.getLogger("core")  # Python 3
else:
	logger = logging.getLogger("AWSIoTPythonSDK.core")  # Python 2
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = None
if useWebsocket:
	myAWSIoTMQTTClient = AWSIoTMQTTClient("basicPubSub", useWebsocket=True)
	myAWSIoTMQTTClient.configureEndpoint(host, 443)
	myAWSIoTMQTTClient.configureCredentials(rootCAPath)
else:
	myAWSIoTMQTTClient = AWSIoTMQTTClient("basicPubSub")
	myAWSIoTMQTTClient.configureEndpoint(host, 8883)
	myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1) # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()
#myAWSIoTMQTTClient.subscribe("sdk/test/Python", 1, customCallback)
#myAWSIoTMQTTClient.subscribe("iotbutton/+",1, customCallback)
#time.sleep(2)


try:
	while True:
		loopCount += 1
		#start with tmp102
		data = dev_pi.i2c_read_word_data(tmp102, reg102)
		t102 = tmp_sensors.tmp102_reading(data)
		#read TMP006
		data = dev_pi.i2c_read_word_data(tmp006, reg006)
		t006 = tmp_sensors.tmp006_reading(data)
		
		timestamp = datetime.datetime.now()
		print(' Temperature\nTMP006: {} C\nTMP102: {}C\nLoop #{:d}\n'.format(t006,t102,loopCount))
		print('Time: {}\n'.format(timestamp))
		msg = '"Device": "{:s}", "TMP102": "{}", "TMP006": "{}", "Loop": "{}"'.format(sensor_sn, t102, t006,loopCount)
		msg = '{'+msg+'}'
		myAWSIoTMQTTClient.publish(topic, msg, 1)
		print('Sleeping...')
		time.sleep(delay_s)
except KeyboardInterrupt:
	pass
	
print('Exiting the loop');
r = dev_pi.i2c_close(dev_tmp)
myAWSIoTMQTTClient.disconnect()
print('Disconnected from AWS')