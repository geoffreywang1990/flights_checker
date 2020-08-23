#!/usr/bin/python3

import requests
#import streamlit as st
import bs4
from lxml import html
from bs4 import BeautifulSoup
from distutils.filelist import findall
import re
import pandas as pd
import functools
from urllib.request import urlopen
from selenium import webdriver
#from selenium.webdriver.chrome.options import Options
import time
import datetime
import random
import os
#from dateutil.rrule import *
import threading
import os

import boto3
from botocore.exceptions import ClientError

from monitor import run

# config sender and receiver
from email_config import SENDER, RECIPIENT, Wechat_Recipient_ID
AWS_REGION = "us-east-2"
CHARSET = "UTF-8"
from wechat_talker import WT


start = datetime.date(2020,9,4)
end= datetime.date(2020,10,1)
#start = datetime.date(2020,10,24)
#end= datetime.date(2020,10,28)
cur='CNY'
jk_blist=['NH921','NH959']    #these two flights is not permitted by CAAC but still sell tickets on ANA official website.



import logging
logger = logging.getLogger('flight_checker')
hdlr = logging.FileHandler('log/flight_checker_{}.log'.format(datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")))
formatter = logging.Formatter('[%(levelname)s] [%(asctime)s] %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.INFO)



def notify(data):
    # Mac system norification
    # os.system("""
    #           osascript -e 'display notification "{}" with title "{} {}" subtitle "{} - {} ￥{}" sound name "Frog"'
    #           """.format(data['官网购票链接'].values[0] , data['日期'].values[0],data['航班号'].values[0], data['始发机场'].values[0],data['到达机场'].values[0],data['票价'].values[0] ))
    ticket_info = "[TICKET], Date {}, Route {} - {}, Flight {},  Price: ￥{}".format(data['日期'].values[0],data['始发机场'].values[0],data['到达机场'].values[0],data['航班号'].values[0],data['票价'].values[0])
    ticket_link = "Link: {}".format(data['官网购票链接'].values[0])
    logger.info("{}\n{}".format(ticket_info, ticket_link))

    # The subject line for the email.
    subject = "[TICKET BOT]: {} {}".format(data['日期'].values[0], data['航班号'].values[0])

    # The email body for recipients with non-HTML email clients.
    body_text = ("{} \n{}".format(ticket_info,ticket_link))
                
    # The HTML body of the email.
    body_html = """<html>
    <head></head>
    <body>
      <h1>[TICKET BOT]: {} {}</h1>
      <h2><a href='{}'>PURCHASE LINK</a></h2>
      <p> 
          {}.
      </p>
    </body>
    </html>""".format(data['日期'].values[0], data['航班号'].values[0], data['官网购票链接'].values[0], ticket_info)

    client = boto3.client('ses',region_name=AWS_REGION)

    # Try to send the email.
    try:
        #Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': body_html,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': body_text,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': subject,
                },
            },
            Source=SENDER,
        )
    # Display an error if something goes wrong.	
    except ClientError as e:
        logger.error(e.response['Error']['Message'])
    else:
        logger.info("Email sent! Message ID: {}".format(response['MessageId']))

    for user_id in Wechat_Recipient_ID:
        WT.send_text_msg(user_id, body_text)

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    #options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1280x1696')
    # options.add_argument('--user-data-dir=/tmp/user-data')
    options.add_argument('--hide-scrollbars')
    # options.add_argument('--enable-logging')
    # options.add_argument('--log-level=0')
    # options.add_argument('--v=99')
    # options.add_argument('--single-process')
    # options.add_argument('--data-path=/tmp/data-path')
    options.add_argument('--ignore-certificate-errors')
    # options.add_argument('--homedir=/tmp')
    # options.add_argument('--disk-cache-dir=/tmp/cache-dir')
    options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')
    # options.binary_location = "/usr/bin/chromium-browser"

    driver = webdriver.Chrome(options=options)
    return driver

# def make_clickable(url, text):
#     return f'<a target="_blank" href="{url}">{text}</a>'

#Searching function
def Search(dept,arrv,date,cur,ali):
    url = 'https://www.google.com/flights?hl=zh-CN#'
    df_record = pd.DataFrame(columns=['日期','始发机场','到达机场','航空公司' ,'航班号','票价','官网购票链接'])  
#     dept='LAX'
#     arrv='SFO'
#     date='2020-11-21'
#     cur='USD'
#     ali='UA'
    if arrv == 'PVG':
        arrv1='SHA'
    else:
        arrv1=arrv
    if date.month <10:
        mo='0'+str(date.month)
    else:
        mo=str(date.month)
    if date.day <10:
        da='0'+str(date.day)
    else:
        da=str(date.day)
    date1=str(date)
    date2=str(date.year)[:2]+str(mo)+str(da)
    date3=str(date.year)+str(mo)+str(da)
    url1=url+'flt='+dept+'.'+arrv+'.'+date1+';c:'+cur+';e:1'+';s:0;a:'+ali+';sd:1;t:f;tt:o'
    driver = init_driver()
    driver.get(url1)
    #wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".gws-flights__flex-filler")))
    time.sleep(1)
    #results = driver.find_elements_by_class_name('LJTSM3-v-d')
    #search=driver.find_elements_by_xpath("//div[@class='gws-flights-results__carriers']")
    #print(driver.find_element_by_css_selector('.gws-flights-results__itinerary-price').text)
    elem = driver.find_element_by_xpath("//*")
    source_code = elem.get_attribute("outerHTML")
    driver.quit()

    bs = BeautifulSoup(source_code, 'html.parser')
    a = bs.find_all('div', class_='gws-flights-results__itinerary-card-summary')
    if a==[]:
        pass
    else:
        for tag in a: 
            fls = tag.findAll('div', class_='gws-flights-results__carriers')
            a1=str(a)
            #for i in range(1,12):
                #if i <= a1.count('gws-flights-results__carriers'):
            fl=fls[0].get_text()
            num = str(tag.find('div',class_="gws-flights-results__select-header gws-flights__flex-filler"))
            num1 = num[num.find(arrv):num.find('class')][4:9]
            price=tag.find('div', class_='gws-flights-results__itinerary-price').text
            link=url1
            df_record = df_record.append({'日期':date1, '始发机场':dept,'到达机场':arrv,'航空公司':fl, '航班号':num1, '票价':price, '官网购票链接':link}, ignore_index=True)       
            notify(df_record.tail(1))
    # global pgbar, percentage_complete,done
    # percentage_complete = percentage_complete + done
    # pgbar.progress(percentage_complete)
    # df_record['官网购票链接'] = df_record['官网购票链接'].apply(make_clickable, args = ('点击前往',))
    return df_record

   
#North America
#@cache_on_button_press('Search') 
def NA(start,end,cur):
    date=start
    df1 = pd.DataFrame(columns=['日期','始发机场','到达机场','航空公司' ,'航班号','票价','官网购票链接']) 
    #st.write('查询进度：')
    #global pgbar
    #pgbar=st.progress(0)
    logger.info("start NA searching {}".format(date))
    while date <= end:
        #print("start NA searching {}".format(date))
        if date.weekday()==0:
            df1=df1.append(Search('LAX','XMN',date,cur,'MF'))
            #st.write(date.strftime('%A')+'完成')
            date=date+datetime.timedelta(days=1)
            time.sleep(random.randint(0,10)/10)
        elif date.weekday()==1:
            date=date+datetime.timedelta(days=1)
        elif date.weekday()==2:
            df1=df1.append(Search('JFK','PVG',date,cur,'MU'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('SFO','PVG',date,cur,'UA'))
            time.sleep(random.randint(0,10)/10)
            # df1=df1.append(Search('YYZ','PEK',date,cur,'HU'))
            # time.sleep(random.randint(0,10)/10)
            # df1=df1.append(Search('YVR','CAN',date,cur,'CZ'))
            # time.sleep(random.randint(0,10)/10)
            # df1=df1.append(Search('YVR','CTU',date,cur,'3U'))
            # st.write(date.strftime('%A')+'完成')
            time.sleep(random.randint(0,10)/10)
            date=date+datetime.timedelta(days=1)
        elif date.weekday()==3:
            df1=df1.append(Search('SEA','PVG',date,cur,'DL'))
            # st.write(date.strftime('%A')+'完成')
            date=date+datetime.timedelta(days=1)
            time.sleep(random.randint(0,10)/10)
        elif date.weekday()==4:
            df1=df1.append(Search('DTW','PVG',date,cur,'DL'))
            time.sleep(random.randint(0,10)/10)
            # df1=df1.append(Search('YVR','XMN',date,cur,'MF'))
            # st.write(date.strftime('%A')+'完成')
            df1=df1.append(Search('SFO','PVG',date,cur,'UA'))
            time.sleep(random.randint(0,10)/10)
            date=date+datetime.timedelta(days=1)
            time.sleep(random.randint(0,10)/10)
        elif date.weekday()==5:
            # df1=df1.append(Search('YYZ','PVG',date,cur,'MU'))
            # time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('SFO','PVG',date,cur,'UA'))
            time.sleep(random.randint(0,10)/10)
            # st.write(date.strftime('%A')+'完成')
            date=date+datetime.timedelta(days=1)
            time.sleep(random.randint(0,10)/10)
        else:
            # df1=df1.append(Search('YVR','PEK',date,cur,'CA'))
            # time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('SFO','PVG',date,cur,'UA'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('LAX','PEK',date,cur,'CA'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('LAX','CAN',date,cur,'CZ'))
            #st.write(date.strftime('%A')+'完成')
            time.sleep(random.randint(0,10)/10)
            # df1=df1.append(Search('YYZ','PEK',date,cur,'HU'))
            # time.sleep(random.randint(0,10)/10)
            date=date+datetime.timedelta(days=1)
    return df1

#Europe part 1: CDG/AMS/FRA
#@cache_on_button_press('Search') 
def EU_p1(start,end,cur):
    date=start
    df1 = pd.DataFrame(columns=['日期','始发机场','到达机场','航空公司' ,'航班号','票价','官网购票链接']) 
    #st.write('查询进度：')
    #global pgbar
    #pgbar=st.progress(0)
    while date <= end:
        if date.weekday()==0:
            df1=df1.append(Search('AMS','PVG',date,cur,'MU'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('FRA','NKG',date,cur,'LH'))
            time.sleep(random.randint(0,5)/10)
            df1=df1.append(Search('FRA','PVG',date,cur,'LH'))
            time.sleep(random.randint(0,10)/10)
            #st.write(date.strftime('%A')+'完成')
            df1=df1.append(Search('CDG','PVG',date,cur,'AF'))
            time.sleep(random.randint(0,10)/10)
            date=date+datetime.timedelta(days=1)
        elif date.weekday()==1:
            df1=df1.append(Search('AMS','PVG',date,cur,'KL'))
            time.sleep(random.randint(0,5)/10)
            df1=df1.append(Search('FRA','PVG',date,cur,'MU'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('CDG','CAN',date,cur,'CZ'))
            time.sleep(random.randint(0,10)/10)
            date=date+datetime.timedelta(days=1)
        elif date.weekday()==2:
            df1=df1.append(Search('CDG','PEK',date,cur,'CA'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('FRA','PVG',date,cur,'LH'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('AMS','XMN',date,cur,'MF'))
            time.sleep(random.randint(0,10)/10)
            date=date+datetime.timedelta(days=1)
        elif date.weekday()==3:
            df1=df1.append(Search('CDG','PVG',date,cur,'AF'))
            date=date+datetime.timedelta(days=1)
            time.sleep(random.randint(0,10)/10)
        elif date.weekday()==4:
            df1=df1.append(Search('AMS','CAN',date,cur,'CZ'))
            time.sleep(0.1)
            date=date+datetime.timedelta(days=1)
        elif date.weekday()==5:
            df1=df1.append(Search('FRA','PVG',date,cur,'CA'))
            time.sleep(random.randint(0,10)/10)
            date=date+datetime.timedelta(days=1)
            time.sleep(0.1)
        else:
            df1=df1.append(Search('CDG','PVG',date,cur,'MU'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('FRA','PVG',date,cur,'LH'))
            time.sleep(random.randint(0,10)/10)
            date=date+datetime.timedelta(days=1)
    return df1



#Europe part 2: other airports
def EU_p2(start,end,cur):
    date=start
    df1 = pd.DataFrame(columns=['日期','始发机场','到达机场','航空公司' ,'航班号','票价','官网购票链接']) 
    #st.write('查询进度：')
    #global pgbar
    #pgbar=st.progress(0)
    while date <= end:
        if date.weekday()==0:
            df1=df1.append(Search('CPH','PEK',date,cur,'CA'))
            time.sleep(random.randint(0,10)/10)
            #st.write(date.strftime('%A')+'完成')
            date=date+datetime.timedelta(days=1)
        elif date.weekday()==1:
            df1=df1.append(Search('BRU','PEK',date,cur,'HU'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('LHR','PVG',date,cur,'VS'))
            #st.write(date.strftime('%A')+'完成')
            time.sleep(random.randint(0,10)/10)
            date=date+datetime.timedelta(days=1)
        elif date.weekday()==2:
            df1=df1.append(Search('IST','CAN',date,cur,'TK'))
            #st.write(date.strftime('%A')+'完成')
            time.sleep(random.randint(0,10)/10)
            date=date+datetime.timedelta(days=1)
        elif date.weekday()==3:
            df1=df1.append(Search('LHR','CAN',date,cur,'CZ'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('SVO','PVG',date,cur,'SU'))
            #st.write(date.strftime('%A')+'完成')
            df1=df1.append(Search('MXP','NKG',date,cur,'NO'))
            time.sleep(random.randint(0,10)/10)
            date=date+datetime.timedelta(days=1)
            time.sleep(random.randint(0,10)/10)
        elif date.weekday()==4:
            df1=df1.append(Search('LHR','PVG',date,cur,'MU;CA'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('WAW','PEK',date,cur,'CA'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('MSQ','PEK',date,cur,'CA'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('ARN','PEK',date,cur,'CA'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('SVO','PEK',date,cur,'CA'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('LHR','TAO',date,cur,'JD'))
            #st.write(date.strftime('%A')+'完成')
            time.sleep(0.5)
            date=date+datetime.timedelta(days=1)
        elif date.weekday()==5:
            df1=df1.append(Search('MAD','PEK',date,cur,'CA'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('VIE','PEK',date,cur,'CA'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('ATH','PEK',date,cur,'CA'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('LIS','XIY',date,cur,'JD'))
            #st.write(date.strftime('%A')+'完成')
            df1=df1.append(Search('BRU','PEK',date,cur,'HU'))
            time.sleep(random.randint(0,10)/10)
            date=date+datetime.timedelta(days=1)
            time.sleep(0.1)
        else:
            df1=df1.append(Search('HEL','PVG',date,cur,'HO'))
            #st.write(date.strftime('%A')+'完成')
            time.sleep(random.randint(0,5)/10)
            df1=df1.append(Search('ZRH','PVG',date,cur,'LX'))
            time.sleep(random.randint(0,10)/10)
            date=date+datetime.timedelta(days=1)
    return df1

#Japan-Korea
#@cache_on_button_press('Search') 
def JK(start,end,cur):
    date=start
    df1 = pd.DataFrame(columns=['日期','始发机场','到达机场','航空公司' ,'航班号','票价','官网购票链接']) 
    #st.write('查询进度：')
    #global pgbar
    #pgbar=st.progress(0)
    while date <= end:
        if date.weekday()==0:
            df1=df1.append(Search('ICN','XMN',date,cur,'MF'))
            #st.write(date.strftime('%A')+'完成')
            date=date+datetime.timedelta(days=1)
            time.sleep(random.randint(0,10)/10)
        elif date.weekday()==1:
            df1=df1.append(Search('KIX','PVG',date,cur,'HO'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('ICN','CGQ',date,cur,'OZ'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('NRT','XIY',date,cur,'MU'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('NRT','FOC',date,cur,'MF'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('NRT','DLC',date,cur,'JL'))
            time.sleep(random.randint(0,10)/10)
            #st.write(date.strftime('%A')+'完成')
            date=date+datetime.timedelta(days=1)
        elif date.weekday()==2:
            df1=df1.append(Search('ICN','WEH',date,cur,'7C'))
            time.sleep(random.randint(0,10)/10)
            #st.write(date.strftime('%A')+'完成')
            date=date+datetime.timedelta(days=1)
        elif date.weekday()==3:
            df1=df1.append(Search('NRT','PVG',date,cur,'CA'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('NRT','SHE',date,cur,'CZ'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('NRT','DLC',date,cur,'JL'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('CJU','XIY',date,cur,'LJ'))
            time.sleep(random.randint(0,10)/10)
            #st.write(date.strftime('%A')+'完成')
            date=date+datetime.timedelta(days=1)
        elif date.weekday()==4:
            df1=df1.append(Search('ICN','PVG',date,cur,'MU'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('NRT','PVG',date,cur,'MU'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('ICN','PEK',date,cur,'CA'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('ICN','TAO',date,cur,'SC'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('NRT','FOC',date,cur,'MF'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('ICN','SZX',date,cur,'BX'))
            time.sleep(random.randint(0,10)/10)
            #st.write(date.strftime('%A')+'完成')
            date=date+datetime.timedelta(days=1)
        elif date.weekday()==5:
            #st.write(date.strftime('%A')+'完成')
            date=date+datetime.timedelta(days=1)
        else:
            #df1=df1.append(Search('NRT','PVG',date,cur,'9C'))
            #time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('NRT','PVG',date,cur,'NH'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('ICN','SHE',date,cur,'CZ'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('ICN','NKG',date,cur,'OZ'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('NRT','SZX',date,cur,'ZH'))
            #st.write(date.strftime('%A')+'完成')
            date=date+datetime.timedelta(days=1)
    return df1

#Aus/Afr/Mid-east/S Asia

def AUAF(start,end,cur):
    date=start
    df1 = pd.DataFrame(columns=['日期','始发机场','到达机场','航空公司' ,'航班号','票价','官网购票链接']) 
    #st.write('查询进度：')
    #global pgbar
    #pgbar=st.progress(0)
    while date <= end:
        if date.weekday()==0:
            df1=df1.append(Search('IKA','CAN',date,cur,'W5'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('DAC','KMG',date,cur,'MU'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('AKL','PVG',date,cur,'NZ'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('ADD','PVG',date,cur,'ET'))
            time.sleep(random.randint(0,10)/10)
            #st.write(date.strftime('%A')+'完成')
            date=date+datetime.timedelta(days=1)
            time.sleep(random.randint(0,10)/10)
        elif date.weekday()==1:
            df1=df1.append(Search('DEL','TYN',date,cur,'CA'))
            time.sleep(random.randint(0,10)/10)
            date=date+datetime.timedelta(days=1)
        elif date.weekday()==2:
            df1=df1.append(Search('IKA','CAN',date,cur,'W5'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('AKL','PVG',date,cur,'MU'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('SYD','PVG',date,cur,'MU'))
            time.sleep(random.randint(0,10)/10)
            #st.write(date.strftime('%A')+'完成')
            date=date+datetime.timedelta(days=1)
        elif date.weekday()==3:            
            df1=df1.append(Search('CAI','CAN',date,cur,'MS'))
            time.sleep(random.randint(0,10)/10)
            #st.write(date.strftime('%A')+'完成')
            date=date+datetime.timedelta(days=1)
            time.sleep(random.randint(0,10)/10)
        elif date.weekday()==4:
            df1=df1.append(Search('CAI','PEK',date,cur,'3U'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('DXB','XIY',date,cur,'CA'))
            #st.write(date.strftime('%A')+'完成')
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('DEL','PVG',date,cur,'MU'))
            time.sleep(random.randint(0,10)/10)
            date=date+datetime.timedelta(days=1)
        elif date.weekday()==5:
            df1=df1.append(Search('ISB','XIY',date,cur,'CA'))
            time.sleep(random.randint(0,10)/10)
            #st.write(date.strftime('%A')+'完成')
            df1=df1.append(Search('DXB','CAN',date,cur,'EK'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('KTM','CAN',date,cur,'CZ'))
            time.sleep(random.randint(0,10)/10)
            date=date+datetime.timedelta(days=1)
        else:
            df1=df1.append(Search('AKL','CAN',date,cur,'CZ'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('SYD','CAN',date,cur,'TR'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('SYD','XMN',date,cur,'MF'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('DOH','CAN',date,cur,'QR'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('KTM','CTU',date,cur,'CA'))
            time.sleep(random.randint(0,10)/10)
            #st.write(date.strftime('%A')+'完成')
            date=date+datetime.timedelta(days=1)
    return df1

#SE Asia Part A
#@cache_on_button_press('Search') 
def SEA_a(start,end,cur):
    date=start
    df1 = pd.DataFrame(columns=['日期','始发机场','到达机场','航空公司' ,'航班号','票价','官网购票链接']) 
    #st.write('查询进度：')
    #global pgbar
    #pgbar=st.progress(0)
    while date <= end:
        if date.weekday() +1 == 1:
            df1=df1.append(Search('SIN','PVG',date,cur,'SQ'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('KUL','HGH',date,cur,'D7'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('BKK','CAN',date,cur,'AQ'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('PNH','CAN',date,cur,'CZ'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('BKK','XMN',date,cur,'MF'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('SIN','CTU',date,cur,'CA'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('SIN','CKG',date,cur,'MI'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('BKK','CAN',date,cur,'AQ'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('PNH','XIY',date,cur,'QV'))
            time.sleep(random.randint(0,10)/10)
            #st.write(date.strftime('%A')+'完成')
            date=date+datetime.timedelta(days=1)
            time.sleep(random.randint(0,10)/10)
        elif date.weekday()+1 == 2:
            df1=df1.append(Search('BKK','PVG',date,cur,'9C'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('KUL','CAN',date,cur,'CZ'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('BKK','TAO',date,cur,'CA'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('SIN','CAN',date,cur,'CZ'))
            time.sleep(random.randint(0,10)/10)
            #st.write(date.strftime('%A')+'完成')
            date=date+datetime.timedelta(days=1)
        elif date.weekday()+1 == 3:
            df1=df1.append(Search('PNH','PVG',date,cur,'MU'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('BKK','CAN',date,cur,'CZ'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('PNH','XMN',date,cur,'MF'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('PNH','CTU',date,cur,'KR'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('PNH','NKG',date,cur,'9C'))
            #st.write(date.strftime('%A')+'完成')
            time.sleep(random.randint(0,10)/10)
            date=date+datetime.timedelta(days=1)
        elif date.weekday() + 1 == 4:
            df1=df1.append(Search('SIN','PVG',date,cur,'MU'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('PNH','CGO',date,cur,'CA'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('SIN','NKG',date,cur,'TR'))
            time.sleep(random.randint(0,10)/10)
            #st.write(date.strftime('%A')+'完成')
            date=date+datetime.timedelta(days=1)
            time.sleep(random.randint(0,10)/10)
        elif date.weekday() +1 == 5:
            df1=df1.append(Search('SIN','PVG',date,cur,'HO'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('BKK','PVG',date,cur,'HO'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('PNH','CAN',date,cur,'LQ'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('SIN','XMN',date,cur,'MF'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('BKK','TSN',date,cur,'XJ'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('KUL','XMN',date,cur,'MF'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('BKK','CAN',date,cur,'AQ'))
            time.sleep(random.randint(0,10)/10)
            #st.write(date.strftime('%A')+'完成')
            date=date+datetime.timedelta(days=1)
        elif date.weekday()+1 == 6:
            #st.write(date.strftime('%A')+'完成')
            date=date+datetime.timedelta(days=1)
        else:
            df1=df1.append(Search('KUL','PVG',date,cur,'FM'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('SIN','CAN',date,cur,'TR'))
            time.sleep(random.randint(0,10)/10)
            date=date+datetime.timedelta(days=1)
    return df1

#SE Asia part B
#@cache_on_button_press('Search') 
def SEA_b(start,end,cur):
    date=start
    df1 = pd.DataFrame(columns=['日期','始发机场','到达机场','航空公司' ,'航班号','票价','官网购票链接']) 
    #st.write('查询进度：')
    #global pgbar
    #pgbar=st.progress(0)
    while date <= end:
        if date.weekday() +1 == 1:
            df1=df1.append(Search('MNL','NKG',date,cur,'2P'))
            time.sleep(random.randint(0,10)/10)

            #st.write(date.strftime('%A')+'完成')
            date=date+datetime.timedelta(days=1)
        elif date.weekday()+1 == 2:
            df1=df1.append(Search('MNL','PVG',date,cur,'MU'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('MNL','TAO',date,cur,'CA'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('VTE','KMG',date,cur,'MU'))
            time.sleep(random.randint(0,10)/10)
            #st.write(date.strftime('%A')+'完成')
            date=date+datetime.timedelta(days=1)
        elif date.weekday()+1 == 3:
            df1=df1.append(Search('RGN','KMG',date,cur,'MU'))
            time.sleep(random.randint(0,10)/10)
            #st.write(date.strftime('%A')+'完成')
            time.sleep(random.randint(0,10)/10)
            date=date+datetime.timedelta(days=1)
        elif date.weekday() + 1 == 4:
            df1=df1.append(Search('MNL','CAN',date,cur,'CZ'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('VTE','KMG',date,cur,'QV'))
            time.sleep(random.randint(0,10)/10)
            #st.write(date.strftime('%A')+'完成')
            date=date+datetime.timedelta(days=1)
            time.sleep(random.randint(0,10)/10)
        elif date.weekday() +1 == 5:
            df1=df1.append(Search('VTE','CAN',date,cur,'CZ'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('MNL','XMN',date,cur,'MF'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('VTE','KMG',date,cur,'MU'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('VTE','KMG',date,cur,'MU'))
            time.sleep(random.randint(0,10)/10)
            #st.write(date.strftime('%A')+'完成')
            time.sleep(1)
            date=date+datetime.timedelta(days=1)
        elif date.weekday()+1 == 6:
            df1=df1.append(Search('KOS','KMG',date,cur,'CA'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('RGN','CAN',date,cur,'CZ'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('CEI','CTU',date,cur,'3U'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('KOS','KMG',date,cur,'CA'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('HAN','NKG',date,cur,'VN'))
            time.sleep(random.randint(0,10)/10)
            #st.write(date.strftime('%A')+'完成')
            date=date+datetime.timedelta(days=1)
            time.sleep(random.randint(0,10)/10)
        else:
            df1=df1.append(Search('RGN','CGO',date,cur,'CA'))
            time.sleep(random.randint(0,10)/10)
            df1=df1.append(Search('VTE','KMG',date,cur,'QV'))
            time.sleep(random.randint(0,10)/10)
            #st.write(date.strftime('%A')+'完成')
            date=date+datetime.timedelta(days=1)
    return df1

def AUAF1():
    global start,end,cur
    while True:  
        start = max(start,datetime.date.today()+ datetime.timedelta(days=1) ) #set start and end time
        df=AUAF(start,end,cur)
        df.to_csv('~/flight_search_auaf.csv')

def SEA1():
    global start,end,cur
    while True:  
        start = max(start,datetime.date.today()+ datetime.timedelta(days=1) ) #set start and end time
        df=SEA_a(start,end,cur)
        df.to_csv('~/flight_search_sea1.csv')

        
def SEA2():
    global start,end,cur
    while True:  
        start = max(start,datetime.date.today()+ datetime.timedelta(days=1) ) #set start and end time
        df=SEA_b(start,end,cur)
        df.to_csv('~/flight_search_sea2.csv')


def NA1():
    global start,end,cur
    while True:  
        start = max(start,datetime.date.today()+ datetime.timedelta(days=1) ) #set start and end time
        df=NA(start,end,cur)
        df.to_csv('~/flight_search_na.csv')

def EU1():
    global start,end,cur
    while True:  
        start = max(start,datetime.date.today()+ datetime.timedelta(days=1) ) #set start and end time
        df=EU_p1(start,end,cur)
        df.to_csv('~/flight_search_eu1.csv')


def EU2():
    global start,end,cur
    while True:  
        start = max(start,datetime.date.today()+ datetime.timedelta(days=1) ) #set start and end time
        df=EU_p2(start,end,cur)
        df.to_csv('~/flight_search_eu2.csv')

        
    
def JK1():
    global start,end,cur,jk_blist
    while True:  
        start = max(start,datetime.date.today()+ datetime.timedelta(days=1) ) #set start and end time
        df=JK(start,end,cur)
        jk_blist=['NH921','NH959']
        df= df_jk[~df_jk['航班号'].isin(jk_blist)] 
        df.to_csv('E:\\flight\\flight_search_jk.csv')
    

if __name__ == '__main__':
    #thread0 = threading.Thread(target=run(), name= 'monitor')
    thread1 = threading.Thread(target=NA1,name='NAThread')

    #thread2 = threading.Thread(target=EU1,name='EU1Thread')
    #thread3 = threading.Thread(target=JK1,name='JKThread')
    #thread4 = threading.Thread(target=EU2,name='EU2Thread')
#add other threads here as well
    #thread0.start()
    thread1.start()
    #thread2.start()
    #thread3.start()
    #thread4.start()

