# -*- coding: utf-8 -*-

import os
import urllib2
from uuid import uuid4

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

from models import Member
from semesters import get_current_semester, semester_pretty, validate_semester

JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates/')),
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)


class QRCodePage(webapp2.RequestHandler):
	def get(self, id):
		member = Member.query(Member.id == id).get()
		
		if not member:
			# 404 if a nonexistent member is specified.
			self.error(404)
			return
		
		if not member.qr_code:
			member.qr_code = member.get_qr_code()
			member.put()
		
		self.response.headers['Content-Type'] = 'image/png'
		self.response.write(member.qr_code)

class SingleCardPage(webapp2.RequestHandler):
	def get(self, id):
		member = Member.query(Member.id == id).get()
		
		if not member:
			# 404 if a nonexistent member is specified.
			self.response.write('Not found.')
			self.error(404)
			return
		
		# Pick current semester by default, otherwise if there is a parameter in the request use that as a reference
		semester = validate_semester(self.request.get('semester'))
		if not semester:
			semester = get_current_semester()

		template_vals = {
			'title': 'ID card for ' + member.name,
			'members': [member],
			# Replace 0 with O because it looks better in the font
			'semester': semester_pretty(semester).replace('0', 'O')
		}
		
		template = JINJA_ENVIRONMENT.get_template('cards.html')
		self.response.write(template.render(template_vals))

class AllCardsPage(webapp2.RequestHandler):
	def get(self):
		# Pick current semester by default, otherwise if there is a parameter in the request use that as a reference
		semester = validate_semester(self.request.get('semester'))
		if not semester: 
			semester = get_current_semester()

		members = Member.query(Member.card_printed == False, Member.current_student == True, Member.semesters_paid == semester).order(Member.name).fetch(limit=None)

		template_vals = {
			'title': 'ID cards for ' + semester_pretty(semester),
			'members': members,
			# Replace 0 with O because it looks better in the font.
			'semester': semester_pretty(semester).replace('0', 'O')
		}
		
		template = JINJA_ENVIRONMENT.get_template('cards.html')
		self.response.write(template.render(template_vals))

app = webapp2.WSGIApplication([
	('/cards/qrcode/([a-z0-9]+)\.png', QRCodePage),
	('/cards/single/([a-z0-9]+)/?', SingleCardPage),
	('/cards/all/?', AllCardsPage)
])
