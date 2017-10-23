# -*- coding: utf-8 -*-

import os

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

from models import PageContent
from utils import require_admin, generate_base_template_vals

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

app = webapp2.WSGIApplication([
	('/admin/?(\?.*)?', AdminPage)
])
