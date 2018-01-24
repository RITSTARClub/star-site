# -*- coding: utf-8 -*-

import os
from uuid import uuid4

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

from models import APIKey, PageContent
from utils import require_admin, generate_base_template_vals
from semesters import get_all_semesters, get_current_semester

JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates/')),
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)

class AdminPage(webapp2.RequestHandler):
	def get(self, args):
		if not require_admin(self):
			return
		
		template_vals = generate_base_template_vals(self)
		template_vals['title'] = 'Admin Hub'
		template_vals['page'] = 'admin'
		template_vals['semesters'] = get_all_semesters()
		template_vals['current_semester'] = get_current_semester()
		
		# Get custom home page text.
		home_content = PageContent.query(PageContent.page == 'home').get()
		if not home_content:
			home_content = PageContent()
			home_content.page = 'home'
			home_content.text = ''
			home_content.put()
		
		template_vals['home_text'] = home_content.text
		
		template = JINJA_ENVIRONMENT.get_template('admin.html')
		self.response.write(template.render(template_vals))
	
	def post(self, args):
		if not require_admin(self):
			return
		
		home_text = self.request.get('home_text')
		if not home_text:
			self.error(422)
			self.response.write('<h1>422 Unprocessable Entity</h1>')
			return
		
		home_content = PageContent.query(PageContent.page == 'home').get()
		if not home_content:
			home_content = PageContent()
			home_content.page = 'home'
		
		home_content.text = home_text
		home_content.put()
		
		self.redirect('/admin', code=303)

class APIPage(webapp2.RequestHandler):
	def get(self, args):
		if not require_admin(self):
			return
		
		template_vals = generate_base_template_vals(self)
		template_vals['title'] = 'API Admin'
		template_vals['page'] = 'admin'
		
		template_vals['keys'] = APIKey.query().fetch(limit=None)
		
		template = JINJA_ENVIRONMENT.get_template('admin_api.html')
		self.response.write(template.render(template_vals))
		
	def post(self, args):
		if not require_admin(self):
			return
		
		# Ensure a name was passed.
		name = self.request.get('name')
		if not name:
			self.error(422)
			self.response.write('<h1>422 Unprocessable Entity</h1><p>No name was specified.</p>')
			return
		
		# Ensure the name has not already been used.
		existing_entity = APIKey.query(APIKey.name == name).get()
		if existing_entity:
			self.error(409)
			self.response.write('<h1>409 Conflict</h1><p>A key with that name already exists.</p>')
			return
		
		# Create a new ID and verify it is unique.
		while True:
			new_key = uuid4().hex
			if not APIKey.query(APIKey.key == new_key).get():
				break
		
		# Add the new key entity to the datastore.
		new_entity = APIKey()
		new_entity.name = name
		new_entity.key = new_key
		new_entity.put()
		
		self.redirect('/admin/api', code=303)

app = webapp2.WSGIApplication([
	('/admin/?(\?.*)?', AdminPage),
	('/admin/api/?(\?.*)?', APIPage)
])
