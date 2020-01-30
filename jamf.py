#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 29 2020
@author: Boris Kassautzki


jampf - Just another mail fetcher
jampf can fetch imap mails from your provider and forward it to an smtp
like fetchmail it did. 
"""
from imaplib import IMAP4_SSL
from smtplib import SMTP
import email
import sys


#Example Configuration
'''
Provider settings are stored in a nasted dictionary, so you can easily edit and add new.
For new provider settings copy an existing entry, just remember to increment the counter at beginn
and the comma at the end of the line, execpt for last entry.

#example provider configuration
provider = { 
        1: {'login':'example@gmail.com', 'password':'secret1', 'host':'imap.gmail.com', 'port':'', 'addr_to':'example@gmx.net', 'addr_from':'example@gmail.com', 'folder':'INBOX'}, 
        2: {'login':'example@gmx.net', 'password':'secret1', 'host':'imap.gmx.net', 'port':'', 'addr_to':'example@gmail.com', 'addr_from':'example@gmx.net', 'folder':'INBOX'}
            }

In this dict you configure the target SMTP Server where you want to deliver the fetched messages to.
SMTP_DESTINATION = {'server':'smtp.example.com', 'port':'25', 'user':'username', 'password':'password', 'debug_level':'3'}

The following settings are bolean, valid entrys are True or False

SMTP_AUTH = True / False
This setting can be usefull if you don't need to auth on the SMTP Server, for example if the service run local.

REWRITE_TO_ADDR = True / False
REWRITE_FROM_ADDR = True / False
With this settings you can actived the header rewrite function configured in the provider dict,
if disabled it will use the original from  message header.

REMOVE_MAIL_FROM_PROVIDER = True / False
Will remove messages from imap after transfer to our smtp server

SHOW_IMAP_FOLDER = True / False
When active it will show your the avalible imap folder on provider
'''
provider = {
        1: {'login':'example@gmail.com', 'password':'secret1', 'host':'imap.gmail.com', 'port':'', 'addr_to':'example@gmx.net', 'addr_fro>
        2: {'login':'example@gmx.net', 'password':'secret1', 'host':'imap.gmx.net', 'port':'', 'addr_to':'example@gmail.com', 'addr_from'>
            }

SMTP_DESTINATION = {'server':'smtp.example.com', 'port':'25', 'user':'username', 'password':'password', 'debug_level':'3'}

SMTP_AUTH = True

REWRITE_TO_ADDR = False
REWRITE_FROM_ADDR= False

REMOVE_MAIL_FROM_PROVIDER = False
SHOW_IMAP_FOLDER = False

def ImapConn(_id):
    server = provider[_id]['host']
    user = provider[_id]['login']
    passwd = provider[_id]['password']
    folder = provider[_id]['folder']
    
    imap_conn = IMAP4_SSL(server)
    imap_conn.login(user, passwd)
    if SHOW_IMAP_FOLDER:
        print (f"Found Imap Folder for {user}:") 
        print(imap_conn.lsub())
    imap_conn.select(folder)
    return imap_conn
    
def SMTPConn():
    server = SMTP(SMTP_DESTINATION['server'], SMTP_DESTINATION['port'])
    server.set_debuglevel(int(SMTP_DESTINATION['debug_level']))
    server.starttls
    if SMTP_AUTH:
        server.login(SMTP_DESTINATION['user'], SMTP_DESTINATION['password'])
    return server

def EditHeader(message, _id):
    #Edit header based on provider config, if enabled
    if REWRITE_TO_ADDR:
        TO_ADDR = provider[_id]['addr_to']
        try: 
            message.replace_header('To', TO_ADDR)
        except KeyError:
            message.add_header('To', TO_ADDR)
    if REWRITE_FROM_ADDR:
        FROM_ADDR = provider[_id]['addr_from']
        try: 
            message.replace_header('From', FROM_ADDR)
        except KeyError:
            message.add_header('From', FROM_ADDR)
    return message


def Messagefetcher(_id):
    #Open connection to imap server and check for new messages
    imapc = ImapConn(_id)
    status, data = imapc.search(None, 'ALL')
    
    #Fetch all found messages based on there number
    for n in data[0].split():
        status, msgdata = imapc.fetch(n, '(RFC822)')
        msg = msgdata[0][1]
        mail = email.message_from_bytes(msg)
        mail = EditHeader(mail, provider_id)
        SMTPDeliver(mail)

        #Mark message as to delete on imap server side
        imapc.store(n, '+FLAGS', '\\Deleted')
    
    if REMOVE_MAIL_FROM_PROVIDER:
        imapc.expunge()
    
    #Close imap connection
    imapc.logout()

def SMTPDeliver(message):
    #Deliver the message to our SMTP
    try:
        print (message.get('From'), message.get('to'))
        smtpc.sendmail(message.get('From'), message.get('to'), message.as_string().encode('ascii', "replace"))
    except:
        print("Unexpected error:", sys.exc_info()[0])
        imapc.logout()
        smtpc.quit()
        sys.exit(1)

if __name__ == "__main__":
    #Connect to SMTP Server
    smtpc = SMTPConn()

    #Start fetchting new messages from configured imap provider
    for provider_id, values in provider.items():
        Messagefetcher(provider_id)

    #Close SMTP Connection after finish
    smtpc.quit()
