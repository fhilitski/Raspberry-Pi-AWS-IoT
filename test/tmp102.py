#!bin/python3
#reading TMP 102 sensor

import pigpio
import time

def tmp102_reading(byte0, word0):
	#calculation of the temperature based on 
	#the first word and the first byte
	
	# !!! not tested for negative temperatures !!!!
	#last 4 bits of the word0
	l4b = (word0 & 0b1111000000000000)>>12
	temperature = ((byte0<<4) | l4b) * 0.0625
	return temperature
	
	

#i2c bus of the Raspberry Pi 3
i2c_bus = 1
#TMP 102 address on the i2c bus
addr = 0x48


dev_pi = pigpio.pi()
dev_tmp = dev_pi.i2c_open(i2c_bus, addr, 0)
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
r = dev_pi.i2c_close(dev_tmp)