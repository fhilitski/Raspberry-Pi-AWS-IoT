#!bin/python3
#reading TMP 102 and TMP 106 sensors

import pigpio
import time

def tmp102_reading(byte0, word0):
	#calculation of the temperature based on 
	#the first word and the first byte
	#sensor reading are the first 12 bits
	
	# !!! not tested for negative temperatures !!!!
	#last 4 bits of the word0
	l4b = (word0 & 0b1111000000000000)>>12
	temperature = ((byte0<<4) | l4b) * 0.0625
	return temperature
	
def tmp006_reading(byte0, word0):
	#calculation of the temperature based on 
	#the first word and the first byte
	#we need to extract first 14 bits
	
	# !!! not tested for negative temperatures !!!!
	#last 6 bits of the word0
	l6b = (word0 & 0b1111110000000000)>>10
	temperature = ((byte0<<6) | l6b) / 32
	return temperature
	
	

#i2c bus of the Raspberry Pi 3
i2c_bus = 1
#TMP 102 address on the i2c bus
addr = 0x48


dev_pi = pigpio.pi()
dev_tmp = dev_pi.i2c_open(i2c_bus, addr, 0)
if dev_tmp > 0:

	register_n = 0
	try:
		while True:
			t_byte = dev_pi.i2c_read_byte_data(dev_tmp, 0)
			t_word = dev_pi.i2c_read_word_data(dev_tmp, 0)
			t = tmp102_reading(t_byte, t_word)
			print(' Temperature: {} C'.format(t))
			time.sleep(1)
	except KeyboardInterrupt:
		pass
	print('Exiting the loop');
	
else:
	print('Failed to open I2C');
	
r = dev_pi.i2c_close(dev_tmp)