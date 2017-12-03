# -*- coding: utf-8 -*-

import json

from google.appengine.api import users
from google.appengine.ext import ndb

import webapp2

from models import APIKey, Member, Mission, BridgeCrew
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
		'mailing_list': member.mailing_list,
		'current_student': member.current_student,
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

def format_bridgecrew(crew):
	return {
		'yearStr': crew.year_str,
		'start': str(crew.start),
		'end': str(crew.end),
		'admiral': crew.admiral,
		'captain': crew.captain,
		'first_officer': crew.first_officer,
		'ops': crew.ops,
		'comms': crew.comms,
		'engi': crew.engi,
		'admiralName': crew.admiral_name,
		'captainName': crew.captain_name,
		'firstOfficerName': crew.first_officer_name,
		'opsName': crew.ops_name,
		'commsName': crew.comms_name,
		'engiName': crew.engi_name
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
		
		output = [format_member(member) for member in members]
		
		self.response.headers['Content-Type'] = 'application/json'
		self.response.write(json.dumps(output))

class MemberAPI(webapp2.RequestHandler):
	def get(self, id):
		if not check_authentication(self):
			return
		
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
	def get(self, rank_type, id):
		if not check_authentication(self):
			return

		member = Member.query(Member.id == id).get()
		if not member:
			# 404 if a nonexistent member is specified
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
		
		if rank_type == 'name':
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

		output = [format_mission(mission) for mission in missions]

		self.response.headers['Content-Type'] = 'application/json'
		self.response.write(json.dumps(output))

class MissionAPI(webapp2.RequestHandler):
	def get(self, id):
		if not check_authentication(self):
			return

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

class BridgeCrewListAPI(webapp2.RequestHandler):
	def get(self):
		if not check_authentication(self):
			return
		bridgecrews = BridgeCrew.query().fetch(limit=None)

		output = [format_bridgecrew(crew) for crew in bridgecrews]

		self.response.headers['Content-Type'] = 'application/json'
		self.response.write(json.dumps(output))

class BridgeCrewAPI(webapp2.RequestHandler):
	def get(self, crew):
		if not check_authentication(self):
			return

		# Only link latest bridge crew for now, don't see a reason to send anything besides the current one or all of them
		if crew == 'current':
			bridgecrew = BridgeCrew.query().order(-BridgeCrew.start).get()
		else:
			self.error(404)
			return

		output = format_bridgecrew(bridgecrew)

		self.response.headers['Content-Type'] = 'application/json'
		self.response.write(json.dumps(output))

class APIFail(webapp2.RequestHandler):
	def get(self, args):
		# Just error out.
		self.error(404)

app = webapp2.WSGIApplication([
	('/api/members/?', MemberListAPI),
	('/api/member/([a-z0-9]+)', MemberAPI),
	('/api/rank/([a-z_]+)/([a-zA-Z0-9]+)', RankAPI),
	('/api/missions/?', MissionListAPI),
	('/api/mission/([a-z0-9]+)', MissionAPI),
	('/api/bridgecrews/?', BridgeCrewListAPI),
	('/api/bridgecrew/([a-z0-9]+)?', BridgeCrewAPI),
	('/api/?(\?.*)?', APIFail)
])
