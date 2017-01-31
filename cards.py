# -*- coding: utf-8 -*-

import os
import urllib2
from uuid import uuid4

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

from models import Member
from utils import get_current_semester, get_all_semesters, prev_semester, next_semester

JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates/')),
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)

class SingleCardPage(webapp2.RequestHandler):
	def get(self, id):
		member = Member.query(Member.id == id).get()
		
		if not member:
			# 404 if a nonexistent member is specified.
			self.response.write('Not found.')
			self.error(404)
			return
		
		# TODO: Replace with fetching the current semester once semester formatting functions are merged in.
		semester = 'Spring 2017'
		# Replace 0 with O because it looks better in the font.
		semester = semester.replace('0', 'O')
		
		template_vals = {
			'title': 'ID card for ' + member.name,
			'members': [member],
			'semester': semester
		}
		
		template = JINJA_ENVIRONMENT.get_template('cards.html')
		self.response.write(template.render(template_vals))


app = webapp2.WSGIApplication([
	('/cards/single/(.*)', SingleCardPage)
])
