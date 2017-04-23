# -*- coding: utf-8 -*-

import logging

from google.appengine.ext import deferred
from google.appengine.ext import ndb

import webapp2

import models_r4
import models_r5_1
import models_r5_2

def update_schema_task_part1(cursor=None, num_updated=0, batch_size=100):
	"""Scans each entity in the datastore and converts its string semesters to float semesters"""
	
	# Force ndb to use the new version of the model by reloading it.
	reload(models_r5_1)
	
	# Get all entities.
	query = models_r5_1.Member.query()
	members, next_cursor, more = query.fetch_page(batch_size, start_cursor=cursor)
	
	to_put = []
	for member in members:
		new_semesters = []
		for semester in member.semesters_paid:
			semester = semester.split('_')
			new_semester = int(semester[1]) + (0.1 if semester[0] == 'spring' else 0.2)
			new_semesters.append(new_semester)
		
		member.semesters_paid_new = new_semesters
		to_put.append(member)
	
	# Save the updated entities.
	if to_put:
		ndb.put_multi(to_put)
		num_updated += len(to_put)
		logging.info('update_schema_task_part1 put {} entities to Datastore for a total of {}'.format(len(to_put), num_updated))
	
	# If there are more entities, re-queue the task for the next page.
	if more:
		deferred.defer(update_schema_task_part1, cursor=next_cursor, num_updated=num_updated)
	else:
		logging.debug('update_schema_task_part1 complete with {0} updates!'.format(num_updated))


def update_schema_task_part2(cursor=None, num_updated=0, batch_size=100):
	"""Scans each entity in the datastore and copies its new semester field to its semester field"""
	
	# Force ndb to use the new version of the model by reloading it.
	reload(models_r5_2)
	
	# Get all entities.
	query = models_r5_2.Member.query()
	members, next_cursor, more = query.fetch_page(batch_size, start_cursor=cursor)
	
	to_put = []
	for member in members:
		new_semesters = []
		for semester in member.semesters_paid_new:
			new_semesters.append(semester)
		
		member.semesters_paid = new_semesters
		to_put.append(member)
	
	# Save the updated entities.
	if to_put:
		ndb.put_multi(to_put)
		num_updated += len(to_put)
		logging.info('update_schema_task_part2 put {} entities to Datastore for a total of {}'.format(len(to_put), num_updated))
	
	# If there are more entities, re-queue the task for the next page.
	if more:
		deferred.defer(update_schema_task_part2, cursor=next_cursor, num_updated=num_updated)
	else:
		logging.debug('update_schema_task_part2 complete with {0} updates!'.format(num_updated))


class UpdateSchemaHandler1(webapp2.RequestHandler):
	def get(self):
		deferred.defer(update_schema_task_part1)
		self.response.write('Schema update part 1 started.  Check the console. for task progress.')

class UpdateSchemaHandler2(webapp2.RequestHandler):
	def get(self):
		deferred.defer(update_schema_task_part2)
		self.response.write('Schema update part 2 started.  Check the console. for task progress.')

app = webapp2.WSGIApplication([
	('/updateschema1', UpdateSchemaHandler1),
	('/updateschema2', UpdateSchemaHandler2)
	('/admin/updateschema1', UpdateSchemaHandler1),
	('/admin/updateschema2', UpdateSchemaHandler2),
])
