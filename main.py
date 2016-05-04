#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from datetime import datetime

from google.appengine.api import users

import jinja2
import webapp2

from models import Mission

JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates/')),
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)


class HomePage(webapp2.RequestHandler):
	def get(self):
		template_vals = {
			'page': 'home'
		}
		
		# Get the next five missions.
		# Include missions happening today.
		now = datetime.now()
		today = datetime(now.year, now.month, now.day)
		template_vals['missions'] = Mission.query(Mission.start >= today).order(Mission.start).fetch(limit=5)
		
		template_vals['user'] = users.get_current_user()
		if template_vals['user']:
			template_vals['logout_url'] = users.create_logout_url(self.request.uri)
		else:
			template_vals['login_url'] = users.create_login_url(self.request.uri)
		
		template = JINJA_ENVIRONMENT.get_template('home.html')
		self.response.write(template.render(template_vals))


app = webapp2.WSGIApplication([
	('/', HomePage)
])
