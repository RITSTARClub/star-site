#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from google.appengine.api import users

import jinja2
import webapp2

from models import BridgeCrew

JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates/')),
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)

class BridgeCrewViewPage(webapp2.RequestHandler):
	def get(self):
		template_vals = {
			'title': 'Bridge Crew',
			'page': 'bridgecrew'
		}
		
		user = users.get_current_user()
		if user:
			template_vals['user'] = user
			template_vals['admin'] = users.is_current_user_admin()
			template_vals['logout_url'] = users.create_logout_url(self.request.uri)
		else:
			template_vals['login_url'] = users.create_login_url(self.request.uri)
		
		# Get the bridge crew.
		template_vals['current_crew'] = BridgeCrew.query().order(-BridgeCrew.start).get()
		
		# Get past bridge crews.
		template_vals['past_crews'] = BridgeCrew.query().order(-BridgeCrew.start).fetch(limit=None)[1:]
		
		template = JINJA_ENVIRONMENT.get_template('bridge_crew_view.html')
		self.response.write(template.render(template_vals))

class BridgeCrewEditPage(webapp2.RequestHandler):
	def get(self, args):
		# TODO: Create proper bridge crew editor.
		if not users.is_current_user_admin():
			self.error(403)
			return
		
		new_crew = BridgeCrew()
		new_crew.put()

app = webapp2.WSGIApplication([
	('/bridgecrew/?', BridgeCrewViewPage),
	('/bridgecrew/edit/?(\?.*)?', BridgeCrewEditPage)
])
