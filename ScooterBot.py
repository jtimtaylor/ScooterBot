# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

from bs4 import BeautifulSoup
import requests
import pickle
import sys
import smtplib
import ConfigParser
import os
from email import Charset

Charset.add_charset('utf-8', Charset.QP, Charset.QP, 'utf-8')
sys.setrecursionlimit(10000)

def get_config():
    config = ConfigParser.ConfigParser()
    config_file = '{}.cnf'.format(BOT_TYPE)

    with open(os.path.join(os.getcwd(),config_file),'r') as configfile:
        config.readfp(configfile)

        USERNAME = config.get('auth','user')
        PASSWORD = config.get('auth','password')
        MAILTO = config.get('auth','mailto').split(',')
        RSS = config.get('auth','rss')
        return USERNAME,PASSWORD,MAILTO,RSS

BOT_TYPE = 'ScooterBot'
USERNAME,PASSWORD,MAILTO,RSS = get_config()

def get_links(url):
    xml = requests.get(url)
    soup = BeautifulSoup(xml.text)
    links = [item['rdf:resource'] for item in soup.find_all('rdf:li')]
    return links

def save_postings(postings_dict):
    with open('{}.p'.format(BOT_TYPE),'wb') as save_file:
         pickle.dump(postings_dict, save_file)
    print "Save complete."
    
def open_postings():
    try:
        with open('{}.p'.format(BOT_TYPE),'r') as save_file:
            postings_dict = pickle.load(save_file)
    except:
        postings_dict = {}
    return postings_dict

class Posting():
    def __init__(self, url):
        self.url = url
        page = self.get_soup(url)
        self.soup = page
        self.title = page.h2.text
        frag = self.title.split('-')
        title = frag[0]
        self.cute_title = ''.join([i if ord(i) < 128 else ' ' for i in title])
        self.price = frag[1].split()[0]
        #self.coords = (page.find(id='map')['data-latitude'], page.find(id='map')['data-longitude'])
        #self.neighborhood = self.title.split('(')[1][:-2]
        #self.short_address = self.get_short_address(page)
        #attrs_get = page.find('p', {'class' : 'attrgroup'}).find_all('span')
        #self.attrs = [x.text for x in attrs_get]
        #self.bdba = self.attrs[0]
        #self.other_attrs = self.attrs[1:]
        self.body = page.find(id='postingbody')
        get_info = [x.text for x in page.find('div', {'class' : 'postinginfos'}).find_all('p')]
        self.post_id, self.post_time = [x.split(': ')[1] for x in get_info[:2]]
        if get_info[2]:
            self.update_time = get_info[2]
        self.img = page.find('img', {'id':'iwi'})
            
    def get_soup(self,url):
        page = requests.get(url)
        soup = BeautifulSoup(page.text)
        return soup
    
    def get_short_address(self,page):
        if page.find('div', {'class':'mapaddress'}) == None:
            return '[Unavailable]'
        else:
            return page.find('div', {'class':'mapaddress'}).text
        
def check_postings(rss):
    new_post_list = []
    print "Fetching links..."
    links = get_links(rss)
    print "Retrieving save file..."
    postings_dict = open_postings()
    for link in links:
        new_post = Posting(link)
        if link not in postings_dict or new_post.title not in [x.title for x in postings_dict.values()]:
            postings_dict[link] = new_post
            new_post_list.append(new_post)
            print u"New entry: {}".format(new_post.cute_title)
    if not len(new_post_list):
        print "No new entries."
    else:
        mail_results(new_post_list)
    print "Writing save file..."
    save_postings(postings_dict)
    print "File saved..."
    print "Process complete"
    
def mail_results(new_post_list):
    if len(new_post_list) > 1:
        subject = u'{} found new listings!'.format(BOT_TYPE)
        lead = u'{} found the following new posts:'.format(BOT_TYPE)
    else:
        subject = u'{} found a new listing!'.format(BOT_TYPE)
        lead = u'{} found the following new post:'.format(BOT_TYPE)
    
    msg = '<body>'+lead+'<br><br>'
    
    for post in new_post_list:
        
        listing_content = u'''<h3><b>{0}</b></h3>
        {1}<br><br>
        <h5><a href={2}>Link to post</a></h5><br><br>
        '''.format(post.title,
               post.img,
               post.url)
        msg += listing_content
    
    msg += '<br><br><br>Love,<br><h4><i>{}</i></h4></body>'.format(BOT_TYPE)
    
    msg = msg.encode('utf-8')
    
    #### Sending via Gmail ####
    session = smtplib.SMTP(u'smtp.gmail.com',587)
    session.ehlo()
    session.starttls()
    session.login(USERNAME,PASSWORD)
    headers = u'\r\n'.join([u'from: ' + USERNAME,
                           u'subject: ' + subject,
                           u'to: ' + ','.join(MAILTO),
                           u'mime-version: 1.0',
                           u'content-type: text/html'])
    
    #headers = headers
    content = headers + u'\r\n\r\n' + msg
    #content = content.decode('utf-8')
    session.sendmail(USERNAME,MAILTO,content)
    print 'Mail sent!'

# <codecell>

check_postings(RSS)

# <codecell>


