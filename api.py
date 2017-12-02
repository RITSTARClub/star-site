# -*- coding: utf-8 -*-

import json

from google.appengine.api import users
from google.appengine.ext import ndb

import webapp2

from models import APIKey, Member, Mission
from semesters import get_current_semester, semester_date, next_semester

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
		'semesters_paid': member.semesters_paid,
		'mission_ids': member.mission_ids,
		'committee_rank': member.committee_rank,
		'merit_rank1': member.merit_rank1,
		'merit_rank2': member.merit_rank2,
		'card_color': member.card_color,
		'card_emblem': member.card_emblem,
		'card_printed': member.card_printed
	}

def format_mission(mission):
	return {
		'id': mission.id,
		'type': mission.type,
		'type_name': mission.type_name,
		'title': mission.title,
		'description': mission.description,
		'html_description': mission.html_description,
		'start': mission.start_str,
		'end': mission.end_str,
		'location': mission.location,
		'runners': mission.runners,
		'wave_url': mission.wave_url,
		'drive_url': mission.drive_url,
		'fb_url': mission.fb_url,
		'gplus_url': mission.gplus_url,
		'the_link_url': mission.the_link_url,
		'youtube_url': mission.youtube_url
	}



class MemberListAPI(webapp2.RequestHandler):
	def get(self):
		if not check_authentication(self):
			return
		
		# Get all users from the given semester
		selected_semester = self.request.get('semester')
		
		if selected_semester:
			# Avoid throwing error 500 if a bad semester string is supplied
			try:
				selected_semester = float(selected_semester)
			except ValueError:
				self.error(400)
				return
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

		selected_semester = self.request.get('semester')
		
		if not selected_semester:
			selected_semester = get_current_semester()
		else:
			# Avoid throwing error 500 if a bad semester string is supplied
			try:
				selected_semester = float(selected_semester)
			except ValueError:
				self.error(400)
				return
		
		if not rank_type:
			output = member.get_rank(selected_semester)
		elif rank_type == 'name':
			output = member.get_rank_name(selected_semester)
		elif rank_type == 'disp':
			output = member.get_rank_disp(selected_semester)
		elif rank_type == 'with_name':
			output = member.get_name_with_rank(selected_semester)
		else: 
			# 400 if no known rank type is passed
			self.error(404)
			return

		self.response.headers['Content-Type'] = 'application/json'
		self.response.write(json.dumps(output))

class MissionListAPI(webapp2.RequestHandler):
	def get(self):
		if not check_authentication(self):
			return
		
		selected_semester = self.request.get('semester')

		# Offer option to filter by a semester, but by default just send all missions
		if selected_semester:
			# Avoid throwing error 500 if a bad semester string is supplied
			try:
				selected_semester = float(selected_semester)
			except ValueError:
				self.error(400)
				return
			next_semester_date = semester_date(next_semester(selected_semester))
			selected_semester_date = semester_date(selected_semester)
			missions = Mission.query(Mission.start >= selected_semester_date, Mission.start < next_semester_date).fetch(limit=None)
		else:
			missions = Mission.query().fetch(limit=None)

		output = []
		for mission in missions:
			output.append(format_mission(mission))

		self.response.headers['Content-Type'] = 'application/json'
		self.response.write(json.dumps(output))

class MissionAPI(webapp2.RequestHandler):
	def get(self):
		if not check_authentication(self):
			return

		id = self.request.get('id')

		if not id:
			# Error if no mission specified
			self.error(400)
			return

		mission = Mission.query(Mission.id == id).get()

		if not mission:
			# Error if mission not found
			self.error(404)
			return

		output = format_mission(mission)

		self.response.headers['Content-Type'] = 'application/json'
		self.response.write(json.dumps(output))

class APIFail(webapp2.RequestHandler):
	def get(self, args):
		# Just error out.
		self.error(404)

app = webapp2.WSGIApplication([
	('/api/members/?', MemberListAPI),
	('/api/member/?', MemberAPI),
	('/api/rank/?([a-zA-Z0-9_]+)?', RankAPI),
	('/api/missions/?', MissionListAPI),
	('/api/mission/?', MissionAPI),
	('/api/?(\?.*)?', APIFail)
])
