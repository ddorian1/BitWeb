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
    if (not path.exists("password")) or (not password):
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
    page.addLine("<form action='setpwd' method='post' enctype='multipart/form-data'>", False)
    page.addLine("<input type='password' name='pwd' id='focus' />")
    page.addLine("<input type='submit' class='button' value='Set password' />", False)

    return page.getPage()

def enterHTML(wrongPassword = False):
    page = HTMLPage()

    page.addLine("<h1>Login</h1>", False)
    if wrongPassword:
        page.addLine("Password not correct!")
    page.addLine("<form action='pwd' method='post' enctype='multipart/form-data'>", False)
    page.addLine("<input type='password' name='pwd' id='focus' />")
    page.addLine("<input type='submit' class='button' value='Login' />", False)

    return page.getPage()
