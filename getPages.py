#!/usr/bin/env python2.7.x

import ConfigParser
import xmlrpclib
import datetime
import json
import sys
import os

from htmlTmpl import HTMLPage

api = ''
apiIsInit = False

def lookupAppdataFolder(): 
    """Get's the appropriate folders for the .dat files depending on the OS. 
    Taken from bitmessage main.py"""

    APPNAME = "PyBitmessage"
    from os import path, environ
    if sys.platform == 'darwin':
        if "HOME" in environ:
            dataFolder = path.join(os.environ["HOME"], "Library/Application support/", APPNAME) + '/'
        else:
            print '     Could not find home folder, please report this message and your OS X version to the Daemon Github.'
            os.exit()

    elif 'win32' in sys.platform or 'win64' in sys.platform:
        dataFolder = path.join(environ['APPDATA'], APPNAME) + '\\'
    else:
        dataFolder = path.expanduser(path.join("~", ".config/" + APPNAME + "/"))
    return dataFolder

def apiData():
    """Try to load api data from PyBittmessages keys.dat
    Returns tulple of [errorPage, apiData] where on of it is False."""

    keysPath = 'keys.dat'
    
    config = ConfigParser.SafeConfigParser()    
    config.read(keysPath) #First try to load the config file (the keys.dat file) from the program directory

    try:
        config.get('bitmessagesettings','port')
        appDataFolder = ''
    except:
        #Could not load the keys.dat file in the program directory. Perhaps it is in the appdata directory.
        appDataFolder = lookupAppdataFolder()
        keysPath = appDataFolder + keysPath
        config = ConfigParser.SafeConfigParser()
        config.read(keysPath)

        try:
            config.get('bitmessagesettings','port')
        except:
            page = HTMLPage()
            page.addLine(u"<h1>Error</h1>", False)
            page.addLine(u"Can't find keys.dat!")

            return [page.getPage(), False]

    #try: #Try to load settings from keys.dat 
    apiEnabled = config.getboolean('bitmessagesettings', 'apienabled')
    apiPort = int(config.get('bitmessagesettings', 'apiport'))
    apiInterface = config.get('bitmessagesettings', 'apiinterface')
    apiUsername = config.get('bitmessagesettings', 'apiusername')
    apiPassword = config.get('bitmessagesettings', 'apipassword')
    #except:
    #    apiEnabled = False

    if apiEnabled:    
        return [False, "http://" + apiUsername + ":" + apiPassword + "@" + apiInterface+ ":" + str(apiPort) + "/"] #Build the api credentials
    else:
        page = HTMLPage()
        page.addLine(u"<h1>Error</h1>")
        page.addLine(u"PyBittmessage api not configured correctly in keys.dat!")
        return [page.getPage(), False]
        
def apiTest(): 
    """Tests the API connection to bitmessage.
    Returns True if it is connected."""

    try:
        result = api.add(2,3)
    except:
        return False

    if (result == 5):
        return True
    else:
        return False

def connectionErrorPage():
    """Returns page for connection error."""

    page = HTMLPage()
    page.addLine(u"<h1>Error</h1>", False)
    page.addLine(u"Can't connect to bitmessage daemon!")
    return page.getPage()

def validAddress(address):
    """Tests validity of address.
    Returns True if valid."""

    address_information = api.decodeAddress(address)
    address_information = eval(address_information)
        
    if 'success' in str(address_information.get('status')).lower():
        return True
    else:
        return False

def sendMsg(toAddress, fromAddress, subject, message, broadcast=False): 
    """Sends message and return status page.
    All parameters must be unencoded!"""
    
    page = HTMLPage()
    error = False

    if not validAddress(toAddress) and not broadcast:
        page.addLine(u"<h1>Receivers address not valid!</h1>", False)
        error = True
        
    if not validAddress(fromAddress):
        page.addLine(u"<h1>Senders address not valid!</h1>", False)
        error = True

    subject = subject.encode('base64')
    message = message.encode('base64')

    if error:
        return page.getPage()
            
    try:
        if broadcast:
            api.sendBroadcast(fromAddress, subject, message)
        else:
            api.sendMessage(toAddress, fromAddress, subject, message)
        page.addLine(u"<h1>Message send!</h1>", False)
        page.addLine(u"For status see outbox.")
    except:
        apiIsInit = False
        return connectionErrorPage()

    return page.getPage()

def sanitize(text):
    escapes = {'\"': '&quot;',
               '\'': '&#39;',
               '<': '&lt;',
               '>': '&gt;'}

    text = text.replace('&', '&amp;')
    for seq, esc in escapes.iteritems():
        text = text.replace(seq, esc)
    text = text.replace('\n', '<br>')

    return text

def processText(message):
    """Decode message and make it html save."""

    message = message.decode('base64').decode('utf-8')
    message = sanitize(message)
    return message

def inbox(): 
    """Returns inbox or error page."""

    page = HTMLPage()
    page.addLine(u"<h1>Inbox</h1>", False)

    try:
        inboxMessages = json.loads(api.getAllInboxMessages())
    except:
        apiIsInit = False
        return connectionErrorPage()

    messages = inboxMessages['inboxMessages']
    messages.reverse() #Revers order to show newest meesage on top
    for message in messages: 
        msgId = message['msgid']
        if message['read']:
            page.addLine(u"<div class='msgHeaderRead' id='H-%s' onclick='ShowHideDiv(\"%s\")'>" % (msgId, msgId), False)
        else:
            page.addLine(u"<div class='msgHeaderUnread' id='H-%s' onclick='ShowHideDiv(\"%s\")'>" % (msgId, msgId), False)
        page.addLine(u"From: " + getLabelForAddress(message['fromAddress']))
        page.addLine(u"Subject: " + processText(message['subject'])) 
        page.addLine(u"</div><div class='msgBody' id='%s'>" % (msgId), False)
        page.addLine(u"To: " + getLabelForAddress(message['toAddress'])) 
        page.addLine(u"Received: " + datetime.datetime.fromtimestamp(float(message['receivedTime'])).strftime('%Y-%m-%d %H:%M:%S'))
        page.addLine(u"<div class='msgText'>", False)
        page.addLine(processText(message['message']))
        page.addLine(u"</div>")

        #Prepare text for reply and add it to the link
        to = message['fromAddress']

        subject = message['subject'].decode('base64').decode('utf-8')
        if not subject.startswith(u"Re:"):
            subject = u"Re: " + subject
        subject = subject.encode('utf-8').encode('base64')

        text = message['message'].decode('base64').decode('utf-8')
        text = u"\n\n------------------------------------------------------\n" + text
        text = text.encode('utf-8').encode('base64')

        page.addLine(u"<a href='composer?to=%s&subject=%s&text=%s'>Reply</a>" % (to, subject, text), False)
        
        #Add buttons to switch read status
        page.addLine(u"<a onclick='markUnread(\"%s\")'>Unread</a>" % (msgId), False)
        page.addLine(u"<a onclick='delMsg(\"%s\")'>Delete</a>" % (msgId))
        page.addLine(u"</div>")

    return page.getPage()

def outbox():
    """Returns page with outbox or error page."""

    page = HTMLPage()
    page.addLine(u"<h1>Outbox</h1>", False)

    try:
        outboxMessages = json.loads(api.getAllSentMessages())
    except:
        apiIsInit = False
        return connectionErrorPage()

    fallbackId = 0

    messages = outboxMessages['sentMessages']
    messages.reverse() #Revers order to show newest messages on top.
    for message in messages: 
        msgId = message['msgid']
        if msgId == '': #Unsend messages have no id
            msgId = u"fallback_" + str(fallbackId)
            fallbackId += 1
        page.addLine(u"<div class='msgHeaderRead' id='H-%s' onclick='ShowHideDiv(\"%s\")'>" % (msgId, msgId), False)
        page.addLine(u"To: " + getLabelForAddress(message['toAddress'])) 
        page.addLine(u"Subject: " + processText(message['subject'])) 
        page.addLine(u"</div><div class='msgBody' id='%s'>" % (msgId), False)
        page.addLine(u"From: " + getLabelForAddress(message['fromAddress']))
        page.addLine(u"Status: " + message['status']) 
        page.addLine(u"Send: " + datetime.datetime.fromtimestamp(float(message['lastActionTime'])).strftime('%Y-%m-%d %H:%M:%S'))
        page.addLine(u"<div class='msgText'>", False)
        page.addLine(processText(message['message']))
        page.addLine(u"</div>")
        page.addLine(u"<a onclick='delSentMsg(\"%s\")'>Delete</a>" % (msgId))
        page.addLine(u"</div>")

    return page.getPage()

def markRead(msgId):
    """Mark message read.
    Fails silently."""

    try:
        api.getInboxMessageByID(msgId, True)
    except:
        pass

def markUnread(msgId):
    """Mark message unread.
    Fails silently."""

    try:
        api.getInboxMessageByID(msgId, False)
    except:
        pass

def delMsg(msgId):
    """Delete message from inbox.
    Fails silently."""

    try:
        api.trashMessage(msgId)
    except:
        pass

def delSentMsg(msgId):
    """Delete message from outbox.
    Fails silenty."""

    try:
        api.trashSentMessage(msgId)
    except:
        pass

def subscriptions():
    """Returns path with subscriptions or error page."""

    page = HTMLPage()

    try:
        respons = api.listSubscriptions()
        subscriptions = json.loads(respons)
    except:
        isInit = False
        return connectionErrorPage()

    page.addLine(u"<h1>Subscriptions</h1>", False)

    #Form to subscribe to address
    page.addLine(u"<form action='subscribe' methode='get'>", False)
    page.addLine(u"<input type='text' name='addr' id='focus' placeholder='Address' />", False)
    page.addLine(u"<input type='text' name='label' placeholder='Label' />", False)
    page.addLine(u"<input type='submit' value='Subscribe' class='button' />", False)
    page.addLine(u"</form>")

    #List all subscriptions
    for sub in subscriptions['subscriptions']:
        label = sanitize(sub['label'].decode('base64').decode('utf-8'))
        page.addLine(u"<div class='subscription'>", False)
        if (sub['enabled']):
            page.addLine(u"<div class='label'>%s</div>" % (label), False)
        else:
            page.addLine(label + u" (Disabled)")
        page.addLine(sub['address'])

        page.addLine(u"<a href='unsubscribe?addr=%s' onclick='return confirm(\"Unsubscribe from %s?\")'>Unsubscribe</a>" % (sub['address'], label), False)
        page.addLine(u"</div>")
                  
    return page.getPage()

def unsubscribe(addr):
    """Unsubscribes from address.
    Fails silently."""

    if (not validAddress(addr)):
        return

    try:
        api.deleteSubscription(addr)
    except:
        isInit = False

def subscribe(addr, label):
    """Subscribes to address.
    Fails silently."""

    if (not validAddress(addr)):
        return

    try:
        api.addSubscription(addr, label.encode('base64'))
    except:
        pass

def composeMsg(to = "", subject = "", text = ""):
    """Returns page to compose message or error page.
    Optionally takes to, subject or text.
    Subject and text must be base64 encoded."""

    page = HTMLPage()

    if (subject != ""):
        subject = subject.decode('base64').decode('utf-8')
    if (text != ""):
        text = text.decode('base64').decode('utf-8')

    page.addLine(u"<h1>Composer</h1>", False)
    page.addLine(u"<form action='sendmsg' method='get'>", False)

    #Add radio buttons to select direct message or broadcast
    page.addLine(u"<input type='radio' name='broadcast' value='false' onclick='broadcastMsg(false)' checked />", False)
    page.addLine(u"Send direct message")
    page.addLine(u"<input type='radio' name='broadcast' value='true' onclick='broadcastMsg(true)' />", False)
    page.addLine(u"Send broadcast message")

    #To
    page.addLine(u"<input type='text' size='40' name='to' id='to' placeholder='To' value='%s' />" % (to))

    #Get own address to chose sender
    page.addLine(u"From: <select name='from' size='1'>", False)

    try:
        response = api.listAddresses2()
        addresses = json.loads(response)
        for entry in addresses['addresses']:
            opt = u"<option value='%s'>%s</option>" % (entry['address'], entry['label'].decode('base64').decode('utf-8'))
            page.addLine(opt, False)
    except:
        apiIsInit = False
        return connectionErrorPage()

    page.addLine(u"</select>")

    #Subject and message
    page.addLine(u"<input type='text' size='40' name='subject' placeholder='Subject' value='%s' />" % (subject))
    page.addLine(u"<textarea name='text' id='focus' rows='25' cols='50' placeholder='Your message...'>%s</textarea>" % (text))
    page.addLine(u"<input type='submit' class='button' name='send' value='Send message' />")
    page.addLine(u"</form>")

    return page.getPage()

def addressBook():
    """Returns page with address book or error page"""

    try:
        page = HTMLPage()
        page.addLine(u"<h1>Address book</h1>", False)

        #Form to add address
        page.addLine(u"<form action='addaddressbookentry' methode='get'>", False)
        page.addLine(u"<input type='text' name='addr' id='focus' placeholder='Address' />", False)
        page.addLine(u"<input type='text' name='label' placeholder='Label' />", False)
        page.addLine(u"<input type='submit' value='Add' class='button' />", False)
        page.addLine(u"</form>")

        #List all addresses
        response = api.listAddressBookEntries()
        addressBook = json.loads(response)
        for entry in addressBook['addresses']:
            label = sanitize(entry['label'].decode('base64').decode('utf-8'))
            address = entry['address']
            page.addLine(u"<div class='addrbookentry'>", False)
            page.addLine(u"<div class='label'>%s</div>" % (label), False)
            page.addLine(address)
            page.addLine(u"<a href='composer?to=%s'>Write message</a>" % (address), False)
            page.addLine(u"<a href='deladdressbookentry?addr=%s' onclick='return confirm(\"Delete %s?\")'>Delete</a>" % (address, label), False)
            page.addLine(u"</div>")


    except:
        page = connectionErrorPage()
        apiIsInit = False

    return page.getPage()

def getLabelForAddress(address):
    knownAddresses = getKnownAddresses()
    if address in knownAddresses:
        return sanitize(knownAddresses[address])
    else:
        return address


def getKnownAddresses():
    knownAddresses = dict()

    # add from address book
    try:
        response = api.listAddressBookEntries()
        addressBook = json.loads(response)
        for entry in addressBook['addresses']:
            if entry['address'] not in knownAddresses:
                knownAddresses[entry['address']] = u"%s (%s)" % (entry['label'].decode('base64').decode('utf-8'), entry['address'])
    except:
        return False

    # add from my addresses
    try:
        response = api.listAddresses2()
        addresses = json.loads(response)
        for entry in addresses['addresses']:
            if entry['address'] not in knownAddresses:
                knownAddresses[entry['address']] = u"%s (%s)" % (entry['label'].decode('base64').decode('utf-8'), entry['address'])
    except:
        return False

    return knownAddresses

def addAddressBookEntry(addr, label):
    """Add address to address book.
    Fails silently."""

    if (validAddress(addr)):
        try:
            api.addAddressBookEntry(addr, label.encode('base64'))
        except:
            pass

def delAddressBookEntry(addr):
    """Deletes address from address book.
    Fails silently."""

    if (validAddress(addr)):
        try:
            api.deleteAddressBookEntry(addr)
        except:
            pass

def chans():
    """Returns page with chans or error page."""

    page = HTMLPage()

    page.addLine(u"<h1>Chans</h1>", False)

    #Form to join chan
    page.addLine(u"<form action='joinchan' methode='get'>", False)
    page.addLine(u"<input type='text' name='pw' placeholder='Passphrase' />", False)
    page.addLine(u"<input type='text' name='addr' placeholder='Address' />", False)
    page.addLine(u"<input type='submit' value='Join' class='button' />", False)
    page.addLine(u"</form>")

    #Form to create chan
    page.addLine(u"<form action='createchan' methode='get'>", False)
    page.addLine(u"<input type='text' name='pw' placeholder='Passphrase' />", False)
    page.addLine(u"<input type='submit' value='Create' class='button' />", False)
    page.addLine(u"</form>")

    #Show all chans
    try:
        addresses = json.loads(api.listAddresses2())
    except:
        isInit = False
        return connectionErrorPage()
    
    for addr in addresses['addresses']:
        if (not addr['chan']):
            continue
        label = sanitize(addr['label'].decode('base64').decode('utf-8'))
        if label.startswith("[chan] "):
            label = label[7:]
        address = addr['address']
        page.addLine(u"<div class='addrbookentry'>", False)
        if (addr['enabled']):
            page.addLine(u"<div class='label'>%s</div>" % (label), False)
        else:
            page.addLine(label + u" (Disabled)")
        page.addLine(address)
        page.addLine(u"(Stream %s)" % (str(addr['stream']))) #????
        page.addLine(u"<a href='leavechan?addr=%s' onclick='return confirm(\"Leave %s?\")'>Leave</a>" % (address, label), False)
        page.addLine(u"</div>")

    return page.getPage()

def createChan(pw):
    """Creates Chan.
    Fails silently."""

    try:
        api.createChan(pw.encode('base64'))
    except:
        pass

def joinChan(pw, addr):
    """Joins Chan.
    Fails silently."""

    try:
        api.joinChan(pw.encode('base64'), addr)
    except:
        pass

def leaveChan(addr):
    """Leave Chan.
    Fails silenty."""

    try:
        api.leaveChan(addr)
    except:
        pass

def identities():
    """Returns page with identities or error page."""

    page = HTMLPage()

    page.addLine(u"<h1>Your Identities</h1>", False)

    #Form to add random address
    page.addLine(u"<form action='addrandomaddress' methode='get'>", False)
    page.addLine(u"New random address: ", False)
    page.addLine(u"<input type='text' name='label' placeholder='Label' />", False)
    page.addLine(u"<input type='submit' value='Generate' class='button' />", False)
    page.addLine(u"</form>")

    #Show all addresses
    try:
        addresses = json.loads(api.listAddresses2())
    except:
        isInit = False
        return connectionErrorPage()
    
    for addr in addresses['addresses']:
        if (addr['chan']):
            continue
        label = sanitize(addr['label'].decode('base64').decode('utf-8'))
        address = addr['address']
        page.addLine(u"<div class='addrbookentry'>", False)
        if (addr['enabled']):
            page.addLine(u"<div class='label'>%s</div>" % (label), False)
        else:
            page.addLine(label + u" (Disabled)")
        page.addLine(address)
        page.addLine(u"(Stream %s)" % (str(addr['stream'])))
        page.addLine(u"<a href='deladdress?addr=%s' onclick='return confirm(\"Remove %s permanently?\")'>Delete</a>" % (address, label), False)
        page.addLine(u"</div>")

    return page.getPage()

def genRandomAddress(label):
    """Generates random address.
    Fails silently."""

    try:
        api.createRandomAddress(label.encode('base64'))
    except:
        pass

def delAddress(addr):
    """Deletes address.
    Fails silently."""

    try:
        api.deleteAddress(addr)
    except:
        pass
        
def initApi():
    """Init api. Returns error page in case of error, else returns False."""

    global api
    global apiIsInit

    error, data = apiData()
    if (error):
        return error

    api = xmlrpclib.ServerProxy(data) #Connect to BitMessage using these api credentials
    if (not apiTest()):
        return connectionErrorPage()
            
    apiIsInit = True
    return False
