# -*- coding: utf-8 -*-

import json
from uuid import uuid4

from google.appengine.api import users
from google.appengine.ext import ndb

import webapp2

from models import APIKey, Member

def check_authentication(handler):
	key = handler.request.get('key')
	if not key or not APIKey.query(APIKey.key == key).get():
		# Error out if no valid key.
		handler.error(401)
		return False
	return True

def format_member(member):
	return {
		'id': member.id,
		'name': member.name,
		'dce': member.dce,
		'mailingList': member.mailing_list,
		'currentStudent': member.current_student,
		'email': member.email,
		'semestersPaid': member.semesters_paid
	}

class APIKeyHandler(webapp2.RequestHandler):
	def get(self):
		if not users.get_current_user():
			self.error(401)
			return
		if not users.is_current_user_admin():
			self.error(403)
			return
		self.response.write('<html><head><title>STAR API Key Creator</title></head><body><form method="POST"><input type="text" name="name" /><button type="submit">Submit</button></form></body></html>')
	def post(self):
		name = self.request.get('name')
		if not name:
			self.error(400)
		
		while True:
			# Create a new ID and verify it is unique.
			new_key = uuid4().hex
			if not APIKey.query(APIKey.key == new_key).get():
				break
		
		new_entity = APIKey()
		new_entity.name = name
		new_entity.key = new_key
		new_entity.put()
		
		self.response.write('<html><head><title>STAR API Key Creator</title></head><body><strong>Name:</strong> ' + name + '<br /><strong>Key:</strong> ' + new_key + '</body></html>')

class MemberListAPI(webapp2.RequestHandler):
	def get(self):
		if not check_authentication(self):
			return
		
		# Get all users from the given semester
		selected_semester = self.request.get('semester')
		
		if selected_semester:
			members = Member.query(Member.show == True, Member.semesters_paid == selected_semester).order(Member.name).fetch(limit=None)
		else:
			members = Member.query(Member.show == True, Member.never_paid == False).order(Member.name).fetch(limit=None)
		
		output = []
		for member in members:
			output.append(format_member(member))
		
		self.response.headers['Content-Type'] = 'application/json'
		self.response.write(json.dumps(output))

class MemberAPI(webapp2.RequestHandler):
	def get(self):
		if not check_authentication(self):
			return
		
		id = self.request.get('id')
		
		if not id:
			# Error out if no member is specified.
			self.error(400)
			return
		
		member = Member.query(Member.id == id).get()
		if not member:
			# 404 if a nonexistent member is specified.
			self.error(404)
			return
		
		output = format_member(member)
		
		self.response.headers['Content-Type'] = 'application/json'
		self.response.write(json.dumps(output))

class APIFail(webapp2.RequestHandler):
	def get(self, args):
		# Just error out.
		self.error(404)

app = webapp2.WSGIApplication([
	('/api/key', APIKeyHandler),
	('/api/members', MemberListAPI),
	('/api/member', MemberAPI),
	('/api/?(\?.*)?', APIFail)
])
