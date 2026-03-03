
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
'''

class ControlFields(Enum):
    '''
    Enum storing non-templated Control Protocol API endpoint field names
    '''
    SYS_MODEL = "/sys/model"
    SYS_HWMODEL = "/sys/hwmodel"
    SYS_FEATURES = "/sys/features"
    SYS_VERSION = "/sys/version"
    SYS_COPYRIGHT = "/sys/copyright"
    SYS_DEBUG = "/sys/debug"

    SYS_RESTART = "/sys/restart" # write "self" to reboot device

    IR_TARGET = "/ir/target" # error unknown getset variable on HDTC-2US
    LINEUP_LOCATION = "/lineup/location" # error unknown getset variable on HDTC-2US
    SYS_BOOT = "/sys/boot" # error unknown getset variable on HDTC-2US
    SYS_DVBC_MODULATION = "/sys/dvbc_modulation" # error unknown getset variable on HDTC-2US
    OOB_STATUS = "/oob/status" # error unknown getset variable on HDTC-2US
    OOB_PLOTSAMPLE = "/oob/plotsample" # error unknown getset variable on HDTC-2US

class TunerFields(Enum):
    '''
    Enum storing tuner-specific Control Protocl endpoint template strings

    These values are *template strings* whcich must be format()ed with a
    tunerNumber integer in {0, 1, 2, 3} before use.
    '''
    CHANNEL = "/tuner{tunerNumber:d}/channel"
    VCHANNEL = "/tuner{tunerNumber:d}/vchannel"
    CHANNELMAP = "/tuner{tunerNumber:d}/channelmap"
    FILTER = "/tuner{tunerNumber:d}/filter"
    PROGRAM = "/tuner{tunerNumber:d}/program"
    TARGET = "/tuner{tunerNumber:d}/target"
    STATUS = "/tuner{tunerNumber:d}/status"
    VSTATUS = "/tuner{tunerNumber:d}/vstatus" # error unknown getset variable on HDTC-2US
    STREAMINFO = "/tuner{tunerNumber:d}/streaminfo"
    PLPINFO = "/tuner{tunerNumber:d}/plpinfo"
    PLOTSAMPLE = "/tuner{tunerNumber:d}/plotsample" # error unknown getset variable on HDTC-2US
    DEBUG = "/tuner{tunerNumber:d}/debug"
    LOCKKEY = "/tuner{tunerNumber:d}/lockkey"
