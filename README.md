BitWeb
======

BitWeb should be a WebUI for PyBitmessage (or any other bitmessage client that implements the api).
It can be used to run bitmessage on your own server and access it easily from wherever you are.

This is in very early development, USE AT YOUR OWN RISK!

This should already work:

- Read messages
- Write messages (no broadcast at the moment)
- Manage your subscriptions
- Use the address book

What's not implementet yet:

- Manage your addresses
- Chans

To use it, just download the files to your sever, set the port you want to use in bitweb.py and run it.
BitWeb will try to read the api settings from PyBittmessage 'keys.dat' file.
You will be promted to set a password at the first visit of the site. If you wish to set a new one, just delete the file 'password' in BitWeb's directory and you will be prompted again.

I strongly recommend to use SSL. To do so, you need to set the path to your SSL certificat and keyfile in bitweb.py.
Make shure to select the correct protocoll in your browser (http:// or https://), else you will not see anything at all.

BitWeb requires python 2 without any additional packages.
