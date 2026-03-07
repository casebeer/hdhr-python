# hdhr-python HDHomeRun API Client

Native cross-platform Python asyncio HDHomeRun TCP and UDP API client.

## Features

- TCP "Control" API
  - GETSET commands
  - Client-managed legacy device channel scan using the GETSET API
- UDP "Discover" API
  - Dual stack unicast, multicast, and IPv4 broadcast support
- Undocumented https://api.hdhomerun.com/device/sync?LegacyChannelScan=1&DeviceAuth= API
  - Allows upload of client-managed legacy device channel scans to support modern HDHomeRun clients
- Python client classes
- CLI client

## Usage

Send discover packets to broadcast/multicast addresses on LAN

    $ hdhr

"get" all known endpoints and print them out

    $ hdhr --host 192.0.1.123

Print the value of `/sys/hwmodel`

    $ hdhr --host 192.0.1.123 /sys/hwmodel

Set the value of `/tuner0/channel`

    $ hdhr --host 192.0.1.123 /tuner0/channel auto:33

### Channel scans

Start an on-device channel scan (for modern HDHR4+ devices). Note that this will overwrite the
previous channel scan stored on the device:

    $ hdhr --host 192.0.1.123 /lineup/scan start

Perform a read-only (non-desctructive) legacy channel scan and print out the results. This will work
on both legacy and modern devices:

    $ hdhr --host 192.0.1.123 --legacy-scan

Perform a legacy channel scan and upload it to the HDHomeRun servers for use by HDHomeRun viewing
clients. This is necessary to use modern viewing clients with legacy devices.  Note that this will
overwrite any previous uploaded channel scan for this device.

The offical way to perform this scan and upload process is to use the SiliconDust Windows app.
Scanning and uploading is not supported in the official `hdhomerun_config` Linux CLI tool.

    $ hdhr --host 192.0.1.123 --legacy-scan-and-upload

### Tuning

Tune a modern tuner to a virtual channel:

    $ hdhr --host 192.0.1.123 /tuner0/vchannel 13.1

Tune a legacy tuner to a virtual channel. Note that you'll need to know ahead of time what RF
channel and/or frequency to start from (for example, from a previous channel scan):

    $ hdhr --host 192.0.1.123 /tuner0/channel auto:12

Alternatively, you can set the RF channel by frequency in Hertz:

    $ hdhr --host 192.0.1.123 /tuner0/channel auto:207000000

Now find the correct program ID for virtual channel 13.1:

    $ hdhr --host 192.0.1.123 /tuner0/streaminfo
    {'/tuner0/streaminfo': '3: 13.1 WNET-HD\n'
                       '4: 13.2 KIDS\n'
                       '5: 14.1 WNDT-CD\n'
                       '6: 21.1 WLIW-HD\n'
                       '7: 21.3 WORLD\n'
                       '8: 21.4 AllArts\n'
                       'tsid=0x07DB\n'}

And set that program:

    $ hdhr --host 192.0.1.123 /tuner0/program 3

You can now send that video to a receiver on the network:

    $ hdhr --host 192.0.1.123 /tuner0/target udp://192.0.1.254:8000

# Locking and unlocking the tuner's "lockkey"

Setting a tuner's "lockkey" prevents other devices on the network from taking over the tuner until
you delete the lockkey.

If the tuner has been locked by another device and you need to force it to unlock, set the lockkey
to `force`:

    $ hdhr --host 192.0.1.123 /tuner0/lockkey force

### Python API usage

For usage examples, see the `main()` methods in

- `discover.py` – UDP Discovery API client
- `control.py` – TCP Control API client
- `hdhr.py` low level packet parsing

## TODO

- Usage of tuner with a lockkey set

## Non-goals

- Firmware upload API
