
import collections
from dataclasses import dataclass

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
