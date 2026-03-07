
import hdhr
from control import ControlClient
from discover import DiscoverClient
import fields

import logging
logger = logging.getLogger(__name__)

DEFAULT_TUNER_COUNT = 2

class HdhrClient:
    def __init__(self, host, controlClient, discoverClient):
        self.host = host
        self.controlClient = controlClient
        self.discoverClient = discoverClient

    @classmethod
    async def create(cls, host, controlPort=65001, discoverPort=65001):
        return cls(
            host=host,
            controlClient=ControlClient(host, port=controlPort),
            discoverClient=await DiscoverClient.create(bind_port=discoverPort),
        )

    def get(self, endpoint):
        '''Control protocol get request'''
        return self.controlClient.get(endpoint)

    def set(self, endpoint, value):
        '''Control protocol get request'''
        return self.controlClient.set(endpoint, value)

    async def getAllFields(client):
        data = {}
        tunerCount = DEFAULT_TUNER_COUNT

        for field in fields.ControlFields:
            data.update(client.get(field.value))

        discover = await client.discoverOne()

        if discover:
            tunerCount = discover.get('TUNER_COUNT', DEFAULT_TUNER_COUNT)
            data.update(discover)

        # n.b. need to get number of tuners via Discovery API or HTTP API /discover.json
        for tunerNumber in range(tunerCount):
            for field in fields.TunerFields:
                data.update(client.get(field.value.format(tunerNumber=tunerNumber)))
        return data

    async def discover(self, maxcount=0):
        '''Discover protocol request for all matching devices'''
        self.discoverClient.sendDiscover(self.host)
        async for reply in self.discoverClient.discoverReplies(maxcount=maxcount):
            yield reply

    async def discoverOne(self):
        '''
        Get discover data via UDP discover protocol for only a single device

        Most useful if self.host is the IP address of a specific device, and we just want to
        retrieve the device ID and auth token.
        '''
        async for reply in self.discover():
            # break out of loop after first reply
            return reply
        logger.warn("No discovery replies received")
        return {}
