# -*- coding: utf-8 -*-
"""The Simplest Range Sharing

This application is intended to demonstrate possibilities of Redis Database
in range sharding.
"""
import redis
import zlib

# Connection to Database: this is how we work with Redis
database1 = redis.StrictRedis(host='localhost', port=6379, db=0)
database2 = redis.StrictRedis(host='localhost', port=6380, db=0)

# number of shards
NUM_SHARDS = 2

def get_shard(user_id):
	"""Return shard dependent on user_id

	The shard is calculated base on crc32 function

	"""
	hash_number = zlib.crc32('user:id:{0}'.format(user_id))
	return globals()['database{0}'.format(hash_number % NUM_SHARDS + 1)]


def save_user(user):
	"""Persist user's data in Redis database.

	Also appropriate shard is calculated.
	"""
	# Here we determine shard
	shard = get_shard(user['id'])

	# Saving on appropriate shard
	shard.set('user:id:{0}'.format(user['id']), user['value'])


if __name__ == '__main__':
	# Creating two records for 2 users
	user1 = {'id': 1, 'value': 'user1@example.com'}
	user2 = {'id': 4, 'value': 'user2@example.com'}

	# Saving users' records on appropriate shards
	save_user(user1)
	save_user(user2)