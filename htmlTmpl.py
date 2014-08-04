header = """
<!DOCTYPE html>
<html>
<head>
<title>Bitmessage</title>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<meta name="viewport" content="width=device-width"; />

<style>
body {
    color: #2B2B2B;
    background-color: #FDFDFD;
    text-align: center;
    line-height: 1.5;
}

a, input.button, select {
    white-space: nowrap;
    color: #FDFDFD;
    background-color: #2B2B2B;
    text-decoration: none;
    font-weight: bold;
    padding: 2px;
    margin-right: 4px;
    border: none;
} 

a.menu {
    padding: 5px;
    margin: 5px;
    line-height: 2.5;
    font-size: large;
}

input {
    margin-right: 4px;
}

div {
    text-align: left;
}

div.msgHeaderRead {
    background-color: #A0A0A0;
    padding: 5px;
}

div.msgHeaderUnread {
    color: #EDEDED;
    background-color: #2B2B2B;
    font-weight: bold;
    padding: 5px;
}

div.msgText {
    background-color: #FDFDFD;
    padding: 5px;
    line-height: 1;
}

div.msgBody, div.addrbookentry, div.subscription {
    background-color: #C6C6C6;
    padding: 5px;
}

div.label {
    font-weight: bold;
}

form {
    line-height: 2;
}

hr {
    color: #2B2B2B;
    background-color: #2B2B2B;
    height: 4px;
    border: none;
}

</style>

<script type="text/javascript">
function callback(url, params) {
    if (window.XMLHttpRequest) {
       http = new XMLHttpRequest();
    } else if (window.ActiveXObject) {
       http = new ActiveXObject("Microsoft.XMLHTTP");
    }
    if (http != null) {
       http.open("GET", url + "?" + params, true);
       http.send(null);
    }
}

function markRead(id) {
    header = document.getElementById("H-" + id);
    if (header.className.match(/(?:^|\s)msgHeaderUnread(?!\S)/)) {
        header.className = 'msgHeaderRead';
        callback("markread", "msgid=" + id);
    }
}

function markUnread(id) {
    header = document.getElementById("H-" + id);
    if (header.className.match(/(?:^|\s)msgHeaderRead(?!\S)/)) {
        header.className = 'msgHeaderUnread';
        callback("markunread", "msgid=" + id);
    }
}

function delMsg(id) {
    callback("delmsg", "msgid=" + id);
    document.getElementById("H-" + id).style.display = 'none';
    document.getElementById(id).style.display = 'none';
}

function delSentMsg(id) {
    callback("delsentmsg", "msgid=" + id);
    document.getElementById("H-" + id).style.display = 'none';
    document.getElementById(id).style.display = 'none';
}

function ShowHideDiv(id) {
    obj = document.getElementById(id);
    if(obj.style.display == 'none') {
        obj.style.display = 'block';
        markRead(id);
    } else {
        obj.style.display = 'none';
    }
}

function HideMessages() {
    obj = document.getElementsByClassName("msgBody");
    for (i in obj) {
        if(obj[i].style != undefined) {
            obj[i].style.display = 'none';
        }
    }
}

function broadcastMsg(brd) {
    document.getElementById("to").disabled = brd;
}

</script>

</head>

<body>
    <a href="inbox" class="menu">Inbox</a>
    <a href="outbox" class="menu">Outbox</a>
    <a href="composer" class="menu">New message</a>
    <a href="subscriptions" class="menu">Subscriptions</a>
    <a href="addressbook" class="menu">Address book</a>
    <a href="identities" class="menu">Your identities</a>
    <a href="logout" class="menu">Logout</a>
    <br />
<hr />
"""

footer = """
<script type="text/javascript">
if (document.getElementById("focus")) {
    document.getElementById("focus").focus();
}
HideMessages();
</script>
</body>
</html>
"""

class HTMLPage():
    def __init__(self):
        self.data = u""

    def addLine(self, line, withBr = True):
        self.data += line
        if withBr:
            self.data += u"<br />"
            self.data += u"\n"

    def getPage(self):
        page = header + self.data + footer
        return page.encode('utf-8')
