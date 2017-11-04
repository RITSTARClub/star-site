# -*- coding: utf-8 -*-

import os
from datetime import datetime
from random import choice

import jinja2
import webapp2

from models import Mission, PageContent
from utils import require_admin, generate_base_template_vals

JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates/')),
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)


class HomePage(webapp2.RequestHandler):
	def get(self):
		template_vals = generate_base_template_vals(self)
		template_vals['page'] = 'home'
		
		# Get the home page text.
		home_content = PageContent.query(PageContent.page == 'home').get()
		template_vals['home_html'] = home_content.html_text if home_content else ''
		
		# Get the next five missions.
		# Include missions happening today.
		now = datetime.now()
		today = datetime(now.year, now.month, now.day)
		template_vals['missions'] = Mission.query(Mission.start >= today).order(Mission.start).fetch(limit=5)
		
		# Pick an end quote.
		template_vals['end_quote'] = choice([
			'Live long and prosper.',
			'May the Force be with you.',
			'Never give up!  Never surrender!'
		])
		
		template = JINJA_ENVIRONMENT.get_template('home.html')
		self.response.write(template.render(template_vals))

class AVTestPage(webapp2.RequestHandler):
	def get(self):
		template_vals = generate_base_template_vals(self)
		template_vals['title'] = 'A/V Test'
		
		template = JINJA_ENVIRONMENT.get_template('av_test.html')
		self.response.write(template.render(template_vals))

class GPlusRedirect(webapp2.RequestHandler):
	def get(self):
		self.redirect('https://plus.google.com/111596425090423212471', code=301)

app = webapp2.WSGIApplication([
	('/avtest/?', AVTestPage),
	('/\+', GPlusRedirect),
	('/?', HomePage)
])
