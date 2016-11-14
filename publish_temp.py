'''
/*
 * Copyright 2010-2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
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
#For TMP 102 sensor
import pigpio
def tmp102_reading(byte0, word0):
	#calculation of the temperature based on 
	#the first word and the first byte
	
	# !!! not tested for negative temperatures !!!!
	#last 4 bits of the word0
	l4b = (t_word & 0b1111000000000000)>>12
	temperature = ((byte0<<4) | l4b) * 0.0625
	return temperature

#i2c bus of the Raspberry Pi 3
i2c_bus = 1
#TMP 102 address on the i2c bus
addr = 0x48
dev_pi = pigpio.pi()
dev_tmp = dev_pi.i2c_open(i2c_bus, addr, 0)
register_n = 0
#--------------

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
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()
#myAWSIoTMQTTClient.subscribe("sdk/test/Python", 1, customCallback)
#myAWSIoTMQTTClient.subscribe("iotbutton/+",1, customCallback)
#time.sleep(2)

# Publish to the topic in a loop
loopCount = 0
command_str = ''
delay_s = 60
sensor_sn = '00000001'
topic = 'myrpi/'+sensor_sn

try:
	while True:
		loopCount += 1
		t_byte = dev_pi.i2c_read_byte_data(dev_tmp, 0)
		t_word = dev_pi.i2c_read_word_data(dev_tmp, 0)
		t = tmp102_reading(t_byte, t_word)
		timestamp = datetime.datetime.now()
		print(' Temperature: {} C   Loop # {:d}'.format(t,loopCount))
		print(' Time: {} \n'.format(timestamp))
		msg = '"Device": "{:s}", "Temperature": "{}", "Loop": "{}"'.format(sensor_sn, t,loopCount)
		msg = '{'+msg+'}'
		myAWSIoTMQTTClient.publish(topic, msg, 1)
		print('Sleeping...')
		time.sleep(delay_s)
except KeyboardInterrupt:
	pass

dev_pi.i2c_close(dev_tmp)
myAWSIoTMQTTClient.disconnect()
print('Disconnected from AWS')