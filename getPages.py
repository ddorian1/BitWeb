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
            page.addLine("<h1>Error</h1>")
            page.addLine("Can't find keys.dat!")

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
        page.addLine("<h1>Error</h1>")
        page.addLine("PyBittmessage api not configured correctly in keys.dat!")
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
    page.addLine("<h1>Error</h1>")
    page.addLine("Can't connect to bitmessage daemon!")
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

def sendMsg(toAddress, fromAddress, subject, message): 
    """Sends message and return status page.
    All parameters must be unencoded!"""
    
    page = HTMLPage()
    error = False

    if not validAddress(toAddress):
        page.addLine("<h1>Receivers address not valid!</h1>", False)
        error = True
        
    if not validAddress(fromAddress):
        page.addLine("<h1>Senders address not valid!</h1>", False)
        error = True

    if (subject == ''):
        page.addLine("<h1>No subject given!</h1>", False)
        error = True
    else:
        subject = subject.encode('base64')

    if (message == ''):
        page.addLine("<h1>No message given!</h1>", False)
        error = True
    else: 
        message = message.encode('base64')

    if error:
        return page.getPage()
            
    try:
        ackData = api.sendMessage(toAddress, fromAddress, subject, message)
        page.addLine("<h1>Message send!</h1>", False)
        page.addLine("For status see outbox.")
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

    message = message.decode('base64')
    message = sanitize(message)
    return message

def inbox(): 
    """Returns inbox or error page."""

    page = HTMLPage()
    page.addLine("<h1>Inbox</h1>", False)

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
            page.addLine("<div class='msgHeaderRead' id='H-%s' onclick='ShowHideDiv(\"%s\")'>" % (msgId, msgId), False)
        else:
            page.addLine("<div class='msgHeaderUnread' id='H-%s' onclick='ShowHideDiv(\"%s\")'>" % (msgId, msgId), False)
        page.addLine("From: " + getLabelForAddress(message['fromAddress']))
        page.addLine("Subject: " + processText(message['subject'])) 
        page.addLine("</div><div class='msgBody' id='%s'>" % (msgId), False)
        page.addLine("To: " + getLabelForAddress(message['toAddress'])) 
        page.addLine("Received: " + datetime.datetime.fromtimestamp(float(message['receivedTime'])).strftime('%Y-%m-%d %H:%M:%S'))
        page.addLine("<div class='msgText'>", False)
        page.addLine(processText(message['message']))
        page.addLine("</div>")

        #Prepare text for reply and add it to the link
        to = message['fromAddress']

        subject = message['subject'].decode('base64')
        if not subject.startswith("Re:"):
            subject = "Re: " + subject
        subject = subject.encode('base64')

        text = message['message'].decode('base64')
        text = "\n\n------------------------------------------------------\n" + text
        text = text.encode('base64')

        page.addLine("<a href='composer?to=%s&subject=%s&text=%s'>Reply</a>" % (to, subject, text), False)
        
        #Add buttons to switch read/unread status
        #page.addLine("<a onclick='markRead(\"%s\")'>Read</a>" % (msgId), False)
        page.addLine("<a onclick='markUnread(\"%s\")'>Unread</a>" % (msgId), False)
        page.addLine("<a onclick='delMsg(\"%s\")'>Delete</a>" % (msgId))
        page.addLine("</div>")

    return page.getPage()

def outbox():
    """Returns page with outbox or error page."""

    page = HTMLPage()
    page.addLine("<h1>Outbox</h1>", False)

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
            msgId = "fallback_" + str(fallbackId)
            fallbackId += 1
        page.addLine("<div class='msgHeaderRead' id='H-%s' onclick='ShowHideDiv(\"%s\")'>" % (msgId, msgId), False)
        page.addLine("To: " + getLabelForAddress(message['toAddress'])) 
        page.addLine("Subject: " + processText(message['subject'])) 
        page.addLine("</div><div class='msgBody' id='%s'>" % (msgId), False)
        page.addLine("From: " + getLabelForAddress(message['fromAddress']))
        page.addLine("Status: " + message['status']) 
        page.addLine("Send: " + datetime.datetime.fromtimestamp(float(message['lastActionTime'])).strftime('%Y-%m-%d %H:%M:%S'))
        page.addLine("<div class='msgText'>", False)
        page.addLine(processText(message['message']))
        page.addLine("</div>")
        page.addLine("<a onclick='delSentMsg(\"%s\")'>Delete</a>" % (msgId))
        page.addLine("</div>")

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

    page.addLine("<h1>Subscriptions</h1>", False)

    #Form to subscribe to address
    page.addLine("<form action='subscribe' methode='get'>", False)
    page.addLine("<input type='text' name='addr' placeholder='Address' />", False)
    page.addLine("<input type='text' name='label' placeholder='Label' />", False)
    page.addLine("<input type='submit' value='Subscribe' class='button' />", False)
    page.addLine("</form>")

    #List all subscriptions
    for sub in subscriptions['subscriptions']:
        label = sanitize(sub['label'].decode('base64'))
        page.addLine("<div class='subscription'>", False)
        if (sub['enabled']):
            page.addLine("<div class='label'>%s</div>" % (label), False)
        else:
            page.addLine(label + " (Disabled)")
        page.addLine(sub['address'])

        page.addLine("<a href='unsubscribe?addr=%s'>Unsubscribe</a>" % (sub['address']), False)
        page.addLine("</div>")
                  
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
        subject = subject.decode('base64')
    if (text != ""):
        text = text.decode('base64')

    page.addLine("<h1>Composer</h1>", False)
    page.addLine("<form action='sendmsg' method='get'>", False)
    page.addLine("<input type='text' size='40' name='to' placeholder='To' value='%s' />" % (to))

    #Get own address to chose sender
    page.addLine("From: <select name='from' size='1'>", False)

    try:
        response = api.listAddresses2()
        addresses = json.loads(response)
        for entry in addresses['addresses']:
            opt = "<option value='%s'>%s</option>" % (entry['address'], entry['label'].decode('base64'))
            page.addLine(opt, False)
    except:
        apiIsInit = False
        return connectionErrorPage()

    page.addLine("</select>")

    page.addLine("<input type='text' size='40' name='subject' placeholder='Subject' value='%s' />" % (subject))
    page.addLine("<textarea name='text' rows='25' cols='50' placeholder='Your message...'>%s</textarea>" % (text))
    page.addLine("<input type='submit' class='button' name='send' value='Send message' />")
    page.addLine("</form>")

    return page.getPage()

def addressBook():
    """Returns page with address book or error page"""

    try:
        page = HTMLPage()
        page.addLine("<h1>Address book</h1>", False)

        #Form to add address
        page.addLine("<form action='addaddress' methode='get'>", False)
        page.addLine("<input type='text' name='addr' placeholder='Address' />", False)
        page.addLine("<input type='text' name='label' placeholder='Label' />", False)
        page.addLine("<input type='submit' value='Add' class='button' />", False)
        page.addLine("</form>")

        #List all addresses
        response = api.listAddressBookEntries()
        addressBook = json.loads(response)
        for entry in addressBook['addresses']:
            label = sanitize(entry['label'].decode('base64'))
            address = entry['address']
            page.addLine("<div class='addrbookentry'>", False)
            page.addLine("<div class='label'>%s</div>" % (label), False)
            page.addLine(address)
            page.addLine("<a href='composer?to=%s'>Write message</a>" % (address), False)
            page.addLine("<a href='deladdress?addr=%s'>Delete</a>" % (address), False)
            page.addLine("</div>")


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
                knownAddresses[entry['address']] = "%s (%s)" % (entry['label'].decode('base64'), entry['address'])
    except:
        return False

    # add from my addresses
    try:
        response = api.listAddresses2()
        addresses = json.loads(response)
        for entry in addresses['addresses']:
            if entry['address'] not in knownAddresses:
                knownAddresses[entry['address']] = "%s (%s)" % (entry['label'].decode('base64'), entry['address'])
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
