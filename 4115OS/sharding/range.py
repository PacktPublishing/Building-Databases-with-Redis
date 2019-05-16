# -*- coding: utf-8 -*-
"""The Simplest Range Sharing

This application is intended to demonstrate possibilities of Redis Database
in range sharding.
"""
import redis

# Connection to Database: this is how we work with Redis
database1 = redis.StrictRedis(host='localhost', port=6379, db=0)
database2 = redis.StrictRedis(host='localhost', port=6380, db=0)


def get_shard(user_id=0):
	"""Return shard dependent on user_id

	Preallocated range for users in th first shard is [1..499].
	Other users are going to the second shard: [500.. inf]

	"""
	if 0 < user_id < 500:
		return database1 
	else:
		return database2


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
	user1 = {'id': 4, 'value': 'user1@example.com'}
	user2 = {'id': 504, 'value': 'user2@example.com'}

	# Saving users' records on appropriate shards
	save_user(user1)
	save_user(user2)