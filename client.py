
import hdhr
from control import ControlClient
from discover import DiscoverClient

class HdhrClient:
    def __init__(self, host, controlClient, discoverClient):
        self.host = host
        self.controlClient = controlClient
        self.discoverClient = discoverClient

    @classmethod
    async def create(cls, host):
        return cls(
            host=host,
            controlClient=ControlClient(host),
            discoverClient=await DiscoverClient.create(),
        )

    def get(self, endpoint):
        '''Control protocol get request'''
        return self.controlClient.get(endpoint)

    def set(self, endpoint, value):
        '''Control protocol get request'''
        return self.controlClient.set(endpoint, value)

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
        async for reply in self.discover(maxcount=1):
            # break out of loop after first reply
            return reply
