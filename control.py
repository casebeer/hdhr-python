
import socket
import pprint
import os

import hdhr
import fields

HOST = os.environ.get('HOST')
PORT = int(os.environ.get('PORT', 65001))

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect((HOST, PORT))

    for requestField in fields.ControlFields:
        payload = hdhr.Payload(
            fields=[hdhr.PayloadField(
                tag=hdhr.PayloadTag.HDHOMERUN_TAG_GETSET_NAME,
                value=requestField.value,
            )]
        )

        packet = hdhr.Packet(
            packetType=hdhr.PacketType.HDHOMERUN_TYPE_GETSET_REQ,
            payload=payload,
        )
        #print("Sending")
        #print(packet)

        sock.sendall(packet.unparse())
        data = sock.recv(2048)
        #print("Received")
        #print(data.hex())

        name = None
        value = None
        response = hdhr.Packet.parse(data)
        #print(response)
        for field in response.payload.fields:
            if field.tag == hdhr.PayloadTag.HDHOMERUN_TAG_GETSET_NAME:
                name = field.value[:-1].decode('utf8')
            elif field.tag == hdhr.PayloadTag.HDHOMERUN_TAG_GETSET_VALUE:
                value = field.value[:-1].decode('utf8')
                pprint.pprint({ name: value })
                name, value = None, None
            elif field.tag == hdhr.PayloadTag.HDHOMERUN_TAG_ERROR_MESSAGE:
                value = field.value[:-1].decode('utf8')
                pprint.pprint({ "ERROR": f"{requestField.name} {value}" })
                value = None
            else:
                print(field.tag)
