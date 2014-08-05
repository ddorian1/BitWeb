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

import socket
from SocketServer import BaseServer
from BaseHTTPServer import HTTPServer
import ssl
from requestHandler import myRequestHandler

#Port to use
PORT = 8000
#Interface to bind to
ADDR = "" 

#Set to True to use SSL
SSL = True
#Path to your SSL keyfile
SSLKey = "/path/to/your.key"
#Path to your SSL certfile
SSLCrt = "path/to/your.crt"
#Optional path to your CA certificate
SSLCACert = None

def main():
    try:
        server = HTTPServer((ADDR, PORT), myRequestHandler)
        if SSL:
            server.socket = ssl.wrap_socket(server.socket, certfile=SSLCrt, keyfile=SSLKey, ca_certs=SSLCACert, server_side=True)
        print 'Starting BitWeb, use CTRL+C to shut down...'
        server.serve_forever()
    except KeyboardInterrupt:
        print ''
        print '^C received, shutting down...'
        server.socket.close()

if __name__ == '__main__':
    main()
