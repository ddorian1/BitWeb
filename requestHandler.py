#!/usr/bin/env python2

# Copyright (C) 2014 Johannes Schwab

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from BaseHTTPServer import BaseHTTPRequestHandler
from os import urandom
from time import sleep
import socket
import cgi
import Cookie
import password
import getPages
from htmlTmpl import HTMLPage

sessionID = None

def parseQuery(url):
    if not '?' in url:
        return dict()
    
    query = url[url.find('?')+1:]
    return cgi.parse_qs(query, keep_blank_values = True)

class myRequestHandler(BaseHTTPRequestHandler):
    def write(self, data):
        if not self.headerFinished:
            self.headerFinished = True
            self.end_headers()

        self.wfile.write(data)

    def do_GET(self):
        global sessionID
        self.headerFinished = False
        self.send_response(200)

        #return favicon.ico
        if self.path.startswith("/favicon.ico"):
            self.send_header('Content-type', 'image/x-icon')

            try: 
                f = open("favicon.ico", "rb")
                self.write(f.read())
            except:
                pass
            return

        #Header for text
        self.send_header('Content-type', 'text/html')

        #Session Management
        authenticated = False

        #Check password
        if self.path.startswith("/pwd"):
            query = parseQuery(self.path)
            try:
                pwd = query["pwd"][0]
            except:
                pwd = None

            if password.isCorrect(pwd):
                sessionID = urandom(16).encode('base64').strip()
                self.send_header("Set-Cookie", "sessionID=" + sessionID)
                authenticated = True
                self.path = "/inbox"
                sleep(1) #To slow down brutforce
            else:
                self.write(password.enterHTML(True))
                sleep(1) #To slow down brutforce
                return


        #Set password
        if self.path.startswith("/setpwd") and not password.isSet():
            query = parseQuery(self.path)
            try:
                pwd = query["pwd"][0]
                password.set(pwd)
                authenticated = True
            except:
                authenticated = False

        #Logout
        if self.path.startswith("/logout"):
            sessionID = None

        #Check seesionID from cookie
        if sessionID and not authenticated:
            try:
                cookie = Cookie.SimpleCookie(self.headers.getheader("cookie"))
                if sessionID == cookie['sessionID'].value:
                    authenticated = True
            except:
                authenticated = False

        #If not authenticated
        if not authenticated:
            if password.isSet():
                self.write(password.enterHTML())
            else:
                self.write(password.setHTML())
            return

        #End session management. 
        #The following code should only be executed when the user has passed authentication!

        #Init api
        if (not getPages.apiIsInit):
            error = getPages.initApi();

            if (error):
                self.write(error)
                return
                
        #Handel called URL
        if self.path.startswith("/inbox") or self.path == "/":
            self.write(getPages.inbox())

        elif self.path.startswith("/outbox"):
            self.write(getPages.outbox())

        elif self.path.startswith("/composer"):
            query = parseQuery(self.path)
            toAddress = ""
            subject = ""
            text = ""
            try:
                if query.has_key("to"):
                    toAddress = query["to"][0]
                if query.has_key("subject"):
                    subject = query["subject"][0]
                if query.has_key("text"):
                    text = query["text"][0]
            except:
                pass
                
            self.write(getPages.composeMsg(toAddress, subject, text))

        elif self.path.startswith("/sendmsg"):
            query = parseQuery(self.path)
            
            try:
                if query.has_key("to"):
                    toAddress = query["to"][0]
                else:
                    toAddress = ""
                fromAddress = query["from"][0]
                subject = query["subject"][0]
                text = query["text"][0]
                if query["broadcast"][0] == "true":
                    broadcast = True
                else:
                    broadcast = False
            except:
                page = HTMLPage()
                page.addLine("<h1>Error while parsing message.")
                page.addLine("Message NOT send!</h1>")
                self.write(page.getPage())
                return

            self.write(getPages.sendMsg(toAddress, fromAddress, subject, text, broadcast))

        elif self.path.startswith("/subscriptions"):
            self.write(getPages.subscriptions())

        elif self.path.startswith("/unsubscribe"):
            query = parseQuery(self.path)

            try:
                addr = query["addr"][0]
                getPages.unsubscribe(addr)
            except:
                pass

            self.write(getPages.subscriptions())

        elif self.path.startswith("/subscribe"):
            query = parseQuery(self.path)

            try:
                addr = query["addr"][0]
                label = query["label"][0]
                getPages.subscribe(addr, label)
            except:
                pass

            self.write(getPages.subscriptions())

        elif self.path.startswith("/addressbook"):
            self.write(getPages.addressBook())

        elif self.path.startswith("/addaddressbookentry"):
            query = parseQuery(self.path)

            try:
                addr = query["addr"][0]
                label = query["label"][0]
                getPages.addAddressBookEntry(addr, label)
            except:
                pass

            self.write(getPages.addressBook())

        elif self.path.startswith("/deladdressbookentry"):
            query = parseQuery(self.path)

            try:
                addr = query["addr"][0]
                getPages.delAddressBookEntry(addr)
            except:
                pass

            self.write(getPages.addressBook())

        elif self.path.startswith("/chans"):
            self.write(getPages.chans())

        elif self.path.startswith("/createchan"):
            query = parseQuery(self.path)

            try:
                pw = query["pw"][0]
                getPages.createChan(pw)
            except:
                pass
            
            self.write(getPages.chans())

        elif self.path.startswith("/joinchan"):
            query = parseQuery(self.path)

            try:
                pw = query["pw"][0]
                addr = query["addr"][0]
                getPages.joinChan(pw, addr)
            except:
                pass
            
            self.write(getPages.chans())

        elif self.path.startswith("/leavechan"):
            query = parseQuery(self.path)

            try:
                addr = query["addr"][0]
                getPages.leaveChan(addr)
            except:
                pass
            
            self.write(getPages.chans())

        elif self.path.startswith("/identities"):
            self.write(getPages.identities())

        elif self.path.startswith("/addrandomaddress"):
            query = parseQuery(self.path)

            try:
                label = query["label"][0]
                getPages.genRandomAddress(label)
            except:
                pass

            self.write(getPages.identities())

        elif self.path.startswith("/deladdress"):
            query = parseQuery(self.path)

            try:
                addr = query["addr"][0]
                getPages.delAddress(addr)
            except:
                pass

            self.write(getPages.identities())

        elif self.path.startswith("/markread"):
            query = parseQuery(self.path)

            try:
                msgid = query["msgid"][0]
            except:
                return

            getPages.markRead(msgid)

        elif self.path.startswith("/markunread"):
            query = parseQuery(self.path)

            try:
                msgid = query["msgid"][0]
            except:
                return

            getPages.markUnread(msgid)

        elif self.path.startswith("/delmsg"):
            query = parseQuery(self.path)

            try:
                msgid = query["msgid"][0]
            except:
                return

            getPages.delMsg(msgid)

        elif self.path.startswith("/delsentmsg"):
            query = parseQuery(self.path)

            try:
                msgid = query["msgid"][0]
            except:
                return

            getPages.delSentMsg(msgid)

        else:
            html = HTMLPage()
            html.addLine("<h1>Page not found!</h1>", False)
            self.write(html.getPage())
