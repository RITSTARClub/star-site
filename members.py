# -*- coding: utf-8 -*-

import os
import urllib2
from uuid import uuid4

from google.appengine.api import search
from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

from constants import MEMBER_SEARCH_INDEX_NAME
from models import Member
from semesters import FIRST_SEMESTER, get_current_semester, get_all_semesters, get_semester_from_query, prev_semester, next_semester, semester_pretty
from utils import require_admin, generate_base_template_vals

JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates/')),
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)

class MemberListPage(webapp2.RequestHandler):
	def get(self, args):
		template_vals = generate_base_template_vals(self)
		template_vals['title'] = 'Members'
		template_vals['page'] = 'members'
		
		# Check for a search query.
		search_query = self.request.get('q')
		
		# If there was no search or semester specified, default to the current semester.
		if not search_query:
			search_query = 'semester:' + str(get_current_semester())
		
		# Run the search.
		search_results = search.Index(MEMBER_SEARCH_INDEX_NAME).search(search.Query(
				query_string=search_query,
				options=search.QueryOptions(
					limit=999,
					ids_only=True,
					sort_options=search.SortOptions(
						expressions=[
							search.SortExpression(
								expression='name',
								direction=search.SortExpression.ASCENDING, 
								default_value='')
						]))))
		
		# Fetch the members.
		show_private = users.is_current_user_admin()
		members = []
		for result in search_results.results:
			member = Member.query(Member.id == result._doc_id).get()
			if member and (member.show or show_private):
				members.append(member)
		
		template_vals['members'] = members
		
		# Get all possible semesters to put in the menu.
		selected_semester = get_semester_from_query(search_query)
		
		semesters = []
		for semester in get_all_semesters():
			semesters.append({
				'id': semester,
				'pretty': semester_pretty(semester),
				'selected': semester == selected_semester
			})
		template_vals['semesters'] = semesters
		if selected_semester and selected_semester > FIRST_SEMESTER:
			template_vals['prev_semester'] = prev_semester(selected_semester)
		if selected_semester and selected_semester < get_current_semester():
			template_vals['next_semester'] = next_semester(selected_semester)
		if selected_semester and selected_semester >= FIRST_SEMESTER and selected_semester <= get_current_semester():
			template_vals['selected_semester'] = selected_semester
		
		template = JINJA_ENVIRONMENT.get_template('members_list.html')
		self.response.write(template.render(template_vals))

class HiddenListPage(webapp2.RequestHandler):
	def get(self):
		if not require_admin(self):
			return
		
		template_vals = generate_base_template_vals(self)
		template_vals['title'] = 'Hidden Users'
		template_vals['page'] = 'members'
		
		template_vals['members'] = Member.query(ndb.OR(Member.show == False, Member.never_paid == True)).order(Member.name).fetch(limit=None)
		
		template_vals['current_semester'] = get_current_semester()
		
		template = JINJA_ENVIRONMENT.get_template('members_hidden.html')
		self.response.write(template.render(template_vals))

class EveryUserListPage(webapp2.RequestHandler):
	def get(self):
		if not require_admin(self):
			return
		
		template_vals = generate_base_template_vals(self)
		template_vals['title'] = 'Every User Ever'
		template_vals['page'] = 'members'
		
		template_vals['members'] = Member.query().order(Member.name).fetch(limit=None)
		
		template_vals['current_semester'] = get_current_semester()
		
		template = JINJA_ENVIRONMENT.get_template('members_hidden.html')
		self.response.write(template.render(template_vals))

class MailingList(webapp2.RequestHandler):
	def get(self):
		if not require_admin(self):
			return
		
		members = Member.query(Member.mailing_list == True).fetch(limit=None)
		mailing_list = []
		
		for index, member in enumerate(members):
			if (index + 1) % 100 == 0:
				mailing_list.append('\n')
			if member.email:
				mailing_list.append(member.name + ' <' + member.email + '>')
			elif member.dce:
				mailing_list.append(member.name + ' <' + member.dce + '@rit.edu>')
		
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.write('; '.join(mailing_list))

class MemberInfoPage(webapp2.RequestHandler):
	def get(self, req_id):
		if not req_id:
			# Redirect to the members list if no member is specified.
			self.redirect('/members')
			return
		
		member = Member.query(Member.id == req_id).get()
		if not member:
			# 404 if a nonexistent member is specified.
			self.error(404)
			return
		
		template_vals = generate_base_template_vals(self)
		template_vals['page'] = 'members'
		
		template_vals['member'] = member
		template_vals['title'] = member.name
		
		template = JINJA_ENVIRONMENT.get_template('member_info.html')
		self.response.write(template.render(template_vals))

class MemberEditPage(webapp2.RequestHandler):
	def get(self, args):
		if not require_admin(self):
			return
		
		template_vals = generate_base_template_vals(self)
		template_vals['title'] = 'Edit Member'
		template_vals['page'] = 'members'
		
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
		if not require_admin(self):
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
