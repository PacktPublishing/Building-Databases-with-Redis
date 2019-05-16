# -*- coding: utf-8 -*-
"""The Simplest Wiki Application

This application is intended to demonstrate possibilities of Redis Database
used as a main storage for an application.
"""
import os.path
import redis
import sys
import web

# Connection to Database: this is how we work with Redis
database = redis.StrictRedis(host='localhost', port=6379, db=0)

main_path = os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__))
render = web.template.render(os.path.join(main_path, 'templates'))

urls = (
	'/', 'index',
	'/page', 'page',
)

class WikiPage(object):
	"""Holds model of the wiki page

	"""
	title = ""
	text = ""
	
	def __init__(self, title, text):
		self.title = title
		self.text = text


class index:
	"""Handles root page of the overall web application
	
	""" 	
	def GET(self):
		"""Performs GET request processing: must show list of pages
		
		"""
		cache = database.get('cache:index')
		if cache == None:
			print 'non-cached'
			# You can use `scan` here also
			titles = database.keys('page:title:*')
			# We take several first character to disply short text using 'getrange'
			shorts = [database.getrange('page:title:{0}'.format(title.split(':')[-1]), 0, 20) for title in titles]
			# Creating page model represented by `WikiPage` class
			pages = [WikiPage(title.split(':')[-1], short + '...') for title, short in zip(titles, shorts)]
			
			html = render.index(pages)
			database.set('cache:index', html)
			return html
		else:
			return cache


class page:
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
			index.index_page_cache = ""
			return render.page_new()
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
			raise web.redirect('/')
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


def run_wiki_app():
    wiki_app = web.application(urls, globals())
    wiki_app.run()


if __name__ == "__main__":
	run_wiki_app()