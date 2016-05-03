#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime


FIRST_YEAR = 2013
FALL_START_MONTH = 8

###
### Semesters are always formatted as semester_year (e.g., “fall_2013”, or “spring_2014”)
###

def is_fall():
	return datetime.now().month >= FALL_START_MONTH

def format_semester(semester, year):
	return '%s_%d' % (semester, year)

def get_current_semester():
	# Get the current month and year.
	now = datetime.now()
	
	# Treat August as the start of fall semester.
	semester = ('fall' if is_fall() else 'spring')
	
	# Return the formatted semester string, “semester_year”.
	return format_semester(semester, now.year)

def get_all_semesters():
	# Create the list of semesters.
	semesters = [format_semester('fall', FIRST_YEAR)]
	
	# Start at STAR's first year.
	year = FIRST_YEAR
	now = datetime.now()
	
	while year <= now.year:
		semesters.append(format_semester('spring', year))
		if year != now.year or is_fall():
			semesters.append(format_semester('fall', year))
		year += 1
	
	return semesters

def prev_semester(semester_str):
	if semester_str.count('fall') != 0:
		return semester_str.replace('fall', 'spring')
	else:
		year = int(semester_str.split('_')[1])
		year -= 1
		return format_semester('fall', year)

def next_semester(semester_str):
	if semester_str.count('spring') != 0:
		return semester_str.replace('spring', 'fall')
	else:
		year = int(semester_str.split('_')[1])
		year += 1
		return format_semester('spring', year)

def semester_date(semester_str):
	year = int(semester_str.split('_')[1])
	semester = semester_str.split('_')[0]
	month = (1 if semester == 'spring' else FALL_START_MONTH)
	
	return datetime(year, month, 1)
