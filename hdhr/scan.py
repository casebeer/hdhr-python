'''
Perform a legacy client-managed channel scan

Intended for "legacy" devices which cannot perform a channel scan and store lineup data on-device,
i.e. HDHR3 devices and earlier. Any device which supports `set /lineup/scan start` or the
http://<device ip>/lineup.json HTTP endpoint should not need this manual channel scan.
'''

import logging
import asyncio
import pprint
import collections
import json
import urllib.request
import re
import time

from dataclasses import dataclass, asdict
from typing import Optional, List

from .tuning import TunerStatus
from . import __version__, __user_agent_name__, __url__

logger = logging.getLogger(__name__)

# variables for use in User-Agent string construction
PROJECT_NAME=__user_agent_name__
PROJECT_VERSION=__version__
PROJECT_URI=__url__

# Documented channel maps
# us-bcast
# us-cable
# us-hrc
# us-irc
# au-bcast
# au-cable
# eu-bcast
# eu-cable
# tw-bcast
# tw-cable
#

'''
SCANNING: 497000000 (us-bcast:18)
LOCK: 8vsb (ss=77 snq=59 seq=100)
TSID: 0x07DF
PROGRAM 3: 63.1 ESTRETV
PROGRAM 4: 63.2 MYSTERY
PROGRAM 6: 63.4 NTD
PROGRAM 7: 63.5 NTDTV
PROGRAM 8: 63.6 JTV
PROGRAM 9: 63.7 ALIENTO
PROGRAM 11: 63.9 KCBN
PROGRAM 12: 63.10 WDNJ
'''

'''
hdhomerun_config ... scan 0 output:
...
SCANNING: 617000000 (us-bcast:38)
LOCK: none (ss=58 snq=0 seq=0)
SCANNING: 605000000 (us-bcast:36)
LOCK: 8vsb (ss=89 snq=89 seq=100)
TSID: 0x086D
PROGRAM 1: 2.1 WCBS-HD
PROGRAM 2: 2.2 STARTTV
PROGRAM 3: 2.3 DABL
PROGRAM 4: 2.4 365BLK
PROGRAM 5: 2.5 COMET
PROGRAM 6: 21.2 CREATE
...
'''


CHANNELS = {
    "us-bcast": range(2, 37), # ch2 through ch36 valid in US-BCAST post-2020
    #"us-bcast": range(18, 30),
    #"us-bcast": range(20, 22),
}

@dataclass
class VChannel:
    rfChannel: int
    frequency: int
    modulation: str
    programNumber: int
    tsid: int
    vChannel: str
    vName: str = ''
    signalStrength: Optional[int] = None
    signalQuality: Optional[int] = None

class OptionalFields:
    def to_dict(self):
        '''Return serializable dict, skipping any fields set to None'''
        return { k:v for k,v in asdict(self).items() if v is not None }

@dataclass
class LineupProgram(OptionalFields):
    '''Serializer for lineup.json?tuning compatibility'''
    GuideNumber: str
    GuideName: str
    URL: Optional[str] = None # not optional

    Frequency: Optional[int] = None
    Modulation: Optional[str] = None
    RFChannel: Optional[int] = None # not in lineup.json

    TransportStreamID: Optional[int] = None
    ProgramNumber: Optional[int] = None

    VideoCodec: Optional[str] = None
    AudioCodec: Optional[str] = None

    SignalStrength: Optional[int] = None
    SignalQuality: Optional[int] = None

    HD: Optional[int] = None
    Favorite: Optional[int] = None

    @classmethod
    def fromVChannel(cls, vChannel):
        hd = 1 if re.search("HD$", vChannel.vName) else None
        return cls(
            GuideNumber=vChannel.vChannel,
            GuideName=vChannel.vName,

            #URL=,

            Frequency=vChannel.frequency,
            Modulation=vChannel.modulation,
            RFChannel=vChannel.rfChannel, # non-standard

            TransportStreamID=vChannel.tsid,
            ProgramNumber=vChannel.programNumber,

            #VideoCodec=vChannel.,
            #AudioCodec=vChannel.,

            SignalStrength=vChannel.signalStrength,
            SignalQuality=vChannel.signalQuality,

            HD=hd,
            #Favorite=vChannel.,
        )

@dataclass
class ScanProgram(OptionalFields):
    '''Serializer for api.hdhomerun.com/devices/sync?LegacyChannelScan=1 uploads'''
    Frequency: int
    Modulation: str
    TransportStreamID: int
    ProgramNumber: int
    VctNumber: str
    VctName: str
    HD: Optional[int] = None

    @classmethod
    def fromVChannel(cls, vChannel):
        hd = 1 if re.search("HD$", vChannel.vName) else None
        return cls(
            Frequency=vChannel.frequency,
            Modulation=vChannel.modulation,
            TransportStreamID=vChannel.tsid,
            ProgramNumber=vChannel.programNumber,
            VctNumber=vChannel.vChannel,
            VctName=vChannel.vName,
            HD=hd,
        )

@dataclass
class ChannelScan:
    deviceId: str
    lineup: List[VChannel]

    def scanUploadJson(self,indent=0):
        return json.dumps(
            {
                "Lineup": [ScanProgram.fromVChannel(vChannel).to_dict() for vChannel in self.lineup],
                "DeviceID": self.deviceId,
            },
            indent=indent,
        )

    def json(self,indent=0):
        return json.dumps(self.to_dict(), indent=indent)

    def to_dict(self):
        return {
            "lineup": [LineupProgram.fromVChannel(vChannel).to_dict() for vChannel in self.lineup],
            "deviceId": self.deviceId,
        }


class ScanManager:
    channelmap = "us-bcast"
    tuner = '/tuner1'

    def __init__(self, client):
        self.client = client
        self.channelScan = None

    '''
    {'/tuner0/streaminfo': '3: 49.1 WEDW-1\n'
                       '4: 43.1 STORY\n'
                       '6: 43.3 MeTV\n'
                       '7: 43.4 TOONS\n'
                       '10: 43.2 MeTV+\n'
                       '15: 43.12 EMLW\n'
                       'tsid=0x01F7\n'}
    '''
    async def scan(self, channels: list=None):
        # TODO: retrieve channelmap from device
        # TODO: determine valid rfChannel and/or rfFrequency ranges for channelmaps

        if channels is None or len(channels) == 0:
            channels = CHANNELS[self.channelmap]

        startTime = time.time()
        self.channelScan = await self.rfScan(channels)
        duration = time.time() - startTime
        logging.info(f"Channel scan completed. Found {len(self.channelScan.lineup)} channels "
                     f"in {round(duration, 1)} seconds.")
        return {"lineup": self.channelScan.to_dict()}

    async def upload(self, channels: list=None, apiBase=None, dryRun=False):
        if not self.channelScan:
            await self.scan(channels)

        ScanUploadClient.upload(self.channelScan, self.deviceAuth, apiBase=apiBase, dryRun=dryRun)

        return {"lineup": self.channelScan}

    async def rfScan(self, rfChannels: list[int]) -> ChannelScan:
        lineup = []

        discover = await self.client.discoverOne() # target host from HdhrClient.host
        self.deviceId = discover['DEVICE_ID']
        self.deviceAuth = discover['DEVICE_AUTH_STR']

        for rfChannel in rfChannels:
            logger.info(f"SCANNING: _ ({self.channelmap}:{rfChannel})")
            await self.client.tune(self.tuner, rfChannel)

            tunerStatus: TunerStatus = await self.client.tunerStatus(self.tuner)

            tsid = None
            if tunerStatus.locked:
                tsid, programs = await self.client.streaminfo(self.tuner)

                if tsid is None:
                    # streaminfo() has already retried, bail out
                    logger.warn(f"Unable to get streaminfo after getting tuning lock on "
                                f"ch{rfChannel}. Skipping channel.")
                    continue

                logger.info(f"TSID: 0x{tsid:04X}")
                for programData in programs:

                    programNumber = programData.get("programNumber")
                    vChannel = programData.get("vChannel")
                    vName = programData.get("vName")

                    logger.info(f"PROGRAM {programNumber}: {vChannel} {vName}")

                    program = VChannel(
                        rfChannel=rfChannel,
                        frequency=tunerStatus.lockedFrequency,
                        modulation=tunerStatus.lockedModulation,
                        tsid=tsid,
                        programNumber=programNumber,
                        vChannel=vChannel,
                        vName=vName,
                        signalStrength=tunerStatus.signalStrengthPercent,
                        signalQuality=tunerStatus.modulationErrorRatioSnqPercent,
                    )
                    lineup.append(program)

        channelScan = ChannelScan(deviceId=self.deviceId, lineup=lineup)
        return channelScan


'''
{
  "Frequency": 593000000,
  "VctName": "ION",
  "ProgramNumber": 3,
  "VctNumber": "31.1",
  "TransportStreamID": 2169,
  "Modulation": "8vsb"
},
'''


class ScanUploadClient:
    apiBase = "https://api.hdhomerun.com"
    #apiBase = "http://localhost:8001"
    apiEndpointTemplate = "/device/sync?LegacyChannelScan=1&DeviceAuth={deviceAuth}"
    userAgent= "{projectName}/{projectVersion} {projectUri}".format(
        projectName=PROJECT_NAME,
        projectVersion=PROJECT_VERSION,
        projectUri=PROJECT_URI,
    )

    @classmethod
    def upload(cls, scan, deviceAuth, apiBase=None, dryRun=False):
        apiBase = apiBase if apiBase is not None else cls.apiBase
        apiUriTemplate = f"{apiBase}{cls.apiEndpointTemplate}"
        apiUri = apiUriTemplate.format(deviceAuth=deviceAuth)
        if len(scan.lineup) == 0:
            raise Exception("Cannot upload empty channel scan. Zero channels found.")
        if dryRun:
            logger.info("Legacy channel scan dry-run: "
                        f"would upload {len(scan.lineup)} channels to {apiBase}")
            #print(scan.scanUploadJson(indent=2))
            return
        else:
            logger.info(
                f"Uploading channel scan data ({len(scan.lineup)} channels) to {apiBase}...")

        req = urllib.request.Request(
            apiUri,
            method="POST",
            data=scan.scanUploadJson().encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                #"Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": cls.userAgent,
            },
        )
        with urllib.request.urlopen(req) as response:
            logger.info(response)
            logger.info(response.geturl())
            logger.info(response.status)
            logger.info(response.headers)
            logger.info(response.read().decode('utf8'))
