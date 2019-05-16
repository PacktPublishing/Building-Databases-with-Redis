# The script implements an example of Redis pipelining

import redis

database1 = redis.StrictRedis(host='localhost', port=6379, db=0)

def make_pipelined_request():
	pipeline = database1.pipeline()  # Here we create pipeline
	
	for i in range(10000):        # Here we make a 10k iterations loop
		pipeline.incr("somekey")  # Increase 'somekey' value every interation
	
	pipeline.execute()            # Execute bunch of commands
	
	return database1.get("somekey")  # Return the result of somekey


if __name__ == '__main__':
	# Here we print the result returned by function ('somekey' value)
	print(make_pipelined_request())
