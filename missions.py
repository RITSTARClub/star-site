#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import os
import urllib2
from uuid import uuid4

from google.appengine.api import users

import jinja2
import webapp2

from models import Mission
from utils import get_current_semester, get_all_semesters, prev_semester, next_semester, semester_date

JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates/')),
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)

class MissionListPage(webapp2.RequestHandler):
	def get(self, args):
		template_vals = {
			'title': 'Missions',
			'page': 'missions'
		}
		
		user = users.get_current_user()
		if user:
			template_vals['user'] = user
			template_vals['admin'] = users.is_current_user_admin()
			template_vals['logout_url'] = users.create_logout_url(self.request.uri)
		else:
			template_vals['login_url'] = users.create_login_url(self.request.uri)
		
		# Get all users from the given semester
		selected_semester = self.request.get('semester')
		if not selected_semester:
			selected_semester = get_current_semester()
		
		prev_semester_str = prev_semester(selected_semester)
		current_semester_str = get_current_semester()
		next_semester_str = next_semester(selected_semester)
		next_semester_date = semester_date(next_semester_str)
		selected_semester_date = semester_date(selected_semester)
		
		template_vals['missions'] = Mission.query(Mission.start >= selected_semester_date, Mission.start < next_semester_date).order(Mission.start).fetch(limit=None)
		
		# Get all possible semesters to put in the menu.
		semesters = []
		for semester in get_all_semesters():
			semester_pretty = semester[0].upper() + semester[1:].replace('_', ' ')
			semesters.append({
				'id': semester,
				'pretty': semester_pretty,
				'selected': semester == selected_semester
			})
		template_vals['semesters'] = semesters
		template_vals['prev_semester'] = prev_semester_str if selected_semester != 'fall_2013' else None
		template_vals['next_semester'] = next_semester_str if selected_semester != current_semester_str else None
		
		template = JINJA_ENVIRONMENT.get_template('mission_list.html')
		self.response.write(template.render(template_vals))

class MissionInfoPage(webapp2.RequestHandler):
	def get(self, req_id):
		template_vals = {
			'page': 'missions'
		}
		
		if not req_id:
			# Redirect to the missions page if no mission is specified.
			self.redirect('/missions')
			return
		
		mission = Mission.query(Mission.id == req_id).get()
		if not mission:
			# 404 if a nonexistent mission is specified
			self.error(404)
			return
		
		template_vals['mission'] = mission
		template_vals['title'] = mission.title
		
		# Get user data for the footer and admin controls.
		user = users.get_current_user()
		if user:
			template_vals['user'] = user
			template_vals['admin'] = users.is_current_user_admin()
			template_vals['logout_url'] = users.create_logout_url(self.request.uri)
		else:
			template_vals['login_url'] = users.create_login_url(self.request.uri)
		
		template = JINJA_ENVIRONMENT.get_template('mission_info.html')
		self.response.write(template.render(template_vals))

class MissionEditPage(webapp2.RequestHandler):
	def get(self, args):
		if not users.is_current_user_admin():
			self.error(403)
			return
		
		
		template_vals = {
			'title': 'Edit Mission',
			'page': 'missions'
		}
		template_vals['user'] = users.get_current_user()
		template_vals['logout_url'] = users.create_logout_url(self.request.uri)
		
		req_id = self.request.get('id')
		
		if not req_id:
			new_mission = Mission()
			new_mission.name = 'New Mission'
			template_vals['mission'] = new_mission
		else:
			mission = Mission.query(Mission.id == req_id).get()
			if mission:
				template_vals['mission'] = mission
			else:
				self.error(404)
				return
		
		template_vals['semesters'] = get_all_semesters()
		
		template = JINJA_ENVIRONMENT.get_template('mission_edit.html')
		self.response.write(template.render(template_vals))
		
	def post(self, args):
		if not users.is_current_user_admin():
			self.error(403)
			return
		
		req_id = self.request.get('id')
		if not req_id:
			self.error(422)
			return
		
		mission = Mission.query(Mission.id == req_id).get()
		if not mission:
			mission = Mission()
			req_id = req_id.strip().lower().replace(' ', '-')
			mission.id = req_id
		
		# Update int values.
		for int_param in ['type']:
			req_val = self.request.get(int_param)
			if req_val or req_val == 0:
				req_val = int(req_val)
				setattr(mission, int_param, req_val)
		
		# Update string values.
		for str_param in ['title', 'description', 'location', 'wave_url', 'fb_url', 'gplus_url', 'the_link_url', 'youtube_url']:
			req_val = self.request.get(str_param)
			if req_val or req_val == '':
				req_val = urllib2.unquote(req_val)
				req_val = req_val.strip()
				setattr(mission, str_param, req_val)
		
		# Update date values.
		for date_param in ['start', 'end']:
			req_val = self.request.get(date_param)
			if req_val:
				req_val = urllib2.unquote(req_val)
				req_val = datetime.strptime(req_val, '%Y-%m-%dT%H:%M')
				setattr(mission, date_param, req_val)
			else:
				setattr(mission, date_param, None)
		
		# Update array values.
		req_runners = self.request.get('runners')
		if req_runners:
			req_runners = req_runners.replace(' ','').split(',')
			mission.runners = req_runners
		else:
			mission.runners = []
		
		# Save the updated mission.
		mission.put()
		
		self.redirect('/missions/' + mission.id, code=303)

app = webapp2.WSGIApplication([
	('/missions(\?.*)?', MissionListPage),
	('/missions/edit(\?.*)?', MissionEditPage),
	('/missions/([a-z0-9\-]+)', MissionInfoPage)
])
