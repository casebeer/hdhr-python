
from enum import Enum

'''
See
- https://www.silicondust.com/hdhomerun/hdhomerun_development.pdf
- https://github.com/Silicondust/libhdhomerun/blob/master/hdhomerun_channels.c
- https://github.com/Silicondust/libhdhomerun/blob/master/hdhomerun_device.c

From https://www.silicondust.com/hdhomerun/hdhomerun_development.pdf:

 /tuner<n>/channel <modulation>:<freq|ch> Get/set modulation and frequency
 /tuner<n>/channelmap <channel map> Get/set channel to frequency map
 /tuner<n>/filter 0x<nnnn>-0x<nnnn> [...] Get/set PID filter
 /tuner<n>/program <program number> Get/set MPEG program filter
 /tuner<n>/target <ip>:<port> Get/set target IP for tuner

 /tuner<n>/status Display status of tuner
 /tuner<n>/streaminfo Display stream info
 /tuner<n>/debug Display debug info for tuner

 /tuner<n>/lockkey Set/clear tuner lock

 /ir/target <ip>:<port> Get/set target IP for IR
 /lineup/location <countrycode>:<postcode> Get/Set location for lineup
 /lineup/location disabled Disable lineup server connection

 /sys/model Display model name
 /sys/features Display supported features
 /sys/version Display firmware version
 /sys/copyright Display firmware copyright

Output of `get help` on HDTC-2US:

    Supported configuration options:
    /lineup/scan
    /sys/copyright
    /sys/debug
    /sys/features
    /sys/hwmodel
    /sys/model
    /sys/restart <resource>
    /sys/version
    /tuner<n>/channel <modulation>:<freq|ch>
    /tuner<n>/channelmap <channelmap>
    /tuner<n>/debug
    /tuner<n>/filter "0x<nnnn>-0x<nnnn> [...]"
    /tuner<n>/lockkey
    /tuner<n>/program <program number>
    /tuner<n>/status
    /tuner<n>/plpinfo
    /tuner<n>/streaminfo
    /tuner<n>/target <ip>:<port>
    /tuner<n>/vchannel <vchannel>

From https://www.silicondust.com/hdhomerun/hdhomerun_tech.pdf

/card/status Get status of CableCARD (6CC only)
/oob/channel <modulation>:<freq> Get/set out of band channel (6CC only)
/oob/debug Get out of band channel debug info (6CC only)
/oob/status Get out of band channel status info (6CC only)
/sys/boot <config> Get/set boot configuration
/sys/copyright Get copyright information
/sys/debug Get/set system debug information
/sys/features Get system feature information
/sys/hwmodel Get system hardware model string
/sys/ipaddr dhcp|"<ip> <mask> <gw> <dns>" Get/set system IP address
/sys/model Get/set model string
/sys/restart <resource> Restart device/component
/sys/version Get firmware version
/tuner<n>/channel <modulation>:<freq|ch> Get/set channel
/tuner<n>/channelmap <channelmap> Get/set channelmap
/tuner<n>/debug Get tuner debug information
/tuner<n>/filter "0x<nnnn>-0x<nnnn> […]" Get/set tuner PID filter
/tuner<n>/lockkey Get/set tuner locking
/tuner<n>/plotsample Get raw plotsample data from tuner
/tuner<n>/program <program number> Get/set MPEG program
/tuner<n>/streaminfo Get list of programs on current channel
/tuner<n>/status Get tuner status
/tuner<n>/target <ip>:<port> Get/set stream target
/tuner<n>/vchannel <vchannel> Get/set virtual channel number (6CC only)
/tuner<n>/vstatus Get/set subscription/protection status (6CC only)

'''

class ControlFields(Enum):
    '''
    Enum storing non-templated Control Protocol API endpoint field names
    '''
    HELP = "help" # RO provides list of supported endpoints from device
    SYS_MODEL = "/sys/model" # RO
    SYS_HWMODEL = "/sys/hwmodel" # RO
    SYS_VERSION = "/sys/version" # RO
    SYS_COPYRIGHT = "/sys/copyright" # RO
    SYS_DEBUG = "/sys/debug" # RO
    SYS_FEATURES = "/sys/features" # Seems RO, but gives value format error not RO error on HDTC-2US

    LINEUP_SCAN = "/lineup/scan" # write "start" or "abort"
    SYS_RESTART = "/sys/restart" # write "self" to reboot device

    IR_TARGET = "/ir/target" # error unknown getset variable on HDTC-2US
    LINEUP_LOCATION = "/lineup/location" # error unknown getset variable on HDTC-2US
    SYS_BOOT = "/sys/boot" # error unknown getset variable on HDTC-2US
    SYS_DVBC_MODULATION = "/sys/dvbc_modulation" # error unknown getset variable on HDTC-2US

    CARD_STATUS = "/card/status" # Get status of CableCARD (6CC only)
    OOB_STATUS = "/oob/status" # Get out of band channel debug info (6CC only)
    OOB_PLOTSAMPLE = "/oob/plotsample" # Get out of band channel status info (6CC only)
    OOB_CHANNEL = "/oob/channel" # <modulation>:<freq> Get/set out of band channel (6CC only)
    OOB_DEBUG = "/oob/debug" # Get out of band channel debug info (6CC only)
    SYS_IPADDR = "/sys/ipaddr" # dhcp|"<ip> <mask> <gw> <dns>" Get/set system IP address

class TunerFields(Enum):
    '''
    Enum storing tuner-specific Control Protocl endpoint template strings

    These values are *template strings* whcich must be format()ed with a
    tunerNumber integer in {0, 1, 2, 3} before use.
    '''
    STATUS = "/tuner{tunerNumber:d}/status" # RO
    STREAMINFO = "/tuner{tunerNumber:d}/streaminfo" # RO
    DEBUG = "/tuner{tunerNumber:d}/debug" # RO

    CHANNEL = "/tuner{tunerNumber:d}/channel" # <modulation|"auto">:<frequency|channel>
    VCHANNEL = "/tuner{tunerNumber:d}/vchannel" # "v"<virtual channel>.<virtual subchannel>
    CHANNELMAP = "/tuner{tunerNumber:d}/channelmap" # <channel map>, one of us-bcast, us-cable, us-hrc, uc-irc, {au,eu,tw}-{bcast,cable}
    FILTER = "/tuner{tunerNumber:d}/filter" # "0x<nnnn>-0x<nnnn> […]" Get/set tuner PID filter
    PROGRAM = "/tuner{tunerNumber:d}/program"# <MPEG program number>

    TARGET = "/tuner{tunerNumber:d}/target" # <proto://ip:port>
    LOCKKEY = "/tuner{tunerNumber:d}/lockkey" # write "force" to remove another client's lock

    PLPINFO = "/tuner{tunerNumber:d}/plpinfo"
    VSTATUS = "/tuner{tunerNumber:d}/vstatus" # Get/set subscription/protection status (6CC only)
    PLOTSAMPLE = "/tuner{tunerNumber:d}/plotsample" # Get raw plotsample data from tuner

class HttpEndpoints(Enum):
    LINEUP_JSON = "/lineup.json" # params tuning&show={all,found}
    LINEUP_XML = "/lineup.xml" # params tuning&show={all,found}
    LINEUP_POST = "/lineup.post" # POST params scan={start,abort}
    LINEUP_STATUS = "/lineup_status.json"
    STATUS = "/status.json"
    DISCOVER = "/discover.json"
