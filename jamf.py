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
from smtplib import SMTP, SMTPSenderRefused, SMTPDataError, SMTPResponseException
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
        1: {'login':'example@gmail.com', 'password':'secret1', 'host':'imap.gmail.com', 'port':'', 'addr_to':'example@gmx.net', 'addr_from':'example@gmail.com', 'folder':'INBOX'}, 
        2: {'login':'example@gmx.net', 'password':'secret1', 'host':'imap.gmx.net', 'port':'', 'addr_to':'example@gmail.com', 'addr_from':'example@gmx.net', 'folder':'INBOX'}
            }

SMTP_DESTINATION = {'server':'localhost', 'port':'25', 'user':'username', 'password':'password', 'debug_level':'0'}
SMTP_AUTH = False

REWRITE_TO_ADDR = True
REWRITE_FROM_ADDR= False

REMOVE_MAIL_FROM_PROVIDER = True
SHOW_IMAP_FOLDER = False


#Remove none deliverable messages
REMOVE_MAIL_TO_BIG=True
REMOVE_MAIL_BROKEN_MESSAGE=True


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
        SMTPDeliver(mail, imapc, n)
    
    if REMOVE_MAIL_FROM_PROVIDER:
        imapc.expunge()
    
    #Close imap connection
    imapc.logout()

def SMTPDeliver(message, imap_session, id_num):
    #Deliver the message to our SMTP
    try:
        From = message.get('From')
        To = message.get('To')
        Message = message.as_string().encode('ascii', "replace")
        smtpc.sendmail(From, To, Message)
        
        #Mark transferd message as to delete on imap side
        imap_session.store(id_num, '+FLAGS', '\\Deleted')
    
    except (KeyError) as e:
        print (f'KeyError problem found (id:{id_num})')
        print (e)
        if REMOVE_MAIL_BROKEN_MESSAGE:
            print ('Found broken message body, will be removed')
            imap_session.store(id_num, '+FLAGS', '\\Deleted')
    
    except (TypeError) as e:
        print (f'KeyError problem found (id:{id_num})')
        print (e)
    
    except (UnicodeEncodeError) as e:
        print (f'UnicodeEncodeError problem found (id:{id_num})')
        print (e)
    
    except SMTPResponseException as e:
        print (f'SMTPResponseException problem found (id:{id_num})')
        error_code = e.smtp_code
        error_message = e.smtp_error
        if int(error_code) == int('501'):
            print(f'Problem: {error_message}')
            try:
                From = message.get('Return-Path')
                smtpc.sendmail(From, To, Message)

                #Mark transferd message as to delete on imap side
                imap_session.store(id_num, '+FLAGS', '\\Deleted')
            except:
                print (f'Return-Path is not a valid From (id:{id_num})')
        elif int(error_code) == int('552'):
            print(f'Problem: {error_message}')
            if REMOVE_MAIL_TO_BIG:
                print ('Size to big for transfer, message will be removed')
                imap_session.store(id_num, '+FLAGS', '\\Deleted')
    
    except:
        print(f"Unexpected error:", sys.exc_info()[0], '(id:{id_num})')
        imap_session.logout()
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
