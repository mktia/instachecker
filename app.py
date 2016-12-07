# -*- coding: utf-8 -*-
import json
import os
import pycurl
import urllib
import urllib2
from flask import Flask, render_template, request, session, redirect, url_for
from StringIO import StringIO

app = Flask(__name__)

setting = {
	'url' : 'https://instachecker.herokuapp.com',
	'name' : 'InstaChecker',
	'description' : u'片思い・相互フォローを自動解析してアカウント管理を楽にするアプリ InstaChecker',
	'short_description' : u'片思い・相互フォローを自動でチェック'
}

app_url = setting['url']
app_redirect_url = app_url + '/result'
client_id = os.environ['client_id']
client_secret = os.environ['client_secret']
access_token = ''

base_url = 'https://api.instagram.com'
auth_url = '/oauth/authorize/?client_id=' + client_id + '&redirect_uri=' + app_redirect_url + '&response_type=code&scope=follower_list'

@app.route('/')
def auth():
	url = base_url + auth_url
	return render_template('index.html', url=url, info=setting)

@app.route('/result')
def exe():
	code = request.args.get('code')
	info = StringIO()
	curl = pycurl.Curl()
	curl.setopt(pycurl.URL, 'https://api.instagram.com/oauth/access_token')
	param = urllib.urlencode({
		'client_id':client_id,
		'client_secret':client_secret,
		'grant_type':'authorization_code',
		'redirect_uri':app_redirect_url,
		'code':code
	})
	curl.setopt(pycurl.POSTFIELDS, param)
	curl.setopt(curl.WRITEFUNCTION, info.write)
	curl.perform()
	res = info.getvalue()
	print res
	
	imgs = {}
	load = json.loads(res)
	access_token = load['access_token']
	
	try:
		follows = []
		api = urllib2.urlopen('https://api.instagram.com/v1/users/self/follows?access_token=' + access_token)
		load = json.loads(api.read())
		data = load['data']
		pagination = load['pagination']
		if(pagination != {}):
			next_url = pagination['next_url']
		for i in range(len(data)):
			follows.append(data[i]['username'])
			imgs[data[i]['username']] = data[i]['profile_picture']
	except Exception as e:
		print(e, 'error to get follows')
	while(True):
		if(pagination == {}):
			break
		else:
			api = urllib2.urlopen(next_url)
			load = json.loads(api.read())
			data = load['data']
			pagination = load['pagination']
			print pagination
			if(pagination != {}):
				next_url = pagination['next_url']
			for i in range(len(data)):
				follows.append(data[i]['username'])
				imgs[data[i]['username']] = data[i]['profile_picture']
	print follows
	
	try:
		followed_by = []
		api = urllib2.urlopen('https://api.instagram.com/v1/users/self/followed-by?access_token=' + access_token)
		load = json.loads(api.read())
		data = load['data']
		pagination = load['pagination']
		if(pagination != {}):
			next_url = pagination['next_url']
		for i in range(len(data)):
			followed_by.append(data[i]['username'])
			imgs[data[i]['username']] = data[i]['profile_picture']
	except Exception as e:
		print(e, 'error to get followed by')	
	while(True):
		if(pagination == {}):
			break
		else:
			api = urllib2.urlopen(next_url)
			load = json.loads(api.read())
			data = load['data']
			pagination = load['pagination']
			if(pagination != {}):
				next_url = pagination['next_url']
			for i in range(len(data)):
				followed_by.append(data[i]['username'])
			imgs[data[i]['username']] = data[i]['profile_picture']
	print followed_by
	
	num_follows = len(follows)
	num_followed_by = len(followed_by)
	
	print('Follows:' + str(num_follows) + ', Followers:' + str(num_followed_by))
	
	follows_and_followed = []
	not_follows = []
	not_followed_by = []
	img_follows_and_followed = []
	img_not_follows = []
	img_not_followed_by = []
	num_ff = 0
	num_not_fd = 0
	num_not_fs = 0
	
	for i in range(num_follows):
		for j in range(num_followed_by):
			if follows[i] == followed_by[j]:
				follows_and_followed.append(follows[i])
				tmp_img = imgs[follows[i]]
				img_follows_and_followed.append(tmp_img)
				break
		else:
			not_followed_by.append(follows[i])
			tmp_img = imgs[follows[i]]
			img_not_followed_by.append(tmp_img)
	num_ff = len(follows_and_followed)
	num_not_fd = len(not_followed_by)
	if num_not_fd != 0:
		for i in not_followed_by:
			print("You aren't followed by: " + i)
	else:
		print('You are followed by all the user you follow.')
	
	for i in range(num_followed_by):
		for j in range(num_follows):
			if followed_by[i] == follows[j]:
				break
		else:
			not_follows.append(followed_by[i])
			tmp_img = imgs[followed_by[i]]
			img_not_follows.append(tmp_img)
	num_not_fs = len(not_follows)
	if num_not_fs != 0:
		for i in not_follows:		
			print("You don't follow: " + i)
	else:
		print('You are followed by all the user you follow.')
		
	return render_template('result.html', img_ff=img_follows_and_followed, img_not_fd=img_not_followed_by, img_not_fs=img_not_follows, ff=follows_and_followed, not_fd=not_followed_by, not_fs=not_follows, num_ff=num_ff, num_not_fs=num_not_fs, num_not_fd=num_not_fd, info=setting)

@app.route('/logout')
def restart():
	redirect('https://www.instagram.com/accounts/logout')
	url = base_url + auth_url
	return render_template('index.html', url=url, info=setting)

@app.route('/privacy')
def privacy():
	return render_template('privacy.html', info=setting)
	
@app.route('/contact')
def contact():
	return render_template('contact.html', info=setting)
	
if __name__ == '__main__':
	app.run()