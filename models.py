#!/usr/bin/env python
# -○- coding: utf-8 -○-

from google.appengine.ext import ndb

# The Python Markdown implementation by Waylan Limberg
from markdown import markdown
# The GitHub-Flavored Markdown
from gfm import gfm


class Member(ndb.Model):
	RANKS = [
		{
			'name': 'Cadet', # 0
			'abbr': 'Cdt.',
			'disp': ''
		}, {
			'name': 'Ensign', # 1
			'abbr': 'Ens.',
			'disp': unichr(9679) # ●
		}, {
			'name': 'Lieutenant, Junior Grade', # 2
			'abbr': 'Lt.',
			'disp': unichr(9675) + unichr(9679) # ○●
		}, {
			'name': 'Lieutenant', # 3
			'abbr': 'Lt.',
			'disp': unichr(9679) + unichr(9679) # ●●
		}, {
			'name': 'Lieutenant Commander', # 4
			'abbr': 'Lt. Cmdr.',
			'disp': unichr(9675) + unichr(9679) + unichr(9679) # ○●●
		}, {
			'name': 'Commander', # 5
			'abbr': 'Cmdr.',
			'disp': unichr(9679) + unichr(9679) + unichr(9679) # ●●●
		}, {
			'name': 'Captain', # 6
			'abbr': 'Capt.',
			'disp': unichr(9679) + unichr(9679) + unichr(9679) + unichr(9679) # ●●●●
		}, {
			'name': 'Commodore', # 7
			'abbr': 'Cmdre.',
			'disp': '[' + unichr(9679) + ']' # [●]
		}, {
			'name': 'Rear Admiral', # 8
			'abbr': 'Adm.',
			'disp': '[' + unichr(9679) + unichr(9679) + ']' # [●●]
		}, {
			'name': 'Vice Admiral', #9
			'abbr': 'Adm.',
			'disp': '[' + unichr(9679) + unichr(9679) + unichr(9679) + ']' # [●●●]
		}, {
			'name': 'Admiral', # 10
			'abbr': 'Adm.',
			'disp': '[' + unichr(9679) + unichr(9679) + unichr(9679) + unichr(9679) + ']' # [●●●●]
		}, {
			'name': 'Fleet Admiral', # 11
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
	committee_rank = ndb.BooleanProperty()
	merit_rank1 = ndb.BooleanProperty()
	merit_rank2 = ndb.BooleanProperty()
	
	def get_missions(self):
		return Mission.query(Mission.runners == self.id).order(-Mission.date).fetch(limit=None)
	
	def get_rank(self):
		if len(self.semesters_paid) == 0: # Cadets cannot earn ranks
			return 0
		
		rank = 1
		
		if len(self.semesters_paid) >= 4: # Longevity
			rank += 1
		
		if Mission.query(Mission.runners == self.id, Mission.type == 0).count(limit=1) != 0: # Led weekly mission
			rank += 1
		
		if self.committee_rank or Mission.query(Mission.runners == self.id, Mission.type == 1).count(limit=1) != 0: # Volunteered with special mission
			rank += 1
		
		if self.merit_rank1:
			rank += 1
		if self.merit_rank2:
			rank += 1
		
		if not self.current_student:
			if rank == 6: # Captains become rear admirals
				rank = 8
			else: # Non-captains become commodores
				rank = 7
		
		if BridgeCrew.query(BridgeCrew.admiral == self.id).count(limit=1) != 0:
			rank = 10
		
		return rank
	
	def get_rank_disp(self):
		return Member.RANKS[self.rank]['disp']
	
	def get_rank_name(self):
		return Member.RANKS[self.rank]['name']
	
	def get_name_with_rank(self):
		return Member.RANKS[self.rank]['abbr'] + ' ' + self.name
	
	missions = property(get_missions)
	rank = property(get_rank)
	rank_disp = property(get_rank_disp)
	rank_name = property(get_rank_name)
	name_with_rank = property(get_name_with_rank)


class BridgeCrew(ndb.Model):
	year = ndb.StringProperty() # The ○FALL○ semester the bridge crew started
	admiral = ndb.StringProperty() # Bridge crew member entries are member UUIDs
	captain = ndb.StringProperty()
	first_officer = ndb.StringProperty()
	ops = ndb.StringProperty()
	comms = ndb.StringProperty()
	engi = ndb.StringProperty()


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
	fb_url = ndb.StringProperty()
	gplus_url = ndb.StringProperty()
	
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
	
	def get_html_description(self):
		# Convert the description from Markdown to HTML.
		return markdown(text=gfm(self.description),safe_mode='escape').replace('<a href="', '<a target="_blank" href="')
	
	start_str = property(get_start_str)
	end_str = property(get_end_str)
	pretty_date = property(get_pretty_date)
	runners_str = property(get_runners_str)
	runners_list = property(get_runners_list)
	type_name = property(get_type_name)
	html_description = property(get_html_description)
