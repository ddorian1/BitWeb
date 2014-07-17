#!/usr/bin/env python2
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
SSLCrt = "path/to/yout.crt"
#Optional path to your CA certificat
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
