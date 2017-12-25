# -*- coding: utf-8 -*-
import json
import os
import pycurl
import urllib
import urllib2
from flask import Flask, render_template, request, session, redirect, url_for
from StringIO import StringIO

app = Flask(__name__)

# Basic URL, Web site name, and description which tell search engine
setting = {
    'url' : 'https://instachecker.herokuapp.com',
    'name' : 'InstaChecker',
    'description' : u'インスタグラムで片思いや相互フォローをチェックできるアプリ InstaChecker',
    'short_description' : u'インスタグラムのフォローチェックが簡単に。'
}

app_url = setting['url']
# Redirect URL after OAuth
app_redirect_url = app_url + '/result'

client_id = os.environ['client_id']
client_secret = os.environ['client_secret']
access_token = ''

base_url = 'https://api.instagram.com'
auth_url = '/oauth/authorize/?client_id=' + client_id + '&redirect_uri=' + app_redirect_url + '&response_type=code&scope=follower_list'

url = base_url + auth_url

@app.route('/')
def top():
    setting['description'] = u'インスタグラムで片思いや相互フォローをチェックできるアプリ InstaChecker'
    setting['short_description'] = u'インスタグラムのフォローチェックが簡単に。'
    return render_template('index.html', url=url, info=setting, lang='')

@app.route('/id')
def top_id():
    setting['description'] = 'cara yang untuk melihat siapa yang tidak memfollow kamu atau yang unfollowers kamu'
    setting['short_description'] = 'cara yang untuk melihat siapa yang tidak memfollow kamu atau yang unfollowers kamu'
    return render_template('index_id.html', url=url, info=setting, lang='/id')

@app.route('/result')
def exe():
    # Authentication with OAuth
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
    load = json.loads(res)

    try:
        if(load['error_type'] == 'OAuthException'):
            return(redirect(app_url))
    except Exception as e:
        # It's not error
        pass

    #access token 取得失敗
    try:
        access_token = load['access_token']
    except Exception as e:
        print(e, 'error (access_token)')

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

    result = {
        'fs_and_fd' : {'num' : 0, 'name' : [], 'img' : []},
        'not_fs' : {'num' : 0, 'name' : [], 'img' : []},
        'not_fd' : {'num' : 0, 'name' : [], 'img' : []},
    }

    #相互をフォローユーザー、被フォローユーザーリストから除いた片思い、片思われリスト
    checked_follows = follows
    checked_followed_by = followed_by

    #ffチェック
    for fs in follows:
        for fd in followed_by:
            if fs == fd:
                result['fs_and_fd']['name'].append(fs)
                try:
                    result['fs_and_fd']['img'].append(imgs[fs])
                except Exception as e:
                    print(e, fs_and_fd)
                break

    for ff in result['fs_and_fd']['name']:
        checked_follows.remove(ff)
        checked_followed_by.remove(ff)

    #片思いの処理
    result['not_fd']['name'] = checked_follows
    for cfs in checked_follows:
        try:
            result['not_fd']['img'].append(imgs[cfs])
        except Exception as e:
            print(e, 'not_fd error')

    #片思われの処理
    result['not_fs']['name'] = checked_followed_by
    for cfd in checked_followed_by:
        try:
            result['not_fs']['img'].append(imgs[cfd])
        except Exception as e:
            print(e, 'not_fs error')

    result['fs_and_fd']['num'] = len(result['fs_and_fd']['name'])
    result['not_fd']['num'] = len(result['not_fd']['name'])
    result['not_fs']['num'] = len(result['not_fs']['name'])

    return render_template('result.html', result=result, info=setting)

@app.route('/logout')
def restart():
    urllib2.urlopen('https://www.instagram.com/accounts/logout')
    return redirect(app_url)

@app.route('/privacy')
def privacy():
    return render_template('privacy.html', info=setting)

@app.route('/contact')
def contact():
    return render_template('contact.html', info=setting)

if __name__ == '__main__':
    app.run()
