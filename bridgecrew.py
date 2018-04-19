# -*- coding: utf-8 -*-

from datetime import datetime
import os
import urllib2
from uuid import uuid4

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
		if not require_admin(self):
			return
		
		template_vals = generate_base_template_vals(self)
		template_vals['title'] = 'Edit Bridge Crew'
		template_vals['page'] = 'bridgecrew'
		
		req_id = self.request.get('id')
		
		if not req_id:
			while True:
				# Create a new ID and verify it is unique.
				new_id = uuid4().hex
				if not BridgeCrew.query(BridgeCrew.id == new_id).get():
					new_crew = BridgeCrew()
					new_crew.id = new_id
					template_vals['crew'] = new_crew
					break
		else:
			crew = BridgeCrew.query(BridgeCrew.id == req_id).get()
			if crew:
				template_vals['crew'] = crew
			else:
				self.error(404)
				return
		
		template = JINJA_ENVIRONMENT.get_template('bridge_crew_edit.html')
		self.response.write(template.render(template_vals))
	
	def post(self, args):
		import logging
		logging.debug('SNTHOISNTHOISNT')
		if not require_admin(self):
			return
		
		logging.debug('UPDATE RECEIVED!')
		req_id = self.request.get('id')
		logging.debug('ID = ' + req_id)
		if not req_id:
			self.error(422)
			return
		
		crew = BridgeCrew.query(BridgeCrew.id == req_id).get()
		if not crew:
			crew = BridgeCrew()
			crew.id = req_id
		
		# Update Crew members.
		for crew_position in ['admiral', 'captain', 'first_officer', 'ops', 'comms', 'engi']:
			crew_member = self.request.get(crew_position)
			if crew_member or crew_member == '':
				crew_member = crew_member.strip()
				setattr(crew, crew_position, crew_member)
		
		# Update dates.
		for date_param in ['start', 'end']:
			date = self.request.get(date_param)
			if date:
				date = urllib2.unquote(date)
				date = datetime.strptime(date, '%Y-%m-%dT%H:%M')
				setattr(crew, date_param, date)
			else:
				setattr(crew, date_param, None)
		
		# Save the updated Crew.
		crew.put()
		
		self.redirect('/bridgecrew', code=303)

app = webapp2.WSGIApplication([
	('/bridgecrew/?', BridgeCrewViewPage),
	('/bridgecrew/edit/?(\?.*)?', BridgeCrewEditPage)
])
