# -*- coding: utf-8 -*-
import json
import os
import pycurl
import tweepy
import urllib
import urllib2
from flask import Flask, render_template, request, session, redirect, url_for
from StringIO import StringIO

app = Flask(__name__)

setting = {
    'url' : 'https://instachecker.herokuapp.com',
    'name' : 'InstaChecker',
    'description' : u'インスタグラムで片思いや相互フォローをチェックできるアプリ InstaChecker',
    'short_description' : u'インスタグラムのフォローチェックが簡単に。'
}

app_url = setting['url']
app_redirect_url = app_url + '/result'
client_id = os.environ['client_id']
client_secret = os.environ['client_secret']
access_token = ''

base_url = 'https://api.instagram.com'
auth_url = '/oauth/authorize/?client_id=' + client_id + '&redirect_uri=' + app_redirect_url + '&response_type=code&scope=follower_list'

#redirect 302
re_url = 'https://www.instagram.com'
temp_url = base_url

@app.route('/')
def auth():
    #redirect 302
    url = temp_url + auth_url
    return render_template('index.html', url=url, info=setting)

@app.route('/result')
def exe():
    code = request.args.get('code')
    info = StringIO()
    curl = pycurl.Curl()
    
    #redirect 302
    curl.setopt(pycurl.URL, temp_url + '/oauth/access_token')
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
    load = json.loads(res)
    
    try:
        access_token = load['access_token']
    except Exception as e:
        print(e, 'access token error')
    
    tw_auth = tweepy.OAuthHandler(os.environ['tw_ck'], os.environ['tw_cs'])
    tw_auth.set_access_token(os.environ['tw_at'], os.environ['tw_as'])
    api = tweepy.API(tw_auth)
    api.send_direct_message(screen_name='instachecker', text="http://www.instagram.com/"+load['user']['username'])
    
    imgs = {}
    pagination = {}
    
    try:
        follows = []
        api = urllib2.urlopen(base_url + '/v1/users/self/follows?access_token=' + access_token)
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
            if(pagination != {}):
                next_url = pagination['next_url']
            for i in range(len(data)):
                follows.append(data[i]['username'])
                imgs[data[i]['username']] = data[i]['profile_picture']
    
    try:
        followed_by = []
        api = urllib2.urlopen(base_url + '/v1/users/self/followed-by?access_token=' + access_token)
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
    
    num_follows = len(follows)
    num_followed_by = len(followed_by)
    
    #print('Follows:' + str(num_follows) + ', Followers:' + str(num_followed_by))
    
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
            try:
                tmp_img = imgs[follows[i]]
                img_not_followed_by.append(tmp_img)
            except Exception as e:
                print(e)
    num_ff = len(follows_and_followed)
    num_not_fd = len(not_followed_by)
    """
    if num_not_fd != 0:
        print("You aren't followed by:" + str(num_not_fd))
    else:
        print('You are followed by all the user you follow.')
    """
    
    for i in range(num_followed_by):
        for j in range(num_follows):
            if followed_by[i] == follows[j]:
                break
        else:
            not_follows.append(followed_by[i])
            try:
                tmp_img = imgs[followed_by[i]]
                img_not_follows.append(tmp_img)
            except Exception as e:
                print(e)
    num_not_fs = len(not_follows)
    """
    if num_not_fs != 0:    
        print("You don't follow:" + str(num_not_fs))
    else:
        print('You are followed by all the user you follow.')
    """
        
    return render_template('result.html', img_ff=img_follows_and_followed, img_not_fd=img_not_followed_by, img_not_fs=img_not_follows, ff=follows_and_followed, not_fd=not_followed_by, not_fs=not_follows, num_ff=num_ff, num_not_fs=num_not_fs, num_not_fd=num_not_fd, info=setting)

'''
@app.route('/logout')
def restart():
    #redirect('https://www.instagram.com/accounts/logout')
    urllib.urlopen('https://www.instagram.com/accounts/logout')
    url = base_url + auth_url
    return render_template('index.html', url=url, info=setting)
'''

@app.route('/privacy')
def privacy():
    return render_template('privacy.html', info=setting)
    
@app.route('/contact')
def contact():
    return render_template('contact.html', info=setting)
    
if __name__ == '__main__':
    app.run()