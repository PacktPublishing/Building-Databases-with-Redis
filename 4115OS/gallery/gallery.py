# -*- coding: utf-8 -*-
"""Image Gallery Application

This application is intended to demonstrate possibilities of Redis Database
used as a main storage for an application. Here we present:
 - Hashes
 - Lists

"""
import hashlib
import os.path
import redis
import sys
import web

# Connection to Database: this is how we work with Redis
database = redis.StrictRedis(host='localhost', port=6379, db=0)

# Paths for assistive folders
main_path = os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__))
images_path = os.path.join(main_path, 'images')

render = web.template.render(os.path.join(main_path, 'templates'))

urls = (
	'/',         'index',
	'/login',    'login',
	'/logout',   'logout',
	'/register', 'register',
	'/gallery',  'gallery',
)

class TagCloud(object):
	"""Holds model of the unscored tag cloud

	"""
	uid = None
	cloud = set()

	def __init__(self, uid):
		# Setting user id
		self.uid = uid

		# Getting user's galleries identifiers
		gallery_tag_keys =\
			["gallery:tags:" + gid 
			for gid in database.lrange("gallery:user:{0}".format(uid), 0, -1)]
		
		# Building clound
		self.cloud = database.sunion(gallery_tag_keys)



class Gallery(object):
	"""Holds model of the image gallery

	"""
	def __init__(self, gid=None, title="", description="", owner=None, tags=None):
		self.gid = gid
		self.title = title
		self.description = description
		self.owner = owner
		self.tags = set() # a set of tags for gallery (stored in Redis in set either)

	@staticmethod
	def load_with_gid(gid):
		"""Load gallery data with given identifier

		"""
		# Getting all gallery data fields
		data = database.hmgetall("gallery:{0}".format(gid))
		
		# Getting gallery tags
		tags = set(database.smembers("gallery:tags:{0}".format(gid)))
		
		return Gallery(gid, data["title"], data["description"], data["owner"], tags)

	def save():
		"""Update gallery data or insert new gallery

		"""
		if self.gid == None: # No 'gallery ID': create new by inserting into DB
			# "INCR" is used for gallery ID generation
			self.gid = database.incr('next-gallery-id')

			# Saving gallery fields info into hash
			database.hmset("gallery:{0}".format(self.gid),
				{
					"title": self.title,
					"description": self.description,
					"owner": self.owner,
				}
			)

			# Pushing new gallery into galleries list for user
			database.rpush("gallery:user:{0}".format(self.owner), self.gid)

			# Saving gallery tags
			database.delete("gallery:tags:{0}".format(self.gid))            # Removing old tags
			database.sadd("gallery:tags:{0}".format(self.gid), *self.tags)  # Saving new tags
		
		else: # gallery already exists so we just update gallery object fields
			# Saving gallery fields info into hash
			database.hmset("gallery:{0}".format(self.gid),
				{
					"title": self.title,
					"description": self.description,
					"owner": self.owner,
				}
			)


class Image(object):
	"""Holds model of the image

	"""
	def __init__(self, name, data):
		self.name = name
		self.hashed = hashlib.md5(data).hexdigest()


class User(object):
	"""Holds model for the user.

	Performs user's data storage management using the next database structure:

	next-user-id: <uid>             - holds the next number of user ID to generate
	
	"user:<uid>": {                 - holds needed user data as a hash
		login: <login>
		pasword: <password>
		status: <status>
		date_of_birth: <date_of_birth>
	}                               
	
	"users": {                      - holds hash map of logins to user ids
		<login>: <id>
	}

	"""
	def __init__(self, uid=None, login="", password="", status="", date_of_birth=None):
		self.uid = None
		self.login = login
		self.password = password
		self.status = status
		self.date_of_birth = date_of_birth
		self.tags_cloud_scored = []  # tags cloud with scores
		self.tags_cloud = set()      # tags cloud without scores

	@staticmethod
	def load_with_uid(uid):
		"""Load user data from database with given User ID

		"""
		# "HMGET" to receive several fields in one query - user data
		data = database.hmget("user:{0}".format(self.uid), "login", "password", "status", "date_of_birth")
		
		user = User(uid, data["login"], data["password"], data["status"], data["date_of_birth"])
		
		# "ZRANGEBYSCORE" for reading tags cloud
		user.tags_cloud_scored = database.zrangebyscore(
			"user:tagscloudscored:{0}".format(uid), 0, -1
		)

		return user

	@staticmethod
	def load_with_login(login):
		"""Load user data from database with given login
		
		"""
		# "HGET" to receive one hash field - uid stored in a login-represented key 
		uid = database.hget("users", login)

		if uid is None:
			return None

		# Using "HGETALL" as a shortcut to receive all hash fields - user data
		data = database.hgetall("user:{0}".format(uid))
		return User(uid, data["login"], data["password"], data["status"], data["date_of_birth"])

	def save(self):
		"""Save user data to database (persist)

		"""
		if self.uid is None:  # No uid: creating new user by inserting new info
			# "INCR" is used fro UID generation
			self.uid = database.incr("next-user-id")

			# "HSETNX" allows to set value for key in hash if key does not exist
			result = database.hsetnx("users", self.login, self.uid)
			if result == 0:
				return
			else:
			# "HMSET" allows to set many keys for hash map
				database.hmset("user:{0}".format(self.uid),
					{
						"login": self.login,
						"status": self.status,
						"password": self.password,
						"date_of_birth": self.date_of_birth
					}
				)
		else:  # Uid exists: updating information stored in this object
			# "HMSET" allows to set many keys for hash map
			database.hmset("user:{0}".format(self.uid),
				{
					"login": self.login,
					"status": self.status,
					"password": self.password,
					"date_of_birth": self.date_of_birth
				}
			)

	@staticmethod
	def authenticate(login, password):
		user = User.load_with_login(login)
		if user is not None and password == user.password:
			return user
		return None


class index:
	"""Handles root page of the overall web application
	
	""" 	
	def GET(self):
		"""Show user login status and his/her list of galleries
		
		"""
		user = User.authenticate(web.cookies().get("login"), web.cookies().get("password"))

		if not user:
			web.seeother("/register")
			return

		# Getting number of galleries
		gcount = database.llen("gallery:user:{0}".format(user.uid))

		# Setting up pagination control
		request_data = web.input()

		# Calculating number of pages to show
		page = int(request_data.get('page', 0))
		perpage = int(request_data.get('perpage', 1))
		pages = gcount / perpage + 1

		# Getting user's galleries identifiers
		gallery_ids = database.lrange("gallery:user:{0}".format(user.uid), page * perpage, (page + 1) * perpage - 1)
		
		# Getting user's galleries data
		galleries = [database.hmgetall("gallery:{0}".format(gid)) for gid in gallery_ids]

		# Rendering page
		html = render.index(user, galleries or [], page, pages, perpage)
		return html


class login:
	"""Handles login into application

	"""
	def GET(self):
		request_data = web.input()
		user = User.load_with_login(request_data.login)

		if user is not None and user.password == request_data.password:
			# Saving login and password in cookies (DONT do THAT in production, use encryption and hashing)
			web.setcookie("login", user.login, 10**6)
			web.setcookie("password", user.password, 10**6)

		return web.seeother('/')


class logout:
	"""Handles logout from application

	"""
	def GET(self):
		# Unsetting cookies
		web.setcookie("login", "", -1)
		web.setcookie("password", "", -1)
		
		# Going back to home page
		web.seeother('/')


class register:
	"""Handles registration

	"""
	def GET(self):
		return render.register()

	def POST(self):
		# Create new user based on request input
		request_data = web.input()
		user = User(None, request_data.login, request_data.password, "", request_data.date_of_birth)
		
		# Insert user into Redis database
		user.save()

		return web.seeother('/login?login={0}&password={1}'.format(user.login, user.password))


class gallery:
	"""Handles pages views and operations
	
	"""
	def GET(self):
		"""Performs operations on pages: view and new
		
		"""
		# Here we take request parameters, those after '?'
		request_data = web.input()
		# Decide what action to perform: 'new' | 'view' | 'del'
		action = request_data.action

		if action == 'new':
			return render.gallery_new()
		elif action == 'view':
			# Get value for key
			text = database.get('page:title:{0}'.format(request_data.title))
			# Using counter to increasea page views value
			views = database.incr('page:views:{0}'.format(request_data.title))
			return render.page(request_data.title, text, views)
		elif action == 'del':
			# 'del' Redis command is Python's reserved keyword.
			# That is why we use 'delete'.
			database.delete('page:title:{0}'.format(request_data.title))
			database.delete('page:views:{0}'.format(request_data.title))
			database.delete('cache:index')
			raise web.seeother('/')
		else:
			raise web.notfound()

	def POST(self):
		"""Performs operation on pages: save

		"""
		# Here we take request parameters
		request_data = web.input()
		# Decide what action to perform: 'save'
		action = request_data.action

		if action == 'save':
			# Set value for key
			database.set('page:title:{0}'.format(request_data.title), request_data.text)
			database.delete('cache:index')
			raise web.redirect('/page?action=view&title={0}&text={1}'.format(request_data.title, request_data.text))
		else:
			raise web.notfound()


def run_gallery_app():
    gallery_app = web.application(urls, globals())
    gallery_app.run()


if __name__ == "__main__":
	run_gallery_app()