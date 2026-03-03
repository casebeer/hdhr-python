
import socket
import pprint
import os

import hdhr
import fields

import logging
logger = logging.getLogger(__name__)

MAX_PACKET_LENGTH = 4096 # octets

class ControlClient:
    def __init__(self, host, port=65001):
        self.host = host
        self.port = port

    def request(self, packet):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.host, self.port))
            sock.sendall(packet.unparse())
            data = sock.recv(MAX_PACKET_LENGTH)
            return hdhr.Packet.parse(data)

    def set(self, requestField, value: str):
        payload = hdhr.Payload(
            fields=[
                hdhr.PayloadField(
                    tag=hdhr.PayloadTag.HDHOMERUN_TAG_GETSET_NAME,
                    value=requestField.value,
                ),
                hdhr.PayloadField(
                    tag=hdhr.PayloadTag.HDHOMERUN_TAG_GETSET_VALUE,
                    value=bytes(value + "\0", encoding="utf8"),
                ),
            ]
        )

        packet = hdhr.Packet(
            packetType=hdhr.PacketType.HDHOMERUN_TYPE_GETSET_REQ,
            payload=payload,
        )

        response = self.request(packet)
        return self.processResponse(response, requestField)

    def get(self, requestField):
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

        response = self.request(packet)

        return self.processResponse(response, requestField)

    def processResponse(self, response, requestField):
        name = None
        value = None
        #print(response)
        responseFields = {}
        for field in response.payload.fields:
            if field.tag == hdhr.PayloadTag.HDHOMERUN_TAG_GETSET_NAME:
                name = field.value[:-1].decode('utf8')
            elif field.tag == hdhr.PayloadTag.HDHOMERUN_TAG_GETSET_VALUE:
                value = field.value[:-1].decode('utf8')
                #pprint.pprint({ name: value })
                responseFields[name] = value
                name, value = None, None
            elif field.tag == hdhr.PayloadTag.HDHOMERUN_TAG_ERROR_MESSAGE:
                value = field.value[:-1].decode('utf8')
                #pprint.pprint({ "ERROR": f"{requestField.name} {value}" })
                logger.error(f"ERROR: {value} {requestField.name}")
                responseFields[name]: value
                value = None
            else:
                logger.error(f"UNHANDLED RESPONSE TAG: {field.tag.name}")
        return responseFields

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    host = os.environ.get('HOST')
    port = int(os.environ.get('PORT', 65001))

    client = ControlClient(host, port)

    data = {}
    for field in fields.ControlFields:
        data.update(client.get(field))
    # n.b. need to get number of tuners via Discovery API
    for field in fields.TunerFields:
        data.update(client.get(field))
    pprint.pprint(data)

    # restart device
    #pprint.pprint(client.set(fields.ControlFields.SYS_RESTART, "self"))
