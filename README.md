BitWeb
======

BitWeb should be a WebUI for PyBitmessage (or any other bitmessage client that implements the api).
It can be used to run bitmessage on your own server and access it easily from wherever you are.

This is an early development version, USE AT YOUR OWN RISK!

What should already work:

* Read messages
* Write messages
* Manage your subscriptions
* Manage your addresses (Can't yet create deterministic addresses)
* Use the address book

What's not implemented yet:

* Chans

To use it, just download the files to your sever, set the port you want to use in bitweb.py. You have to set up the api in PyBitmessage's keys.dat file (See https://bitmessage.org/wiki/API_Reference) and run bitweb.py as the same user as PyBitmessage.
BitWeb will try to read the api settings from PyBitmessage keys.dat file.
You will be prompted to set a password at the first visit of the site. If you wish to set a new one, just delete the file 'password' in BitWeb's directory and you will be asked again.

I strongly recommend to use SSL. To do so, you need to set the path to your SSL certificate and keyfile in bitweb.py. If you don't want to use SSL, you must disable it by setting SSL to False in bitweb.py.
Make sure to select the correct protocol in your browser (http:// or https://), else you will most likely not see anything at all.

BitWeb requires python 2 without any additional packages.

![Screenshot](screenshot.png?raw=true "Screenshot")
