# Mass insertion example

import sys  # Gives access to standard output via sys.stdout

def generate(ips):
	# Command pattern according to Redis protocol
	pattern = '*3\r\n$3\r\nSET\r\n${0}\r\n{1}\r\n$1\r\n1\r\n'
	
	for ip in ips:  # Iterating over IP addresses
		# Writing generated commands into standard output
		sys.stdout.write(pattern.format(len(ip.encode('utf-8')), ip.encode('utf-8')))

if __name__ == '__main__':
	data = ''
	
	# Reading file with IP addresses
	with open('ips.txt', 'rt') as f:
		data = f.read()
	
	# Splitting addresses into a list
	ips = data.split('\n')
	
	# Generating commands in Redis protocol manner
	generate(ips)