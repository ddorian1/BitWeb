from os import linesep, path, urandom
from hashlib import sha256
from htmlTmpl import HTMLPage

def set(password):
    salt = urandom(5).encode('base64').strip()
    passHash = sha256(salt + password).hexdigest()

    passFile = open("password", "wb")
    passFile.write(salt + linesep + passHash)
    passFile.close()
    
def isSet():
    if path.exists("password"):
        return True
    else:
        return False

def isCorrect(password):
    if not path.exists("password"):
        return False

    passFile = open("password", "rb")
    salt = passFile.readline()[:-1]
    passHash = passFile.readline()
    if passHash[-1] == "\n":
        passHash = passHash[:-1]
    passFile.close()

    if passHash == sha256(salt + password).hexdigest():
        return True
    else:
        return False

def setHTML():
    page = HTMLPage()

    page.addLine("<h1>Set password</h1>", False)
    page.addLine("<form action='setpwd' method='get'>", False)
    page.addLine("<input type='password' name='pwd' id='focus' />")
    page.addLine("<input type='submit' class='button' value='Set password' />", False)

    return page.getPage()

def enterHTML():
    page = HTMLPage()

    page.addLine("<h1>Login</h1>", False)
    page.addLine("<form action='pwd' method='get'>", False)
    page.addLine("<input type='password' name='pwd' id='focus' />")
    page.addLine("<input type='submit' class='button' value='Login' />", False)

    return page.getPage()
