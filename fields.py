
from enum import Enum

# See
# https://www.silicondust.com/hdhomerun/hdhomerun_development.pdf
# https://github.com/Silicondust/libhdhomerun/blob/master/hdhomerun_channels.c
# https://github.com/Silicondust/libhdhomerun/blob/master/hdhomerun_device.c

class ControlFields(Enum):
    IR_TARGET = "/ir/target"
    LINEUP_LOCATION = "/lineup/location"
    SYS_MODEL = "/sys/model"
    SYS_HWMODEL = "/sys/hwmodel"
    SYS_FEATURES = "/sys/features"
    SYS_VERSION = "/sys/version"
    SYS_COPYRIGHT = "/sys/copyright"
    SYS_DEBUG = "/sys/debug"
    SYS_BOOT = "/sys/boot"
    SYS_DVBC_MODULATION = "/sys/dvbc_modulation"
    OOB_STATUS = "/oob/status"
    OOB_PLOTSAMPLE = "/oob/plotsample"

    SYS_RESTART = "/sys/restart"

class TunerFields(Enum):
    TUNER0_CHANNEL = "/tuner0/channel"
    TUNER0_VCHANNEL = "/tuner0/vchannel"
    TUNER0_CHANNELMAP = "/tuner0/channelmap"
    TUNER0_FILTER = "/tuner0/filter"
    TUNER0_PROGRAM = "/tuner0/program"
    TUNER0_TARGET = "/tuner0/target"
    TUNER0_STATUS = "/tuner0/status"
    TUNER0_VSTATUS = "/tuner0/vstatus"
    TUNER0_STREAMINFO = "/tuner0/streaminfo"
    TUNER0_PLPINFO = "/tuner0/plpinfo"
    TUNER0_PLOTSAMPLE = "/tuner0/plotsample"
    TUNER0_DEBUG = "/tuner0/debug"
    TUNER0_LOCKKEY = "/tuner0/lockkey"

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
