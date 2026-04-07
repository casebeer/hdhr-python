
import asyncio

import hdhr
import tuning
from control import ControlClient
from discover import DiscoverClient
import fields
import pprint

import logging
logger = logging.getLogger(__name__)

DEFAULT_TUNER_COUNT = 2

class HdhrClient:
    tuningWaitSeconds = 0.5
    tuningRetries = 3
    streaminfoRetries = 6

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

    async def getFreeTuner(self):
        raise Exception('Not implemented')

    async def tune(self, tuner, rfChannel):
        '''
        Tune one of the device's tuners to the specified RF channel

        Must pass a specific tuner to use. Find a free tuner with HdhrClient.getFreeTuner().
        '''
        # logger.info(f"SCANNING: _ ({self.channelmap}:{rfChannel})")
        logger.info(f"SCANNING: _ (RF:{rfChannel})")
        # TODO: Use high level client
        result = await self.set(f"{tuner}/channel", str(rfChannel))
        await asyncio.sleep(self.tuningWaitSeconds)
        return result

    '''
    INFO:scan:SCANNING: _ (us-bcast:18)
    INFO:scan:LOCK: 8vsb (ss=78 snq=64 seq=0) us-bcast:18 497000000 Hz
    INFO:scan:TSID: 0x07DF
    INFO:scan:PROGRAM 3: 0 (no data)
    INFO:scan:PROGRAM 4: 0 (no data)
    INFO:scan:PROGRAM 6: 0 (no data)
    INFO:scan:PROGRAM 7: 0 (no data)
    INFO:scan:PROGRAM 8: 0 (no data)
    INFO:scan:PROGRAM 9: 0 (no data)
    INFO:scan:PROGRAM 11: 0 (no data)
    INFO:scan:PROGRAM 12: 0 (no data)
    '''
    async def streaminfo(self, tuner):
        '''
        Attempt to get streaminfo with retries

        Streaminfo lists the virtual channel numbers and names for the currently tuned RF channel.
        '''
        for retries in range(self.streaminfoRetries):
            tsid, programs = await self._streaminfoOnce(tuner)

            if tsid is None or len(programs) == 0 or programs[0].get("vChannel") == "0":
                # TSID should not be none if we have a tuner lock; we might just need a little
                # more time for the tuner to get the TSID and program data. Sleep one more wait
                # period and try again.

                #print(tsid, len(programs) == 0, programs)
                if retries < self.streaminfoRetries - 1:
                    logger.warn(f"Unable to read streaminfo, waiting before retrying...")
                tsid = None # mark the results as invalid
                await asyncio.sleep(self.tuningWaitSeconds)
                continue
            else:
                break
        return tsid, programs

    async def _streaminfoOnce(self, tuner):
        '''Attempt to get streaminfo once. No validation on output data'''
        streaminfo = await self.get(f"{tuner}/streaminfo")
        tsid = None
        programs = []
        for line in streaminfo.get(f"{tuner}/streaminfo").split("\n"):
            program, delim, programData = line.partition(": ")
            vChannel, _, vName = programData.partition(" ")
            if delim == ": ":
                # program info line
                programs.append({
                    "programNumber": int(program),
                    "vChannel": vChannel,
                    "vName": vName,
                })
            else:
                # no program info found, must be TSID line
                field, _, tsidString = line.partition("=")
                if field.lower() == "tsid":
                    tsid = int(tsidString, 16)

        return tsid, programs

    '''
    {'/tuner0/status': 'ch=auto:21 lock=8vsb ss=82 snq=79 seq=100 bps=0 pps=0'}
    {'/tuner0/debug': 'tun: ch=auto:21 lock=8vsb:515000000 ss=80 snq=76 seq=100 '
                      'dbg=-514/13110\n'
                      'dev: bps=19394080 resync=0 overflow=0\n'
                      'ts:  bps=19394080 te=0 crc=0\n'
                      'net: pps=0 err=0 stop=0\n'}
    '''
    async def checkTuning(self, tuner):
        '''
        Query the device's TCP API to get current tuner status with retries

        Tuning info is the "debug" data for the current RF channel.
        '''
        for retries in range(self.tuningRetries):
            tuning = await self._checkTuningOnce(tuner)

            lock = tuning["lock"]

            if lock is None:
                #if retries < self.tuningRetries - 1:
                #    logger.warn(f"Unable to get tuner lock, waiting before retrying...")

                await asyncio.sleep(self.tuningWaitSeconds)
                continue
            else:
                break

        requestedChannel = tuning["requestedChannel"]
        frequency = tuning["frequency"]
        ss, snq, seq = tuning["ss"], tuning["snq"], tuning["seq"]
        logger.info(f"LOCK: {lock} (ss={ss} snq={snq} seq={seq}) "
                    #f"{self.channelmap}:{requestedChannel} "
                    f"RequestedRF:{requestedChannel} "
                    f"{f'{frequency} Hz' if frequency else ''} ({retries+1} attempts)")
        return tuning

    async def _checkTuningOnce(self, tuner):
        '''Query the device's TCP API to get current tuner status'''
        #self.get(fields.TunerFields.DEBUG.value.format(self.tunerNumber))
        responseData = await self.get(f"{tuner}/debug") # already processed
        debugString = responseData[f"{tuner}/debug"]
        debug = tuning.parseTunerDebugString(debugString)

        tun = debug["tun"]

        lock, _, frequency = tun["lock"].partition(":")
        _, _, requestedChannel = tun["ch"].partition(":")
        ss, snq, seq = tun["ss"], tun["snq"], tun["seq"]

        return {
            'lock': None if lock == 'none' else lock,
            'frequency': int(frequency) if frequency else None,
            'requestedChannel': int(requestedChannel) if requestedChannel else None,
            'ss': int(ss) if ss else None,
            'snq': int(snq) if snq else None,
            'seq': int(seq) if seq else None,
        }
