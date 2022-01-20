import socket
import time
import gc
import ujson

#TODO Buscar una mejor manera de asegurar esto

#This is the API connection info
SERVER_CONN_IPPORT = ('192.168.4.2', 8000)


'''
Sends an HTTP request to the API for saving the data.
'''
def send_to_api(source_address, filename, bytes_content):
    #print("send_to_api")
    result = False
    s = socket.socket()
    try:

        s.setblocking(True)
        addr = socket.getaddrinfo(SERVER_CONN_IPPORT[0], SERVER_CONN_IPPORT[1])[0][-1]
        s.connect(addr)

        route = "/source/{}/{}".format(source_address, filename)
        content = ujson.dumps({"content": bytes_content.decode('utf-8')})
        content_length = len(content)
        httpreq = 'POST {} HTTP/1.1\r\nHost: 192.168.4.2\r\nConnection: close\r\nAccept: */*\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\r\n{}\r\n'.format(route, content_length, content)
        #print(httpreq)

        s.send(httpreq)
        raw_response = s.recv(10000).decode('utf-8')

        #Extracción de la respuesta JSON
        response_json = ujson.loads(raw_response.split("\r\n\r\n")[1].replace('\"', '"'))

        #print(response_json)
        if response_json['source_address'] == source_address and response_json['filename'] == filename:
            result = True
        s.close()
    except Exception as e:
        print("socket-error", e) #Si no pudo, da igual, al no haber sido enviado a la siguiente vez lo intentará
    finally:
        s.close()

    return result

'''
Retrieves the MAC list of the buoys' senders. It performs an HTTP request.
'''
def request_sender_mac_list():
    sender_mac_list = []
    try:
        s = socket.socket()
        s.setblocking(True)
        addr = socket.getaddrinfo(SERVER_CONN_IPPORT[0], SERVER_CONN_IPPORT[1])[0][-1]
        s.connect(addr)

        route = "/source/sender_mac_list"
        httpreq = 'GET {} HTTP/1.1\r\nHost: 192.168.4.2\r\nConnection: close\r\nAccept: */*\r\n\r\n'.format(route)
        #print(httpreq)

        s.send(httpreq)
        raw_response = s.recv(10000).decode('utf-8')

        #Extracción de la respuesta JSON
        response_json = ujson.loads(raw_response.split("\r\n\r\n")[1].replace('\"', '"'))

        #print(response_json)
        if len(response_json['sender_mac_list']) > 0:
            sender_mac_list = response_json['sender_mac_list']
        s.close()
    except Exception as e:
        print(e) #Si no pudo, da igual, al no haber sido enviado a la siguiente vez lo intentará

    return sender_mac_list
