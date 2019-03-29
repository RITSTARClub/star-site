# -*- coding: utf-8 -*-

from google.appengine.api import users

def require_admin(handler):
	if users.is_current_user_admin():
		return True
	else:
		handler.error(403)
		return False

def generate_base_template_vals(handler):
	return {
		'user': users.get_current_user(),
		'logout_url': users.create_logout_url(handler.request.uri),
		'login_url': users.create_login_url(handler.request.uri),
		'admin': users.is_current_user_admin()
	}

def generate_plain_404(handler, message=''):
	handler.error(404)
	handler.response.headers['Content-Type'] = 'text/plain; charset=utf-8'
	message = message.encode('utf-8')
	handler.response.write(message)
