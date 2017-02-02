#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from google.appengine.ext import ndb

# The Python Markdown implementation by Waylan Limberg
from markdown import markdown
# The GitHub-Flavored Markdown
from gfm import gfm

import base64
import sys
# GAE Python QR code generator by Bernard Kobos
sys.path.append('PyQRNativeGAE')
from PyQRNative import QRErrorCorrectLevel
from PyQRNativeGAE import QRCode

from utils import get_current_semester, semester_date

def semester_to_num(semester_str):
	# spring = YEAR.1; false = YEAR.2
	return int(semester_str[-4:]) + (0.1 if semester_str[:7] == 'spring_' else 0.2 if semester_str[:5] == 'fall_' else 0.3)

class Member(ndb.Model):
	RANKS = [
		{
			# 0
			'name': 'Cadet',
			'abbr': 'Cdt.',
			'disp': ''
		}, {
			# 1
			'name': 'Ensign',
			'abbr': 'Ens.',
			'disp': unichr(9679) # ●
		}, {
			# 2
			'name': 'Lieutenant, Junior Grade',
			'abbr': 'Lt. J.G.',
			'disp': unichr(9675) + unichr(9679) # ○●
		}, {
			# 3
			'name': 'Lieutenant',
			'abbr': 'Lt.',
			'disp': unichr(9679) + unichr(9679) # ●●
		}, {
			# 4
			'name': 'Lieutenant Commander',
			'abbr': 'Lt. Cmdr.',
			'disp': unichr(9675) + unichr(9679) + unichr(9679) # ○●●
		}, {
			# 5
			'name': 'Commander',
			'abbr': 'Cmdr.',
			'disp': unichr(9679) + unichr(9679) + unichr(9679) # ●●●
		}, {
			# 6
			'name': 'Captain',
			'abbr': 'Capt.',
			'disp': unichr(9679) + unichr(9679) + unichr(9679) + unichr(9679) # ●●●●
		}, {
			# 7
			'name': 'Commodore',
			'abbr': 'Cmdre.',
			'disp': '[' + unichr(9679) + ']' # [●]
		}, {
			# 8
			'name': 'Rear Admiral',
			'abbr': 'Adm.',
			'disp': '[' + unichr(9679) + unichr(9679) + ']' # [●●]
		}, {
			# 9
			'name': 'Vice Admiral',
			'abbr': 'Adm.',
			'disp': '[' + unichr(9679) + unichr(9679) + unichr(9679) + ']' # [●●●]
		}, {
			# 10
			'name': 'Admiral',
			'abbr': 'Adm.',
			'disp': '[' + unichr(9679) + unichr(9679) + unichr(9679) + unichr(9679) + ']' # [●●●●]
		}, {
			# 11
			'name': 'Fleet Admiral',
			'abbr': 'Adm.',
			'disp': '[' + unichr(9679) + unichr(9679) + unichr(9679) + unichr(9679) + unichr(9679) + ']' # [●●●●●]
		}
	]
	
	id = ndb.StringProperty() # UUID
	show = ndb.BooleanProperty() # Show the user on the public site?
	name = ndb.StringProperty()
	dce = ndb.StringProperty() # None for people who were never RIT students
	mailing_list = ndb.BooleanProperty()
	current_student = ndb.BooleanProperty()
	email = ndb.StringProperty() # Member's preferred e-mail
	semesters_paid = ndb.StringProperty(repeated=True)
	never_paid = ndb.ComputedProperty(lambda self: len(self.semesters_paid) == 0) # Thank you to bossylobster and wag2639 on StackOverflow.
	committee_rank = ndb.BooleanProperty()
	merit_rank1 = ndb.BooleanProperty()
	merit_rank2 = ndb.BooleanProperty()
	
	card_color = ndb.StringProperty()
	card_emblem = ndb.StringProperty()
	card_printed = ndb.BooleanProperty()
	
	def get_missions(self):
		return Mission.query(Mission.runners == self.id).order(Mission.start).fetch(limit=None)
	
	def get_rank(self, semester=get_current_semester()):
		semester_num = semester_to_num(semester)
		num_semesters_paid_to_date = 0
		for semester_paid in map(semester_to_num, self.semesters_paid):
			if semester_paid < semester_num:
				num_semesters_paid_to_date += 1
		
		# Cadets cannot earn ranks
		if num_semesters_paid_to_date == 0:
			return 0
		
		rank = 1
		
		# Longevity
		if num_semesters_paid_to_date >= 4:
			rank += 1
		
		# Led weekly mission
		if Mission.query(Mission.runners == self.id, Mission.type == 0, Mission.start < semester_date(semester)).count(limit=1) != 0:
			rank += 1
		
		# Volunteered with special mission or committee
		if self.committee_rank or Mission.query(Mission.runners == self.id, Mission.type == 1, Mission.start < semester_date(semester)).count(limit=1) != 0:
			rank += 1
		
		# Merit ranks
		if self.merit_rank1:
			rank += 1
		if self.merit_rank2:
			rank += 1
		
		# Voted captain
		if BridgeCrew.query(BridgeCrew.captain == self.id, BridgeCrew.start < semester_date(semester)).count(limit=1) != 0:
			rank = 6
		
		# Alumni ranks
		if not self.current_student:
			if rank == 6:
				# Captains become rear admirals
				rank = 8
			else:
				# Non-captains become commodores
				rank = 7
		
		# Was an admiral (advisor)
		if BridgeCrew.query(BridgeCrew.admiral == self.id, BridgeCrew.start < semester_date(semester)).count(limit=1) != 0:
			rank = 10
		
		return rank
	
	def get_rank_disp(self, semester=get_current_semester()):
		return Member.RANKS[self.get_rank(semester)]['disp']
	
	def get_rank_name(self, semester=get_current_semester()):
		return Member.RANKS[self.get_rank(semester)]['name']
	
	def get_name_with_rank(self, semester=get_current_semester()):
		return Member.RANKS[self.get_rank(semester)]['abbr'] + ' ' + self.name
	
	def get_semesters_paid_pretty(self):
		return ((semester[0].upper() + semester[1:].replace('_', ' ')) for semester in self.semesters_paid)
	
	def get_qr_code(self):
		url = 'http://ritstar.com/members/' + self.id
		qr = QRCode(QRCode.get_type_for_string(url * 2), QRErrorCorrectLevel.Q) # Pass URL * 2 to get a larger QR code.
		qr.addData(url)
		qr.make()
		
		return 'data:image/png;base64,' + base64.b64encode(qr.make_image())
		#return 'data:image/svg+xml;base64,' + base64.b64encode(qr.make_svg())
	
	missions = property(get_missions)


class BridgeCrew(ndb.Model):
	start = ndb.DateTimeProperty()
	end = ndb.DateTimeProperty()
	admiral = ndb.StringProperty() # Bridge crew member entries are member UUIDs
	captain = ndb.StringProperty()
	first_officer = ndb.StringProperty()
	ops = ndb.StringProperty()
	comms = ndb.StringProperty()
	engi = ndb.StringProperty()
	
	def get_admiral_name(self):
		admiral_member = Member.query(Member.id == self.admiral).get()
		return admiral_member.name
	
	def get_captain_name(self):
		captain_member = Member.query(Member.id == self.captain).get()
		return captain_member.name
	
	def get_first_officer_name(self):
		first_officer_member = Member.query(Member.id == self.first_officer).get()
		return first_officer_member.name
	
	def get_ops_name(self):
		ops_member = Member.query(Member.id == self.ops).get()
		return ops_member.name
	
	def get_comms_name(self):
		comms_member = Member.query(Member.id == self.comms).get()
		return comms_member.name
	
	def get_engi_name(self):
		engi_member = Member.query(Member.id == self.engi).get()
		return engi_member.name
	
	def get_year_str(self):
		if self.start.year == self.end.year:
			return str(self.start.year)
		else:
			return str(self.start.year) + '-' + str(self.end.year)
	
	admiral_name = property(get_admiral_name)
	captain_name = property(get_captain_name)
	first_officer_name = property(get_first_officer_name)
	ops_name = property(get_ops_name)
	comms_name = property(get_comms_name)
	engi_name = property(get_engi_name)
	year_str = property(get_year_str)

class Mission(ndb.Model):
	TYPES = [
		'Weekly', # 0
		'Special', # 1
		'Away', # 2
	]
	
	id = ndb.StringProperty() # Mission number (or special identifier for non-standard mission)
	type = ndb.IntegerProperty()
	title = ndb.StringProperty()
	description = ndb.TextProperty()
	start = ndb.DateTimeProperty()
	end = ndb.DateTimeProperty()
	location = ndb.StringProperty()
	runners = ndb.StringProperty(repeated=True) # Member UUIDs
	wave_url = ndb.StringProperty()
	drive_url = ndb.StringProperty()
	fb_url = ndb.StringProperty()
	gplus_url = ndb.StringProperty()
	the_link_url = ndb.StringProperty()
	youtube_url = ndb.StringProperty()
	
	def get_start_str(self):
		if self.start:
			return self.start.strftime('%Y-%m-%dT%H:%M')
		return ''
	
	def get_end_str(self):
		if self.end:
			return self.end.strftime('%Y-%m-%dT%H:%M')
		return ''
	
	def get_pretty_date(self):
		pretty_date = self.start.strftime('%B %d, %Y &middot; %I:%M %p')
		# Do not show the date twice for single-day events.
		if self.start.date() == self.end.date():
			pretty_date += self.end.strftime(' - %I:%M %p')
		else:
			pretty_date += self.end.strftime(' - %B %d, %Y &middot; %I:%M %p')
		return pretty_date
	
	def get_runners_str(self):
		return ','.join(self.runners)
	
	def get_runners_list(self):
		runners_list = []
		for runner_id in self.runners:
			runner = Member.query(Member.id == runner_id).get()
			if runner:
				runners_list.append(runner)
		return runners_list
	
	def get_type_name(self):
		return Mission.TYPES[self.type] + ' Mission'
	
	def get_youtube_embed_url(self):
		if not self.youtube_url:
			return None
		return self.youtube_url.replace('watch?v=', 'embed/').replace('playlist?list=', 'embed/videoseries?list=')
	
	def get_html_description(self):
		# Convert the description from Markdown to HTML.
		return markdown(text=gfm(self.description),safe_mode='escape').replace('<a href="', '<a target="_blank" href="')
	
	start_str = property(get_start_str)
	end_str = property(get_end_str)
	pretty_date = property(get_pretty_date)
	runners_str = property(get_runners_str)
	runners_list = property(get_runners_list)
	type_name = property(get_type_name)
	youtube_embed_url = property(get_youtube_embed_url)
	html_description = property(get_html_description)
