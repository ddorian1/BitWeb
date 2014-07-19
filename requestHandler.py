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
    def do_GET(self):
        global sessionID

        self.send_response(200)
        self.send_header('Content-type', 'text/html')

        authenticated = False

        #Session Management
        if self.path.startswith("/pwd"):
            query = parseQuery(self.path)
            try:
                pwd = query["pwd"][0]
            except:
                pwd = ""

            if password.isCorrect(pwd):
                sessionID = urandom(16).encode('base64').strip()
                self.send_header("Set-Cookie", "sessionID=" + sessionID)
                authenticated = True
                self.path = "/inbox"
                sleep(1) #To slow down brutforce
            else:
                self.wfile.write(password.enterHTML(True))
                sleep(1) #To slow down brutforce
                return


        if self.path.startswith("/setpwd") and not password.isSet():
            query = parseQuery(self.path)
            try:
                pwd = query["pwd"][0]
                password.set(pwd)
                authenticated = True
            except:
                authenticated = False

        if self.path.startswith("/logout"):
            sessionID = None

        if sessionID and not authenticated:
            try:
                cookie = Cookie.SimpleCookie(self.headers.getheader("cookie"))
                if sessionID == cookie['sessionID'].value:
                    authenticated = True
            except:
                authenticated = False

        self.end_headers()

        if not authenticated:
            if password.isSet():
                self.wfile.write(password.enterHTML())
            else:
                self.wfile.write(password.setHTML())
            return

        #End session management. 
        #The following code should only be executed when the user has passed authentication!

        if (not getPages.apiIsInit):
            error = getPages.initApi();

            if (error):
                self.wfile.write(error)
                return
                
        if self.path.startswith("/inbox") or self.path == "/":
            self.wfile.write(getPages.inbox())

        elif self.path.startswith("/outbox"):
            self.wfile.write(getPages.outbox())

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
                
            self.wfile.write(getPages.composeMsg(toAddress, subject, text))

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
                self.wfile.write(page.getPage())
                return

            self.wfile.write(getPages.sendMsg(toAddress, fromAddress, subject, text, broadcast))

        elif self.path.startswith("/subscriptions"):
            self.wfile.write(getPages.subscriptions())

        elif self.path.startswith("/unsubscribe"):
            query = parseQuery(self.path)

            try:
                addr = query["addr"][0]
                getPages.unsubscribe(addr)
            except:
                pass

            self.wfile.write(getPages.subscriptions())

        elif self.path.startswith("/subscribe"):
            query = parseQuery(self.path)

            try:
                addr = query["addr"][0]
                label = query["label"][0]
                getPages.subscribe(addr, label)
            except:
                pass

            self.wfile.write(getPages.subscriptions())

        elif self.path.startswith("/addressbook"):
            self.wfile.write(getPages.addressBook())

        elif self.path.startswith("/addaddress"):
            query = parseQuery(self.path)

            try:
                addr = query["addr"][0]
                label = query["label"][0]
                getPages.addAddressBookEntry(addr, label)
            except:
                pass

            self.wfile.write(getPages.addressBook())

        elif self.path.startswith("/deladdress"):
            query = parseQuery(self.path)

            try:
                addr = query["addr"][0]
                getPages.delAddressBookEntry(addr)
            except:
                pass

            self.wfile.write(getPages.addressBook())

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
            html.addLine("<h1>404 - Not found</h1>")
            self.wfile.write(html.getPage())
