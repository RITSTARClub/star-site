# -*- coding: utf-8 -*-

import os

from google.appengine.api import users

import jinja2
import webapp2

from models import BridgeCrew
from utils import require_admin, generate_base_template_vals

JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates/')),
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)

class BridgeCrewViewPage(webapp2.RequestHandler):
	def get(self):
		template_vals = generate_base_template_vals(self)
		template_vals['title'] = 'Bridge Crew'
		template_vals['page'] = 'bridgecrew'
		
		# Get the bridge crew.
		template_vals['current_crew'] = BridgeCrew.query().order(-BridgeCrew.start).get()
		
		# Get past bridge crews.
		template_vals['past_crews'] = BridgeCrew.query().order(-BridgeCrew.start).fetch(limit=None)[1:]
		
		template = JINJA_ENVIRONMENT.get_template('bridge_crew_view.html')
		self.response.write(template.render(template_vals))

class BridgeCrewEditPage(webapp2.RequestHandler):
	def get(self, args):
		# TODO: Create proper bridge crew editor.
		if not require_admin(self):
			return
		
		new_crew = BridgeCrew()
		new_crew.put()

app = webapp2.WSGIApplication([
	('/bridgecrew/?', BridgeCrewViewPage),
	('/bridgecrew/edit/?(\?.*)?', BridgeCrewEditPage)
])
