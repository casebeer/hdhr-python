
from enum import Enum

# See
# https://www.silicondust.com/hdhomerun/hdhomerun_development.pdf
# https://github.com/Silicondust/libhdhomerun/blob/master/hdhomerun_channels.c
# https://github.com/Silicondust/libhdhomerun/blob/master/hdhomerun_device.c

class ControlFields(Enum):
    IR_TARGET = bytearray("/ir/target\0", encoding="ascii")
    LINEUP_LOCATION = bytearray("/lineup/location\0", encoding="ascii")
    SYS_MODEL = bytearray("/sys/model\0", encoding="ascii")
    SYS_HWMODEL = bytearray("/sys/hwmodel\0", encoding="ascii")
    SYS_FEATURES = bytearray("/sys/features\0", encoding="ascii")
    SYS_VERSION = bytearray("/sys/version\0", encoding="ascii")
    SYS_COPYRIGHT = bytearray("/sys/copyright\0", encoding="ascii")
    SYS_DEBUG = bytearray("/sys/debug\0", encoding="ascii")
    SYS_BOOT = bytearray("/sys/boot\0", encoding="ascii")
    SYS_DVBC_MODULATION = bytearray("/sys/dvbc_modulation\0", encoding="ascii")
    OOB_STATUS = bytearray("/oob/status\0", encoding="ascii")
    OOB_PLOTSAMPLE = bytearray("/oob/plotsample\0", encoding="ascii")

class TunerFields(Enum):
    TUNER0_CHANNEL = bytearray("/tuner0/channel\0", encoding="ascii")
    TUNER0_VCHANNEL = bytearray("/tuner0/vchannel\0", encoding="ascii")
    TUNER0_CHANNELMAP = bytearray("/tuner0/channelmap\0", encoding="ascii")
    TUNER0_FILTER = bytearray("/tuner0/filter\0", encoding="ascii")
    TUNER0_PROGRAM = bytearray("/tuner0/program\0", encoding="ascii")
    TUNER0_TARGET = bytearray("/tuner0/target\0", encoding="ascii")
    TUNER0_STATUS = bytearray("/tuner0/status\0", encoding="ascii")
    TUNER0_VSTATUS = bytearray("/tuner0/vstatus\0", encoding="ascii")
    TUNER0_STREAMINFO = bytearray("/tuner0/streaminfo\0", encoding="ascii")
    TUNER0_PLPINFO = bytearray("/tuner0/plpinfo\0", encoding="ascii")
    TUNER0_PLOTSAMPLE = bytearray("/tuner0/plotsample\0", encoding="ascii")
    TUNER0_DEBUG = bytearray("/tuner0/debug\0", encoding="ascii")
    TUNER0_LOCKKEY = bytearray("/tuner0/lockkey\0", encoding="ascii")

#/sys/features
#/sys/hwmodel
#/sys/model
#/ir/target
#/oob/status
#/tuner{num}/filter
#/tuner{num}/channelmap
#/tuner{num}/vchannel
#/tuner{num}/channel

'''
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
