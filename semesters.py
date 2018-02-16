# -*- coding: utf-8 -*-

import re
from datetime import datetime


FIRST_YEAR = 2013
FIRST_SEMESTER = 2013.2
FALL_START_MONTH = 8

###
### Semesters are always formatted as year.semester (e.g., “2013.2”, or “2014.1”)
###

def is_fall_now():
	return datetime.now().month >= FALL_START_MONTH

def get_current_semester():
	# Get the current month and year.
	now = datetime.now()
	
	# Treat August as the start of fall semester.
	semester = now.year + (0.2 if is_fall_now() else 0.1)
	
	# Return the formatted semester number.
	return semester

def get_all_semesters():
	# Create the list of semesters.
	semesters = [FIRST_YEAR + 0.2]
	
	year = FIRST_YEAR + 1
	now = datetime.now()
	
	while year <= now.year:
		semesters.append(year + 0.1)
		if year != now.year or is_fall_now():
			semesters.append(year + 0.2)
		year += 1
	
	return semesters

def get_semester_from_query(query):
	match = re.search('\\bsemester:([0-9.]{6})\\b', query)
	if match:
		return float(match.group(1))
	else:
		return None

def prev_semester(semester):
	if round(semester - int(semester), 1) == 0.2:
		return semester - 0.1
	else:
		year = int(semester) - 1
		return year + 0.2

def next_semester(semester):
	if round(semester - int(semester), 1) == 0.1:
		return semester + 0.1
	else:
		year = int(semester) + 1
		return year + 0.1

def semester_date(semester):
	year = int(semester)
	semester = semester - year
	month = (1 if round(semester, 1) == 0.1 else FALL_START_MONTH)
	return datetime(year, month, 1)

def semester_pretty(semester):
	year = int(semester)
	semester_str = 'Spring' if round(semester - year, 1) == 0.1 else 'Fall'
	return semester_str + ' ' + `year`

def validate_semester(semester):
	try:
		semester = float(semester)
	# Don't accept anything that does not cast to a float.
	except ValueError: 
		return None

	# Reject semesters that are not in this milennium.
	if semester > 3000 or semester < 2000:
		return None

	# Reject semesters that are not Fall or Spring
	elif round(semester - int(semester), 1) not in [0.1, 0.2]:
		return None
	else: 
		return semester
