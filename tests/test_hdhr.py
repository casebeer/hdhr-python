
import logging
import unittest
from hdhr import hdhr

logger = logging.getLogger(__name__)

class TestPayloadField(unittest.TestCase):
    lengthTestVectors = [
        (120, bytes.fromhex('78')),
        (250, bytes.fromhex('fa01')),
    ]
    def test_writeLength(self):
        for length, expectedBytes in self.lengthTestVectors:
            lengthBytes = hdhr.PayloadField.writeLength(length)
            self.assertEqual(lengthBytes, expectedBytes)

    def test_readLength(self):
        for expectedLength, lengthBytes in self.lengthTestVectors:
            length = hdhr.PayloadField.readLength(lengthBytes)
            self.assertEqual(length, expectedLength)

class TestPacket(unittest.TestCase):
    errorResponse = bytes.fromhex(
        "0005002205204552524f523a206d616c666f726d65642067657473657420"
        "726571756573740037494141") # captured from HDTC-2US
    versionResponse = bytes.fromhex(
        "0005001a030d2f7379732f76657273696f6e000409323032353036323300"
        "053b1257") # captured from HDTC-2US
    discoverResponse = bytes.fromhex(
        "000300690104000000012d04000000010204010203042b18313233343536"
        "3738393031323334353637383930313233342a15687474703a2f2f313932"
        "2e302e322e3132333a38301001022721687474703a2f2f3139322e302e32"
        "2e3132333a38302f6c696e6575702e6a736f6e67e72021") # generated

    def test_parseVersionResponse(self):
        packet = hdhr.Packet.parse(self.versionResponse)

        self.assertEqual(packet.packetType, hdhr.PacketType.GETSET_RPY)

        self.assertEqual(packet.payload.fields[0].tag, hdhr.PayloadTag.GETSET_NAME)
        self.assertEqual(packet.payload.fields[0].value, b"/sys/version\00")

        self.assertEqual(packet.payload.fields[1].tag, hdhr.PayloadTag.GETSET_VALUE)
        self.assertEqual(packet.payload.fields[1].value, b"20250623\00")

    def test_parseErrorResponse(self):
        packet = hdhr.Packet.parse(self.errorResponse)

        self.assertEqual(packet.packetType, hdhr.PacketType.GETSET_RPY)
        self.assertEqual(packet.payload.fields[0].tag, hdhr.PayloadTag.ERROR_MESSAGE)

    def test_parseDiscoveryResponse(self):
        logger.debug("Parsing discovery response packet...")
        packet = hdhr.Packet.parse(self.discoverResponse)

        logger.debug(packet)

        self.assertEqual(packet.packetType, hdhr.PacketType.DISCOVER_RPY)

        self.assertEqual(packet.payload.fields[0].tag, hdhr.PayloadTag.DEVICE_TYPE)
        self.assertEqual(packet.payload.fields[0].value, b"\00\00\00\01")

        self.assertEqual(packet.payload.fields[1].tag, hdhr.PayloadTag.MULTI_TYPE)
        self.assertEqual(packet.payload.fields[1].value, b"\00\00\00\01")

        self.assertEqual(packet.payload.fields[2].tag, hdhr.PayloadTag.DEVICE_ID)
        self.assertEqual(packet.payload.fields[2].value, b"\01\02\03\04")

        self.assertEqual(packet.payload.fields[3].tag, hdhr.PayloadTag.DEVICE_AUTH_STR)
        self.assertEqual(packet.payload.fields[3].value, b"123456789012345678901234")

        self.assertEqual(packet.payload.fields[4].tag, hdhr.PayloadTag.BASE_URL)
        self.assertEqual(packet.payload.fields[4].value, b"http://192.0.2.123:80")

        self.assertEqual(packet.payload.fields[5].tag, hdhr.PayloadTag.TUNER_COUNT)
        self.assertEqual(packet.payload.fields[5].value, b"\02")

        self.assertEqual(packet.payload.fields[6].tag, hdhr.PayloadTag.LINEUP_URL)
        self.assertEqual(packet.payload.fields[6].value,
            b"http://192.0.2.123:80/lineup.json")

    def test_unparseVersionResponse(self):
        packet = hdhr.Packet.parse(self.versionResponse)
        self.assertEqual(packet.unparse(), self.versionResponse)

    def test_unparseErrorResponse(self):
        packet = hdhr.Packet.parse(self.errorResponse)
        self.assertEqual(packet.unparse(), self.errorResponse)

    def test_unparseDiscoveryResponse(self):
        packet = hdhr.Packet.parse(self.discoverResponse)
        self.assertEqual(packet.unparse(), self.discoverResponse)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
