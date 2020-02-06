# Just another mail fetcher  (jamf)
-------------
**jamf fetches your mails from an IMAPS server and delivers them to an SMTP server, much like fetchmail does, but using encryption.** 

jamf requires [Python3](https://www.python.org/) to run.
jamf can be easily configured within the script, so that no external configuration has to be loaded.


_Currently jamf only supports IMAP and no POP3, this feature may be supported in in a future release._

**Configuration example:**

```python
provider = { 
        1: {'login':'example@gmail.com', 'password':'secret1', 'host':'imap.gmail.com', 'port':'', 'addr_to':'example@gmx.net', 'addr_from':'example@gmail.com', 'folder':'INBOX'}, 
        2: {'login':'example@gmx.net', 'password':'secret1', 'host':'imap.gmx.net', 'port':'', 'addr_to':'example@gmail.com', 'addr_from':'example@gmx.net', 'folder':'INBOX'}
           }
```

```python
SMTP_DESTINATION = {'server':'smtp.example.com', 'port':'25', 'user':'username', 'password':'pa$$word', 'debug_level':'1'}
```

No voodoo, no black magic, just code.
