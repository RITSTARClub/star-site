# -*- coding: utf-8 -*-

import json

from google.appengine.api import users
from google.appengine.ext import ndb

import webapp2

from models import APIKey, Member
from semesters import get_current_semester

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
		'show': member.show,
		'name': member.name,
		'dce': member.dce,
		'mailingList': member.mailing_list,
		'currentStudent': member.current_student,
		'email': member.email,
		'semestersPaid': member.semesters_paid,
		'missions': member.missions, # Only computed property, maybe not necessary?
		'committee_rank': member.committee_rank,
		'merit_rank1': member.merit_rank1,
		'merit_rank2': member.merit_rank2,
		'card_color': member.card_color,
		'card_emblem': member.card_emblem,
		'card_printed': member.card_printed
	}




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

class RankAPI(webapp2.RequestHandler):
	def get(self, rank_type):
		if not check_authentication(self):
			return

		id = self.request.get('id')

		if not id:
			# Error if no member specified.
			self.error(400)
			return

		member = Member.query(Member.id == id).get()
		if not member:
			# 404 if a nonexstient member is specified
			self.error(404)
			return

		semester = self.request.get('semester')

		if not rank_type:
			output = member.get_rank(semester)
		elif rank_type == 'name':
			output = member.get_rank_name(semester)
		elif rank_type == 'disp':
			output = member.get_rank_disp(semester)
		elif rank_type == 'with_name':
			output = member.get_name_with_rank(semester)
		else: 
			# 400 if no known rank type is passed
			self.error(404)
			return

		self.response.headers['Content-Type'] = 'application/json'
		self.response.write(json.dumps(output))

class APIFail(webapp2.RequestHandler):
	def get(self, args):
		# Just error out.
		self.error(404)

app = webapp2.WSGIApplication([
	('/api/members', MemberListAPI),
	('/api/member', MemberAPI),
	('/api/rank/?([a-zA-Z0-9_]+)?', RankAPI),
	('/api/?(\?.*)?', APIFail)
])
