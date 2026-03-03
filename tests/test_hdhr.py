
import unittest
import hdhr

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
    errorResponse = bytes.fromhex("0005002205204552524f523a206d616c666f726d65642067657473657420726571756573740037494141")
    versionResponse = bytes.fromhex("0005001a030d2f7379732f76657273696f6e000409323032353036323300053b1257")

    def test_parseVersionResponse(self):
        packet = hdhr.Packet.parse(self.versionResponse)

        self.assertEqual(packet.packetType, hdhr.PacketType.HDHOMERUN_TYPE_GETSET_RPY)

        self.assertEqual(packet.payload.fields[0].tag, hdhr.PayloadTag.HDHOMERUN_TAG_GETSET_NAME)
        self.assertEqual(packet.payload.fields[0].value, b"/sys/version\00")

        self.assertEqual(packet.payload.fields[1].tag, hdhr.PayloadTag.HDHOMERUN_TAG_GETSET_VALUE)
        self.assertEqual(packet.payload.fields[1].value, b"20250623\00")

    def test_parseErrorResponse(self):
        packet = hdhr.Packet.parse(self.errorResponse)

        self.assertEqual(packet.packetType, hdhr.PacketType.HDHOMERUN_TYPE_GETSET_RPY)
        self.assertEqual(packet.payload.fields[0].tag, hdhr.PayloadTag.HDHOMERUN_TAG_ERROR_MESSAGE)

if __name__ == '__main__':
    unittest.main()
