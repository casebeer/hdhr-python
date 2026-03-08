# hdhr-python HDHomeRun API Client

Native Python cross-platform asyncio HDHomeRun TCP and UDP API client. Has no dependencies and does
not make use of the C `libhdhomerun` or `hdhomerun_config` CLI binary.

## Features

- TCP "Control" API
  - GETSET commands
  - Client-managed legacy device channel scan using the GETSET API
- UDP "Discover" API
  - Dual stack unicast, multicast, and IPv4 broadcast support
- Undocumented legacy tuner channel scan upload API
  - POST JSON to https://api.hdhomerun.com/device/sync?LegacyChannelScan=1&DeviceAuth=
  - Allows upload of client-managed legacy device channel scans to support modern HDHomeRun clients
- Python client classes
- CLI client

## Installation

    git clone https://github.com/casebeer/hdhr-python
    cd hdhr-python
    pip install -e .

You'll now have an `hdhr` CLI script on your `PATH`.

Alternatively, install in a venv:

    cd hdhr-python
    python3 -m venv venv
    venv/bin/pip install -e .

And link to the `hdhr` script in the venv from somewhere on your `PATH`:

    ln -s "$(pwd)/venv/bin/hdhr" ~/bin/

## Usage

Send discover packets to broadcast/multicast addresses on LAN

    $ hdhr

"get" all known endpoints, including discover protocol fields, and print them out

    $ hdhr --host 192.0.1.123

Return a single JSON object with all fields found on device:

    $ hdhr --host 192.0.1.123 --json

Print the value of `/sys/hwmodel`

    $ hdhr --host 192.0.1.123 /sys/hwmodel

Set the value of `/tuner0/channel`

    $ hdhr --host 192.0.1.123 /tuner0/channel auto:33

Print just the discover data for a single device:

    $ hdhr --host 192.0.1.123 --discover

Send a discover request to a link-local IPv6 multicast group from interface `en1` and print the
replies (untested with actual HDHR devices):

    $ hdhr --host ff02::176%en1 --discover

### Logging verbosity

Set `-v` or `-vv` to print `INFO` and `DEBUG` level logging to `/dev/stderr`:

    $ hdhr -v

### Help

Print `hdhr` CLI usage help:

    $ hdhr -h

Print on-device help sent by HDHomeRun tuner showing available control protocol endpoints:

    $ hdhr --host 192.0.1.123 help

### Channel scans

Start an on-device channel scan (for modern HDHR4+ devices). Note that this will overwrite the
previous channel scan stored on the device:

    $ hdhr --host 192.0.1.123 /lineup/scan start

Perform a read-only (non-desctructive) legacy channel scan and print out the results. This will work
on both legacy and modern devices:

    $ hdhr --host 192.0.1.123 --legacy-scan -v

Perform a legacy channel scan and upload it to the HDHomeRun servers for use by HDHomeRun viewing
clients. This is necessary to use modern viewing clients with legacy devices.  Note that this will
overwrite any previous uploaded channel scan for this device.

The offical way to perform this scan and upload process is to use the SiliconDust Windows app.
Scanning and uploading is not supported in the official `hdhomerun_config` Linux CLI tool.

    $ hdhr --host 192.0.1.123 --legacy-scan-and-upload -v

You can also pass a `--channels <comma separated list of channels>` option with either
`--legacy-scan` or `--legacy-scan-and-upload` to scan only specific RF channels or frequencies:

    $ hdhr --host 192.0.1.123 --legacy-scan -v --channels 20,21,22

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
    /tuner0/streaminfo
        1: 2.1 WCBS-HD
        2: 2.2 STARTTV
        3: 2.3 DABL
        4: 2.4 365BLK
        5: 2.5 COMET
        6: 21.2 CREATE
        tsid=0x086D

And set that program:

    $ hdhr --host 192.0.1.123 /tuner0/program 3

You can now send that video to a receiver on the network:

    $ hdhr --host 192.0.1.123 /tuner0/target udp://192.0.1.254:8000

### Locking and unlocking the tuner's "lockkey"

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

## References

- https://github.com/Silicondust/libhdhomerun
- https://www.silicondust.com/hdhomerun/hdhomerun_development.pdf
- https://www.silicondust.com/hdhomerun/hdhomerun_http_development.pdf
- https://www.silicondust.com/hdhomerun/hdhomerun_tech.pdf
