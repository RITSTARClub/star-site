# -*- coding: utf-8 -*-


def year_str(year_start, year_end):
	if year_start == year_end:
		return str(year_start)
	else:
		return str(year_start) + '-' + str(year_end)

def date_str(date=None):
	if date:
		return date.strftime('%Y-%m-%dT%H:%M')
	return ''

def pretty_date(date_start, date_end):
	pretty_date = date_start.strftime('%B %d, %Y &middot; %I:%M %p')
	
	# Do not show the date twice for single-day events.
	if date_start.date() == date_end.date():
		pretty_date += date_end.strftime(' - %I:%M %p')
	else:
		pretty_date += date_end.strftime(' - %B %d, %Y &middot; %I:%M %p')
	
	# Remove zero-padding from hours.
	pretty_date = pretty_date.replace(' 0', ' ')
	
	return pretty_date

def pretty_time(date):
	pretty_time = date.strftime('%I:%M %p')
	
	# Remove zero-padding from hours.
	pretty_time = pretty_time.lstrip('0')
	
	return pretty_time
