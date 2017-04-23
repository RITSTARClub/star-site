#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from google.appengine.ext import ndb

import webapp2

from models import Member

def format_member(member):
	return {
		'id': member.id,
		'name': member.name,
		'dce': member.dce,
		'mailingList': member.mailing_list,
		'currentStudent': member.current_student,
		'email': member.email
	}

class MemberListAPI(webapp2.RequestHandler):
	def get(self):
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
	('/api/members', MemberListAPI),
	('/api/member', MemberAPI),
	('/api/?(\?.*)?', APIFail)
])
