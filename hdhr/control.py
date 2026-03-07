
import socket
import pprint
import os

import hdhr
import fields

import logging
logger = logging.getLogger(__name__)

MAX_PACKET_LENGTH = 4096 # octets

class ControlClient:
    '''
    HDHomerun "Control Protocol" client

    The control protocol uses "GETSET" requests over TCP port 65001.

    Get requests specify a GETSET_NAME payload field with the value set to the
    parameter being requested.

    Set request specify both a GETSET_NAME field and a GETSET_VALUE field. The
    values of each are the parameter name to overwrite and the value to write,
    respectively.

    Both get and set requests respond with GETSET_NAME and GETSET_VALUE fields
    providing the value of the parameter from the server.

    Note that while the packet and payload classes deal in NUL terminated raw byte
    strings, this client handles unicode strings and encodes/decodes assuming all
    data is UTF-8.
    '''
    encoding="utf-8"

    def __init__(self, host, port=65001):
        self.host = host
        self.port = port
        self.addrInfo: list = []

    def request(self, packet: hdhr.Packet) -> hdhr.Packet:
        packetBytes = packet.unparse()
        logger.debug(f"-> {packetBytes.hex()}")

        responseBytes = self.requestBytes(packetBytes)

        if responseBytes is None:
            logger.error("Unable to complete Control API request.")
            return hdhr.Packet.invalid()

        return hdhr.Packet.parse(responseBytes)

    def requestBytes(self, packetBytes: bytes) -> bytes:
        if len(self.addrInfo) == 0:
            # cached dual stack DNS lookup
            self.addrInfo = socket.getaddrinfo(self.host, self.port, type=socket.SOCK_STREAM, family=socket.AF_UNSPEC)

        with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0) # disable V6ONLY flag
            # send to first successful addrInfo entry
            #for family, type, proto, canonname, sockaddr in self.addrInfo:
            while len(self.addrInfo) > 0:
                family, type, proto, canonname, sockaddr = self.addrInfo[0]
                if family == socket.AF_INET:
                    v4, port = sockaddr
                    # create mapped ipv4 address for sending on dualstack socket
                    sockaddr = (f"::ffff:{v4}", port, 0, 0)
                try:
                    logger.debug(f"Sending packet to {sockaddr}")
                    sock.connect(sockaddr)
                except socket.error as e:
                    # try next
                    logger.debug(f"{e} while connecting to {sockaddr}, trying next IP...")
                    # discard the unusable addrInfo entry
                    # n.b. getaddrinfo will be a short list – O(n) copy for this popleft
                    self.addrInfo.pop(0)
                    continue

                try:
                    sock.sendall(packetBytes)

                    responseBytes = sock.recv(MAX_PACKET_LENGTH)
                    logger.debug(f"<- {responseBytes.hex()}")

                    return responseBytes
                except socket.error as e:
                    logger.error(f"{e} while sending data to {sockaddr}")
                    # clear addrInfo after error
                    self.addrInfo = []
                    return
            else:
                # we've run out of addresses to try, we're unable to connect
                logger.error(f"Unable to connect to {self.host} on TCP port {self.port}.")


    def set(self, requestFieldName: str, value: str):

        # Construct a "set" payload with both a parameter name and a parameter value specified
        payload = hdhr.Payload(
            fields=[
                hdhr.PayloadField(
                    tag=hdhr.PayloadTag.GETSET_NAME,
                    value=bytes(requestFieldName + "\0", encoding=self.encoding),
                ),
                hdhr.PayloadField(
                    tag=hdhr.PayloadTag.GETSET_VALUE,
                    value=bytes(value + "\0", encoding=self.encoding),
                ),
            ]
        )

        packet = hdhr.Packet(
            packetType=hdhr.PacketType.GETSET_REQ,
            payload=payload,
        )

        response: hdhr.Packet = self.request(packet)
        return self.processResponse(response, requestFieldName)

    def get(self, requestFieldName: str):

        # Construct a "get" payload with only a parameter name specified
        payload = hdhr.Payload(
            fields=[hdhr.PayloadField(
                tag=hdhr.PayloadTag.GETSET_NAME,
                value=bytes(requestFieldName + "\0", encoding=self.encoding),
            )]
        )

        packet = hdhr.Packet(
            packetType=hdhr.PacketType.GETSET_REQ,
            payload=payload,
        )

        response = self.request(packet)

        return self.processResponse(response, requestFieldName)

    def processResponse(self, response: hdhr.Packet, requestFieldName):
        name = None
        value = None
        logger.debug(response)
        responseFields = {}
        for field in response.payload.fields:
            if field.tag == hdhr.PayloadTag.GETSET_NAME:
                name = field.value[:-1].decode(self.encoding)
            elif field.tag == hdhr.PayloadTag.GETSET_VALUE:
                value = field.value[:-1].decode(self.encoding)
                #pprint.pprint({ name: value })
                responseFields[name] = value
                name, value = None, None
            elif field.tag == hdhr.PayloadTag.ERROR_MESSAGE:
                value = field.value[:-1].decode(self.encoding)
                logger.error(f"ERROR: {value} {requestFieldName}")
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
        data.update(client.get(field.value))

    # n.b. need to get number of tuners via Discovery API or HTTP API /discover.json
    for tunerNumber in (0, 1):
        for field in fields.TunerFields:
            data.update(client.get(field.value.format(tunerNumber=tunerNumber)))
    pprint.pprint(data)

    # restart device
    #pprint.pprint(client.set(fields.ControlFields.SYS_RESTART, "self"))
