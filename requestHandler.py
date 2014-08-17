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

#Value of valid session cookie
sessionID = None

class myRequestHandler(BaseHTTPRequestHandler):
    def write(self, data):
        if not self.headerFinished:
            self.headerFinished = True
            self.end_headers()

        self.wfile.write(data)

    def isAuthenticated(self):
        global sessionID

        #Check seesionID from cookie
        if sessionID:
            try:
                cookie = Cookie.SimpleCookie(self.headers.getheader("cookie"))
                if sessionID == cookie['sessionID'].value:
                    return True
            except:
                pass

        #If not authenticated

        #Header for text
        self.send_header('Content-type', 'text/html')

        if password.isSet():
            self.write(password.enterHTML())
        else:
            self.write(password.setHTML())
        return False

    def initApi(self):
        if (not getPages.apiIsInit):
            error = getPages.initApi();

            if (error):
                self.write(error)
                return False
        return True

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

        #Parse query
        if '?' in self.path:
            qs = self.path[self.path.find('?')+1:]
            query = cgi.parse_qs(qs, keep_blank_values = True)
        else:
            query = None

        #Check Authentication
        if not self.isAuthenticated():
            return

        #The following code should only be executed when the user has passed authentication!

        #Check api
        if not self.initApi():
            return
                
        #Handel called URL

        #Return requested image
        if self.path.startswith("/getimage"):
            params = self.path.split("-")
            imageHash = params[1].split(".")[0]
            
            ret = getPages.getImage(imageHash)
            if not ret:
                return

            mimeType, image = ret
            
            self.send_header('Content-type', mimeType)
            self.write(image)
            return
        else:
            #Header for text
            self.send_header('Content-type', 'text/html')

        #Return requestet page
        if self.path.startswith("/inbox") or self.path == "/":
            self.write(getPages.inbox())

        elif self.path.startswith("/outbox"):
            self.write(getPages.outbox())

        elif self.path.startswith("/composer"):
            self.write(getPages.composeMsg())

        elif self.path.startswith("/subscriptions"):
            self.write(getPages.subscriptions())

        elif self.path.startswith("/addressbook"):
            self.write(getPages.addressBook())

        elif self.path.startswith("/chans"):
            self.write(getPages.chans())

        elif self.path.startswith("/identities"):
            self.write(getPages.identities())

        elif self.path.startswith("/logout"):
            sessionID = None
            self.write(password.enterHTML())

        elif self.path.startswith("/markread"):
            try:
                msgid = query["msgid"][0]
            except:
                return

            getPages.markRead(msgid)

        elif self.path.startswith("/markunread"):
            try:
                msgid = query["msgid"][0]
            except:
                return

            getPages.markUnread(msgid)

        elif self.path.startswith("/delmsg"):
            try:
                msgid = query["msgid"][0]
            except:
                return

            getPages.delMsg(msgid)

        elif self.path.startswith("/delsentmsg"):
            try:
                msgid = query["msgid"][0]
            except:
                return

            getPages.delSentMsg(msgid)

        else:
            html = HTMLPage()
            html.addLine("<h1>Page not found!</h1>", False)
            self.write(html.getPage())

    def do_POST(self):
        global sessionID
        self.headerFinished = False
        self.send_response(200)

        #Parse query
        try:
            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                query = cgi.parse_multipart(self.rfile, pdict)
            else:
                query = None
        except:
            query = None

        #Session Management
        authenticated = False

        #Check password
        if self.path.startswith("/pwd"):
            try:
                pwd = query.get("pwd")[0]
            except:
                pwd = None

            if password.isCorrect(pwd):
                sessionID = urandom(16).encode('base64').strip()
                self.send_header("Set-Cookie", "sessionID=" + sessionID)
                authenticated = True
                #Redirect to inbox
                self.path = "/inbox"
                sleep(1) #To slow down brutforce
            else:
                self.send_header('Content-type', 'text/html')
                self.write(password.enterHTML(True))
                sleep(1) #To slow down brutforce
                return

        #Set password
        if self.path.startswith("/setpwd") and not password.isSet():
            try:
                pwd = query["pwd"][0]
                password.set(pwd)
                authenticated = True
            except:
                authenticated = False

        #Check Authentication
        if (not authenticated) and (not self.isAuthenticated()) :
            return

        #End of session management. 
        #The following code should only be executed when the user has passed authentication!

        #Check api
        if not self.initApi():
            return

        #Header for text
        self.send_header('Content-type', 'text/html')
                
        #Handel called URL
        if self.path.startswith("/inbox") or self.path == "/":
            self.write(getPages.inbox())

        elif self.path.startswith("/composer"):
            toAddress = False
            replyTo = False
            try:
                if query.has_key("to"):
                    toAddress = query["to"][0]
                if query.has_key("replyto"):
                    replyTo = query["replyto"][0]
            except:
                pass
                
            self.write(getPages.composeMsg(replyTo, toAddress))

        elif self.path.startswith("/sendmsg"):
            try:
                if query.has_key("to"):
                    toAddress = query["to"][0]
                else:
                    #There is no reciever for broadcast messages
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

        elif self.path.startswith("/unsubscribe"):
            try:
                addr = query["addr"][0]
                getPages.unsubscribe(addr)
            except:
                pass

            self.write(getPages.subscriptions())

        elif self.path.startswith("/subscribe"):
            try:
                addr = query["addr"][0]
                label = query["label"][0]
                getPages.subscribe(addr, label)
            except:
                pass

            self.write(getPages.subscriptions())

        elif self.path.startswith("/addaddressbookentry"):
            try:
                addr = query["addr"][0]
                label = query["label"][0]
                getPages.addAddressBookEntry(addr, label)
            except:
                pass

            self.write(getPages.addressBook())

        elif self.path.startswith("/deladdressbookentry"):
            try:
                addr = query["addr"][0]
                getPages.delAddressBookEntry(addr)
            except:
                pass

            self.write(getPages.addressBook())

        elif self.path.startswith("/createchan"):
            try:
                pw = query["pw"][0]
                getPages.createChan(pw)
            except:
                pass
            
            self.write(getPages.chans())

        elif self.path.startswith("/joinchan"):
            try:
                pw = query["pw"][0]
                addr = query["addr"][0]
                getPages.joinChan(pw, addr)
            except:
                pass
            
            self.write(getPages.chans())

        elif self.path.startswith("/leavechan"):
            try:
                addr = query["addr"][0]
                getPages.leaveChan(addr)
            except:
                pass
            
            self.write(getPages.chans())

        elif self.path.startswith("/addrandomaddress"):
            try:
                label = query["label"][0]
                getPages.genRandomAddress(label)
            except:
                pass

            self.write(getPages.identities())

        elif self.path.startswith("/deladdress"):
            try:
                addr = query["addr"][0]
                getPages.delAddress(addr)
            except:
                pass

            self.write(getPages.identities())

        else:
            html = HTMLPage()
            html.addLine("<h1>Page not found!</h1>", False)
            self.write(html.getPage())
