
import socket
import hdhr

import os

HOST = os.environ.get('HOST')
PORT = int(os.environ.get('PORT', 65001))

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect((HOST, PORT))

    payload = hdhr.Payload(
        fields=[hdhr.PayloadField(
            tag=hdhr.PayloadTag.GETSET_NAME,
            value=bytearray("/sys/version\0", encoding="ascii"),
        )]
    )

    packet = hdhr.Packet(
        packetType=hdhr.PacketType.GETSET_REQ,
        payload=payload,
    )
    print("Sending")
    print(packet)

    sock.sendall(packet.unparse())
    data = sock.recv(2048)
    print("Received")
    print(data.hex())

    response = hdhr.Packet.parse(data)
    print(response)
