
import collections
from dataclasses import dataclass

@dataclass
class TunerStatus:
    requestedChannel: int  # ch
    lockedModulation: str # lock=<>:xxx
    lockedFrequency: int # lock=xxx:<>
    signalStrengthPercent: int  # ss
    modulationErrorRatioSnqPercent: int  # snq
    symbolErrorQualityPercent: int  # seq
    bitsPerSecond: int = None  # bps, not present on HDTC
    packetsPerSecond: int = None  # pps, not present on HDTC

    @property
    def locked(self) -> bool:
        return self.lockedModulation is not None

    @classmethod
    def fromDebugString(cls, debugString):
        debug = parseTunerDebugString(debugString)

        tun = debug["tun"]

        lock, _, frequency = tun["lock"].partition(":")
        _, _, requestedChannel = tun["ch"].partition(":")

        ss = tun.get("ss", None)
        snq = tun.get("snq", None)
        seq = tun.get("seq", None)

        bps = tun.get("bps", None)
        pps = tun.get("pps", None)

        data = {
            'lock': None if lock == 'none' else lock,
            'frequency': int(frequency) if frequency else None,
            'requestedChannel': int(requestedChannel) if requestedChannel else None,
            'ss': int(ss) if ss else None,
            'snq': int(snq) if snq else None,
            'seq': int(seq) if seq else None,
        }

        return cls(
            requestedChannel=int(requestedChannel) if requestedChannel else None,
            lockedModulation=None if lock == 'none' else lock,
            lockedFrequency=int(frequency) if frequency else None,
            signalStrengthPercent=int(ss) if ss else None,
            modulationErrorRatioSnqPercent=int(snq) if snq else None,
            symbolErrorQualityPercent=int(seq) if seq else None,
            bitsPerSecond=int(bps) if bps else None,
            packetsPerSecond=int(pps) if pps else None,
        )


@dataclass
class DeviceStatus:
    bitsPerSecond: int
    resyncCount: int
    overflowCount: int


@dataclass
class TransportStreamStatus:
    bitsPerSecond: int  # bps
    transportErrorCount: int  # te
    crcErrorCount: int  # crc

    @classmethod
    def fromDebugString(self, debugString):
        debug = parseTunerDebugString(debugString)

        ts = debug["ts"]

        bps = tun.get("bps", None)
        te = tun.get("te", None)
        crc = tun.get("crc", None)

        return cls(
            bitsPerSecond=int(bps) if bps else None,
            transportErrorCount=int(te) if te else None,
            crcErrorCount=int(crc) if crc else None,
        )




@dataclass
class NetworkStatus:
    packetsPerSecond: int  # pps
    packetDropCount: int  # err, packets/TS frames dropped *before* transmission
    streamStopReason: str  # stop


def parseTunerDebugString(debugString):
    '''
    Parse /tuner<n>/debug output

    Definitions from https://www.silicondust.com/hdhomerun/hdhomerun_tech.pdf:

    Tuner status
    tun: ch=auto:21 lock=8vsb:515000000 ss=80 snq=76 seq=100 dbg=-514/13110
        ch - requested channel
        lock - modulation detected
        ss - signal strength
        snq - signal to noise quality (MER, modulation error ratio)
        seq - symbolic error quality (based on number of uncorrectable digital errors detected)
        bps - raw channel bits per second
        pps - packets per second sent through the network

    Device status
    dev: bps=19394080 resync=0 overflow=0

    Transport stream status
    ts:  bps=19394080 te=0 crc=0
        bps - bit per second
        te - transport error (uncorrectable reception) counter
        crc - crc error counter

    Network status
    net: pps=0 err=0 stop=0
        pps - packets per second
        err - packets or TS frames dropped
        stop - reason for stopping stream
    '''
    data = collections.defaultdict(lambda: collections.defaultdict(dict))
    for group in debugString.split("\n"):
        if group.strip():
            groupName, _, groupString = group.strip().partition(": ")
            for key, _, value in [field.strip().partition("=") for field in groupString.split()]:
                #print(f"[{groupName}] {key}: {value}")
                data[groupName][key] = value
    return data
