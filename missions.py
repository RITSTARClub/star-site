# -*- coding: utf-8 -*-

from datetime import datetime
import os
import urllib2
from uuid import uuid4

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

from models import Mission
from semesters import FIRST_SEMESTER, get_current_semester, get_all_semesters, prev_semester, next_semester, semester_date, semester_pretty
from utils import require_admin, generate_base_template_vals, generate_plain_404

JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates/')),
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)

class MissionListPage(webapp2.RequestHandler):
	def get(self, args):
		template_vals = generate_base_template_vals(self)
		template_vals['title'] = 'Missions'
		template_vals['page'] = 'missions'
		
		# Get all users from the given semester
		try:
			selected_semester = float(self.request.get('semester'))
		except Exception:
			selected_semester = get_current_semester()
		
		next_semester_date = semester_date(next_semester(selected_semester))
		selected_semester_date = semester_date(selected_semester)
		
		template_vals['missions'] = Mission.query(Mission.start >= semester_date(selected_semester), Mission.start < next_semester_date).order(Mission.start).fetch(limit=None)
		
		# Get all possible semesters to put in the menu.
		semesters = []
		for semester in get_all_semesters():
			semesters.append({
				'id': semester,
				'pretty': semester_pretty(semester),
				'selected': semester == selected_semester
			})
		template_vals['semesters'] = semesters
		template_vals['prev_semester'] = prev_semester(selected_semester) if selected_semester != FIRST_SEMESTER else None
		template_vals['next_semester'] = next_semester(selected_semester) if selected_semester != get_current_semester() else None
		
		template = JINJA_ENVIRONMENT.get_template('missions_list.html')
		self.response.write(template.render(template_vals))

class HiddenListPage(webapp2.RequestHandler):
	def get(self):
		if not require_admin(self):
			return
		
		template_vals = generate_base_template_vals(self)
		template_vals['title'] = 'Hidden Missions'
		template_vals['page'] = 'missions'
		
		template_vals['missions'] = Mission.query(ndb.OR(Mission.start == None)).order(Mission.id).fetch(limit=None)
		
		template = JINJA_ENVIRONMENT.get_template('missions_hidden.html')
		self.response.write(template.render(template_vals))

class MissionInfoPage(webapp2.RequestHandler):
	def get(self, req_id):
		if not req_id:
			# Redirect to the missions page if no mission is specified.
			self.redirect('/missions')
			return
		
		mission = Mission.query(Mission.id == req_id).get()
		if not mission:
			# 404 if a nonexistent mission is specified.
			self.error(404)
			return
		
		template_vals = generate_base_template_vals(self)
		template_vals['page'] = 'missions'
		
		template_vals['mission'] = mission
		template_vals['title'] = mission.title
		
		template = JINJA_ENVIRONMENT.get_template('mission_info.html')
		self.response.write(template.render(template_vals))

class MissionEditPage(webapp2.RequestHandler):
	def get(self, args):
		if not require_admin(self):
			return
		
		template_vals = generate_base_template_vals(self)
		template_vals['title'] = 'Edit Mission'
		template_vals['page'] = 'missions'
		
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
		if not require_admin(self):
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
		for str_param in ['title', 'description', 'location', 'wave_url', 'drive_url', 'intro_url', 'pres_url', 'sign_in_url', 'fb_url', 'gplus_url', 'the_link_url', 'youtube_url']:
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
		
		if not mission.start:
			self.redirect('/missions/hidden', code=303)
			return
		
		self.redirect('/missions/' + mission.id, code=303)

class MissionResourceRedirect(webapp2.RequestHandler):
	def get(self, req_id, resource_name):
		if not req_id:
			# Redirect to the missions page if no mission is specified.
			self.redirect('/missions')
			return
		
		mission = Mission.query(Mission.id == req_id).get()
		if mission:
			if resource_name == 'wave' and mission.wave_url:
				self.redirect(mission.wave_url.encode('utf-8'))
				return
				
			elif (resource_name == 'gdrive' or resource_name == 'drive') and mission.drive_url:
				self.redirect(mission.drive_url.encode('utf-8'))
				return
				
			elif resource_name == 'intro' and mission.intro_url:
				self.redirect(mission.intro_url.encode('utf-8'))
				return
				
			elif (resource_name == 'presentation' or resource_name == 'pres') and mission.pres_url:
				self.redirect(mission.pres_url.encode('utf-8'))
				return
				
			elif resource_name == 'signin' and mission.sign_in_url:
				self.redirect(mission.sign_in_url.encode('utf-8'))
				return
				
			elif (resource_name == 'facebook' or resource_name == 'fb') and mission.fb_url:
				self.redirect(mission.fb_url.encode('utf-8'))
				return
				
			elif (resource_name == 'gplus' or resource_name == 'google' or resource_name == 'google+' or resource_name == 'googleplus') and mission.gplus_url:
				self.redirect(mission.gplus_url.encode('utf-8'))
				return
				
			elif resource_name == 'thelink' and mission.the_link_url:
				self.redirect(mission.the_link_url.encode('utf-8'))
				return
				
			elif (resource_name == 'youtube' or resource_name == 'yt') and mission.youtube_url:
				self.redirect(mission.youtube_url.encode('utf-8'))
				return
			
		# If there was no mission found or a missing link for the redirect, show the error page.
		template_vals = generate_base_template_vals(self)
		template_vals['req_id'] = req_id
		template_vals['resource_name'] = resource_name
		template_vals['mission'] = mission
		template_vals['title'] = 'Oh no!'
		
		template = JINJA_ENVIRONMENT.get_template('mission_resource_error.html')
		self.response.write(template.render(template_vals))

app = webapp2.WSGIApplication([
	('/missions/?(\?.*)?', MissionListPage),
	('/missions/hidden/?', HiddenListPage),
	('/missions/edit/?(\?.*)?', MissionEditPage),
	('/missions/([a-z0-9\-]+)/?', MissionInfoPage),
	('/missions/([a-z0-9\-]+)/([a-z0-9]+)', MissionResourceRedirect)
])
