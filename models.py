# -*- coding: utf-8 -*-

from google.appengine.api import search
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

from constants import MEMBER_SEARCH_INDEX_NAME
from dates import year_str, date_str, pretty_date
from semesters import get_current_semester

class Member(ndb.Model):
	id = ndb.StringProperty() # UUID
	show = ndb.BooleanProperty() # Show the user on the public site?
	name = ndb.StringProperty()
	dce = ndb.StringProperty() # None for people who were never RIT students
	mailing_list = ndb.BooleanProperty()
	current_student = ndb.BooleanProperty()
	email = ndb.StringProperty() # Member's preferred e-mail
	semesters_paid = ndb.FloatProperty(repeated=True)
	never_paid = ndb.ComputedProperty(lambda self: len(self.semesters_paid) == 0) # Thank you to bossylobster and wag2639 on StackOverflow.
	committee_rank = ndb.BooleanProperty()
	merit_rank1 = ndb.BooleanProperty()
	merit_rank2 = ndb.BooleanProperty()
	
	qr_code = ndb.BlobProperty()
	
	card_color = ndb.StringProperty()
	card_emblem = ndb.StringProperty()
	card_printed = ndb.BooleanProperty()
	
	def get_missions(self):
		return Mission.query(Mission.runners == self.id).order(Mission.start).fetch(limit=None)
	
	def get_rank(self, semester=get_current_semester()):
		from ranks import rank
		if not semester:
			semester = get_current_semester()
		return rank(self, semester)
	
	def get_rank_disp(self, semester=get_current_semester()):
		from ranks import rank_disp
		if not semester:
			semester = get_current_semester()
		return rank_disp(self, semester)

	def get_rank_name(self, semester=get_current_semester()):
		from ranks import rank_name
		if not semester:
			semester = get_current_semester()
		return rank_name(self, semester)

	def get_name_with_rank(self, semester=get_current_semester()):
		from ranks import name_with_rank
		if not semester:
			semester = get_current_semester()
		return name_with_rank(self, semester)

	def get_semesters_paid_pretty(self):
		semesters_pretty = []
		for semester in self.semesters_paid:
			i_part = int(semester)
			d_part = round((semester - i_part) * 10)
			semester_pretty = 'Spring ' if d_part == 1 else 'Fall '
			semester_pretty += `i_part`
			semesters_pretty.append(semester_pretty)
		return semesters_pretty
	
	def get_qr_code(self):
		url = 'http://ritstar.com/members/' + self.id
		qr = QRCode(QRCode.get_type_for_string(url * 2), QRErrorCorrectLevel.Q) # Pass URL * 2 to get a larger QR code.
		qr.addData(url)
		qr.make()
		
		return qr.make_image()
		#return 'data:image/png;base64,' + base64.b64encode(qr.make_image())
		#return 'data:image/svg+xml;base64,' + base64.b64encode(qr.make_svg())
	
	missions = property(get_missions)
	
	def _post_put_hook(self, future):
		# Generate the member's QR code if the member does not have one.
		if not self.qr_code:
			self.qr_code = self.get_qr_code()
			self.put()
		
		# Update the member's assosciated search document.
		fields = [
			search.TextField(name='name', value=self.name),
			search.AtomField(name='dce', value=self.dce),
			search.AtomField(name='email', value=self.email)
		]
		for semester in self.semesters_paid:
			fields.append(search.AtomField(name='semester', value=str(round(semester, 1))))
		
		doc = search.Document(doc_id=self.id, fields=fields)
		search.Index(name=MEMBER_SEARCH_INDEX_NAME).put(doc)


class BridgeCrew(ndb.Model):
	id = ndb.StringProperty()
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
	
	def get_start_str(self):
		return date_str(self.start)
	
	def get_end_str(self):
		return date_str(self.end)
	
	def get_year_str(self):
		return year_str(self.start.year, self.end.year)
	
	admiral_name = property(get_admiral_name)
	captain_name = property(get_captain_name)
	first_officer_name = property(get_first_officer_name)
	ops_name = property(get_ops_name)
	comms_name = property(get_comms_name)
	engi_name = property(get_engi_name)
	start_str = property(get_start_str)
	end_str = property(get_end_str)
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
	
	intro_url = ndb.StringProperty()
	pres_url = ndb.StringProperty()
	sign_in_url = ndb.StringProperty()
	
	fb_url = ndb.StringProperty()
	gplus_url = ndb.StringProperty()
	the_link_url = ndb.StringProperty()
	youtube_url = ndb.StringProperty()
	
	def get_start_str(self):
		return date_str(self.start)
	
	def get_end_str(self):
		return date_str(self.end)
	
	def get_pretty_date(self):
		return pretty_date(self.start, self.end)
	
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

class APIKey(ndb.Model):
	key = ndb.StringProperty()
	name = ndb.StringProperty()

class PageContent(ndb.Model):
	page = ndb.StringProperty()
	text = ndb.TextProperty()
	
	def get_html_text(self):
		return markdown(text=gfm(self.text), safe_mode='escape').replace('<a href="', '<a target="_blank" href="')
	
	html_text = property(get_html_text)
