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

#検索エンジンに通知するドメイン、サイト名、説明文
setting = {
    'url' : 'https://instachecker.herokuapp.com',
    'name' : 'InstaChecker',
    'description' : u'インスタグラムで片思いや相互フォローをチェックできるアプリ InstaChecker',
    'short_description' : u'インスタグラムのフォローチェックが簡単に。'
}

app_url = setting['url']
app_redirect_url = app_url + '/result'　#OAuth 後のリダイレクト先
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
    #OAuth による認証
    code = request.args.get('code')
    info = StringIO()
    curl = pycurl.Curl()
    
    curl.setopt(pycurl.URL, base_url + '/oauth/access_token')
    param = urllib.urlencode({
        'client_id' : client_id,
        'client_secret' : client_secret,
        'grant_type' : 'authorization_code',
        'redirect_uri' : app_redirect_url,
        'code':code
    })
    curl.setopt(pycurl.POSTFIELDS, param)
    curl.setopt(curl.WRITEFUNCTION, info.write)
    curl.perform()
    res = info.getvalue()
    print res
    load = json.loads(res)
    
    try:
        if(load['error_type'] == 'OAuthException'):
            return(redirect(app_url))
    except Exception as e:
        print(Exception, e, 'error (OAuthException)')
    
    #access token 取得失敗
    try:
        access_token = load['access_token']
    except Exception as e:
        print(e, 'error (access_token)')
    
    tw_auth = tweepy.OAuthHandler(os.environ['tw_ck'], os.environ['tw_cs'])
    tw_auth.set_access_token(os.environ['tw_at'], os.environ['tw_as'])
    api = tweepy.API(tw_auth)
    try:
        api.send_direct_message(screen_name='instachecker', text="http://www.instagram.com/"+load['user']['username'])
    except Exception as e:
        print(e, 'error (Twitter DM)')
    
    imgs = {}
    pagination = {}
    
    #フォローしているアカウントを取得
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
    
    #フォローされているアカウントを取得
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
    
    result = {
        'fs_and_fd' : {'num' : 0, 'name' : [], 'img' : []},
        'not_fs' : {'num' : 0, 'name' : [], 'img' : []},
        'not_fd' : {'num' : 0, 'name' : [], 'img' : []},
    }
    
    """
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
        
    return render_template('result.html', img_ff=img_follows_and_followed, img_not_fd=img_not_followed_by, img_not_fs=img_not_follows, ff=follows_and_followed, not_fd=not_followed_by, not_fs=not_follows, num_ff=num_ff, num_not_fs=num_not_fs, num_not_fd=num_not_fd, info=setting)
    """
    
    for i in range(num_follows):
        for j in range(num_followed_by):
            if follows[i] == followed_by[j]:
                result['fs_and_fd']['name'].append(follows[i])
                try:
                    tmp_img = imgs[follows[i]]
                    result['fs_and_fd']['img'].append(tmp_img)
                except Exception as e:
                    print(e)
                break
        else:
            result['not_fd']['name'].append(follows[i])
            try:
                tmp_img = imgs[follows[i]]
                result['not_fd']['img'].append(tmp_img)
            except Exception as e:
                print(e)
    result['fs_and_fd']['num'] = len(result['fs_and_fd']['name'])
    result['not_fd']['num'] = len(result['not_fd']['name'])
    
    for i in range(num_followed_by):
        for j in range(num_follows):
            if followed_by[i] == follows[j]:
                break
        else:
            result['not_fs']['name'].append(followed_by[i])
            try:
                tmp_img = imgs[followed_by[i]]
                result['not_fs']['img'].append(tmp_img)
            except Exception as e:
                print(e)
    result['not_fs']['num'] = len(result['not_fs']['name'])
        
    return render_template('result.html', result=result, info=setting)
    
@app.route('/privacy')
def privacy():
    return render_template('privacy.html', info=setting)
    
@app.route('/contact')
def contact():
    return render_template('contact.html', info=setting)
    
if __name__ == '__main__':
    app.run()