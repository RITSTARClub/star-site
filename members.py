#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import urllib2
from uuid import uuid4

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

from models import Member
from semesters import FIRST_SEMESTER, get_current_semester, get_all_semesters, prev_semester, next_semester, semester_pretty

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
		try:
			selected_semester = float(self.request.get('semester'))
		except Exception:
			selected_semester = get_current_semester()
		
		template_vals['members'] = Member.query(Member.show == True, Member.semesters_paid == selected_semester).order(Member.name).fetch(limit=None)
		
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
		template_vals['selected_semester'] = selected_semester
		
		template = JINJA_ENVIRONMENT.get_template('members_list.html')
		self.response.write(template.render(template_vals))

class HiddenListPage(webapp2.RequestHandler):
	def get(self):
		if not users.is_current_user_admin():
			self.error(403)
			return
		
		template_vals = {
			'title': 'Hidden Users',
			'page': 'members'
		}
		
		user = users.get_current_user()
		if user:
			template_vals['user'] = user
			template_vals['admin'] = users.is_current_user_admin()
			template_vals['logout_url'] = users.create_logout_url(self.request.uri)
		else:
			template_vals['login_url'] = users.create_login_url(self.request.uri)
		
		template_vals['members'] = Member.query(ndb.OR(Member.show == False, Member.never_paid == True)).order(Member.name).fetch(limit=None)
		
		template_vals['current_semester'] = get_current_semester()
		
		template = JINJA_ENVIRONMENT.get_template('members_hidden.html')
		self.response.write(template.render(template_vals))

class EveryUserListPage(webapp2.RequestHandler):
	def get(self):
		if not users.is_current_user_admin():
			self.error(403)
			return
		
		template_vals = {
			'title': 'Every User Ever',
			'page': 'members'
		}
		
		user = users.get_current_user()
		if user:
			template_vals['user'] = user
			template_vals['admin'] = users.is_current_user_admin()
			template_vals['logout_url'] = users.create_logout_url(self.request.uri)
		else:
			template_vals['login_url'] = users.create_login_url(self.request.uri)
		
		template_vals['members'] = Member.query().order(Member.name).fetch(limit=None)
		
		template_vals['current_semester'] = get_current_semester()
		
		template = JINJA_ENVIRONMENT.get_template('members_hidden.html')
		self.response.write(template.render(template_vals))

class MailingList(webapp2.RequestHandler):
	def get(self):
		if not users.is_current_user_admin():
			self.error(403)
			return
		
		members = Member.query(Member.mailing_list == True).fetch(limit=None)
		mailing_list = []
		
		for member in members:
			if member.email:
				mailing_list.append(member.name + ' <' + member.email + '>')
			elif member.dce:
				mailing_list.append(member.name + ' <' + member.dce + '@rit.edu>')
		
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.write('; '.join(mailing_list))

class MemberInfoPage(webapp2.RequestHandler):
	def get(self, req_id):
		template_vals = {
			'page': 'members'
		}
		
		if not req_id:
			# Redirect to the members list if no member is specified.
			self.redirect('/members')
			return
		
		member = Member.query(Member.id == req_id).get()
		if not member:
			# 404 if a nonexistent member is specified.
			self.error(404)
			return
		
		template_vals['member'] = member
		template_vals['title'] = member.name
		
		# Get user data for the footer and admin controls.
		user = users.get_current_user()
		if user:
			template_vals['user'] = user
			template_vals['admin'] = users.is_current_user_admin()
			template_vals['logout_url'] = users.create_logout_url(self.request.uri)
		else:
			template_vals['login_url'] = users.create_login_url(self.request.uri)
		
		template = JINJA_ENVIRONMENT.get_template('member_info.html')
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
		for str_param in ['name', 'dce', 'email', 'card_color', 'card_emblem']:
			req_val = self.request.get(str_param)
			if req_val or req_val == '':
				req_val = req_val.strip()
				setattr(member, str_param, urllib2.unquote(req_val))
		
		# Update boolean values.
		for bool_param in ['show','mailing_list', 'current_student', 'committee_rank', 'merit_rank1', 'merit_rank2', 'card_printed']:
			req_val = self.request.get(bool_param)
			setattr(member, bool_param, not not req_val)
		
		# Update multi-select values.
		member.semesters_paid = [float(semester) for semester in self.request.get('semesters_paid', allow_multiple=True)]
		
		# Save the updated member.
		member.put()
		
		if member.never_paid:
			self.redirect('/members/hidden', code=303)
			return
		
		self.redirect('/members/' + member.id, code=303)

app = webapp2.WSGIApplication([
	('/members/?(\?.*)?', MemberListPage),
	('/members/hidden/?', HiddenListPage),
	('/members/every/?', EveryUserListPage),
	('/members/mailinglist/?', MailingList),
	('/members/edit/?(\?.*)?', MemberEditPage),
	('/members/([a-z0-9]+)/?', MemberInfoPage)
])
