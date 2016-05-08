#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import urllib2
from uuid import uuid4

from google.appengine.api import users

import jinja2
import webapp2

from models import Member
from utils import get_current_semester, get_all_semesters, prev_semester, next_semester

JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates/')),
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)

class MemberListPage(webapp2.RequestHandler):
	def get(self, args):
		template_vals = {
			'title': 'Members',
			'page': 'members'
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
		
		template_vals['members'] = Member.query(Member.show == True, Member.semesters_paid == selected_semester).order(Member.name).fetch(limit=None)
		
		# Get all possible semesters to put in the menu.
		semesters = []
		for semester in get_all_semesters():
			semester_pretty = semester.capitalize().replace('_', ' ')
			semesters.append({
				'id': semester,
				'pretty': semester_pretty,
				'selected': semester == selected_semester
			})
		template_vals['semesters'] = semesters
		template_vals['prev_semester'] = prev_semester_str if selected_semester != 'fall_2013' else None
		template_vals['next_semester'] = next_semester_str if selected_semester != current_semester_str else None
		
		template = JINJA_ENVIRONMENT.get_template('member_list.html')
		self.response.write(template.render(template_vals))

class MemberEditPage(webapp2.RequestHandler):
	def get(self, args):
		if not users.is_current_user_admin():
			self.error(403)
			return
		
		
		template_vals = {
			'title': 'Edit Member',
			'page': 'members'
		}
		template_vals['user'] = users.get_current_user()
		template_vals['logout_url'] = users.create_logout_url(self.request.uri)
		
		req_id = self.request.get('id')
		
		if not req_id:
			while True:
				# Create a new ID and verify it is unique.
				new_id = uuid4().hex
				if not Member.query(Member.id == new_id).get():
					new_member = Member()
					new_member.id = new_id
					new_member.name = 'New Member'
					template_vals['member'] = new_member
					break
		else:
			member = Member.query(Member.id == req_id).get()
			if member:
				template_vals['member'] = member
			else:
				self.error(404)
				return
		
		template_vals['semesters'] = get_all_semesters()
		
		template = JINJA_ENVIRONMENT.get_template('member_edit.html')
		self.response.write(template.render(template_vals))
	def post(self, args):
		if not users.is_current_user_admin():
			self.error(403)
			return
		
		req_id = self.request.get('id')
		if not req_id:
			self.error(422)
			return
		
		member = Member.query(Member.id == req_id).get()
		if not member:
			member = Member()
			member.id = req_id
		
		# Update string values.
		for str_param in ['name', 'dce', 'email']:
			req_val = self.request.get(str_param)
			if req_val or req_val == '':
				req_val = req_val.strip()
				setattr(member, str_param, urllib2.unquote(req_val))
		
		# Update boolean values.
		for bool_param in ['show','mailing_list', 'current_student', 'committee_rank', 'merit_rank1', 'merit_rank2']:
			req_val = self.request.get(bool_param)
			setattr(member, bool_param, not not req_val)
		
		# Update multi-select values.
		member.semesters_paid = self.request.get('semesters_paid', allow_multiple=True)
		
		# Save the updated member.
		member.put()
		
		self.get(args)

app = webapp2.WSGIApplication([
	('/members(\?.*)?', MemberListPage),
	('/members/edit(\?.*)?', MemberEditPage)
])
