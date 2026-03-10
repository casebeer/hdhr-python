
import hdhr
from control import ControlClient
from discover import DiscoverClient
import fields
import pprint

import logging
logger = logging.getLogger(__name__)

DEFAULT_TUNER_COUNT = 2

class HdhrClient:
    def __init__(self, host, controlClient, discoverBindPort):
        self.controlClient = controlClient
        self.discoverBindPort = discoverBindPort
        self._host = None
        self.host = host

    @classmethod
    async def create(cls, host, controlPort=65001, discoverPort=65001):
        return cls(
            host=host,
            controlClient=ControlClient(host, port=controlPort),
            discoverBindPort=discoverPort,
        )

    async def discoverClient(self):
        return await DiscoverClient.create(bind_port=self.discoverBindPort)

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, host):
        '''Setter to update host on both controlClient'''
        self._host = host
        if self.controlClient:
            self.controlClient.host = host

    async def get(self, endpoint):
        '''Control protocol get request'''
        return await self.controlClient.get(endpoint)

    async def set(self, endpoint, value):
        '''Control protocol get request'''
        return await self.controlClient.set(endpoint, value)

    async def getAllFields(client):
        data = {}
        tunerCount = DEFAULT_TUNER_COUNT

        for field in fields.ControlFields:
            data.update(await client.get(field.value))

        discover = await client.discoverOne()

        if discover:
            tunerCount = discover.get('TUNER_COUNT', DEFAULT_TUNER_COUNT)
            data.update(discover)

        # n.b. need to get number of tuners via Discovery API or HTTP API /discover.json
        for tunerNumber in range(tunerCount):
            for field in fields.TunerFields:
                data.update(await client.get(field.value.format(tunerNumber=tunerNumber)))
        return data

    async def discover(self, maxcount=0):
        '''Discover protocol request for all matching devices'''
        # n.b. DiscoverClient instances are only good for one discovery attempt, create a new one
        # each time
        discoverClient = await self.discoverClient()
        discoverClient.sendDiscover(self.host)
        async for reply in discoverClient.discoverReplies(maxcount=maxcount):
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

    async def discoverDevice(self, deviceId):
        host = None
        discoverClient = await self.discoverClient()
        # we are seeking anywhere on the network.... but if we got a --host as well, use that
        # This is a bit counterintuitive, but we might want to "search" for a device via e.g. a
        # custom multicast group, e.g. a discovery protocol proxy, etc.
        #
        # Note on confusing meaning of HdhrClient.host:
        # This method will most often be used to _set_ the self.host based on the discovery replies;
        # if self.host is already set, BEFORE we're called, it refers to the *discovery target
        # addresses*, while after we're called, presumably our caller will re-set our self.host to
        # refer to the *discovered target device* that we return.
        #
        # TODO: Change DiscoverClient API to clarify this; we may want a custom multicast group,
        # proxy host, etc.
        discoverClient.sendDiscover(self.host)
        async for reply in discoverClient.discoverReplies():
            if reply.get('DEVICE_ID') == deviceId:
                logger.debug(f"Discovered device with DEVICE_ID {deviceId} on local network...")
                host = reply.get('hostname')

                if host is not None:
                    logger.debug(f"Parsed hostname {host} from {deviceId}'s BASE_URL.")
                else:
                    logger.error(f"Unable to parse hostname from BASE_URL despite finding "
                                  f"matching DEVICE_ID '{reply.get('DEVICE_ID')}. Device data:\n'"
                                  f"{pprint.pformat(reply)}")

        if host is None:
            logger.info(f"Unable to find host for DEVICE_ID {deviceId} to a with discovery API")

        return host
