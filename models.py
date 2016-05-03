#!/usr/bin/env python
# -○- coding: utf-8 -○-

from google.appengine.ext import ndb

# The Python Markdown implementation by Waylan Limberg
import markdown
# The GitHub-Flavored Markdown
import gfm


class Member(ndb.Model):
	RANKS = [
		{
			'name': 'Cadet', # 0
			'disp': ''
		}, {
			'name': 'Ensign', # 1
			'disp': unichr(9679) # ●
		}, {
			'name': 'Lieutenant, Junior Grade', # 2
			'disp': unichr(9675) + unichr(9679) # ○●
		}, {
			'name': 'Lieutenant', # 3
			'disp': unichr(9679) + unichr(9679) # ●●
		}, {
			'name': 'Lieutenant Commander', # 4
			'disp': unichr(9675) + unichr(9679) + unichr(9679) # ○●●
		}, {
			'name': 'Commander', # 5
			'disp': unichr(9679) + unichr(9679) + unichr(9679) # ●●●
		}, {
			'name': 'Captain', # 6
			'disp': unichr(9679) + unichr(9679) + unichr(9679) + unichr(9679) # ●●●●
		}, {
			'name': 'Commodore', # 7
			'disp': '[' + unichr(9679) + ']' # [●]
		}, {
			'name': 'Rear Admiral', # 8
			'disp': '[' + unichr(9679) + unichr(9679) + ']' # [●●]
		}, {
			'name': 'Vice Admiral', #9
			'disp': '[' + unichr(9679) + unichr(9679) + unichr(9679) + ']' # [●●●]
		}, {
			'name': 'Admiral', # 10
			'disp': '[' + unichr(9679) + unichr(9679) + unichr(9679) + unichr(9679) + ']' # [●●●●]
		}, {
			'name': 'Fleet Admiral', # 11
			'disp': '[' + unichr(9679) + unichr(9679) + unichr(9679) + unichr(9679) + unichr(9679) + ']' # [●●●●●]
		}
	]
	
	id = ndb.StringProperty() # UUID
	name = ndb.StringProperty()
	dce = ndb.StringProperty() # None for people who were never RIT students
	current_student = ndb.BooleanProperty()
	email = ndb.StringProperty() # Member's preferred e-mail
	semesters_paid = ndb.StringProperty(repeated=True)
	special_rank1 = ndb.BooleanProperty()
	special_rank2 = ndb.BooleanProperty()
	
	def get_missions(self):
		return Mission.query(Mission.runners == self.id).order(-Mission.date).fetch(limit=None)
	
	def get_rank(self):
		rank = 0
		if len(self.semesters_paid) == 0:
			return 0
		elif len(self.semesters_paid) >= 4: # Longevity
			rank = 2
		else:
			rank = 1
		
		if Mission.query(Mission.runners == self.id, Mission.type == Mission.TYPE_WEEKLY).count(limit=1) != 0: # Led weekly mission
			rank += 1
		
		if Mission.query(Mission.runners == self.id, Mission.type == Mission.TYPE_SPECIAL).count(limit=1) != 0: # Volunteered with special mission
			rank += 1
		
		if self.special_rank1:
			rank +=1
		if self.special_rank2:
			rank +=1
		
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
	
	missions = property(get_missions)
	rank = property(get_rank)
	rank_disp = property(get_rank_disp)
	rank_name = property(get_rank_name)


class BridgeCrew(ndb.Model):
	year = ndb.StringProperty() # The ○FALL○ semester the bridge crew started
	admiral = ndb.StringProperty() # Bridge crew member entries are member UUIDs
	captain = ndb.StringProperty()
	first_officer = ndb.StringProperty()
	ops = ndb.StringProperty()
	comms = ndb.StringProperty()
	engi = ndb.StringProperty()


class Mission(ndb.Model):
	TYPE_WEEKLY = 0
	TYPE_SPECIAL = 1
	TYPE_AWAY = 2
	
	id = ndb.StringProperty() # Mission number (or special identifier for non-standard mission)
	type = ndb.IntegerProperty()
	title = ndb.StringProperty()
	descripiton = ndb.TextProperty()
	start = ndb.DateTimeProperty()
	end = ndb.DateTimeProperty()
	location = ndb.StringProperty()
	runners = ndb.StringProperty(repeated=True) # Member UUIDs
