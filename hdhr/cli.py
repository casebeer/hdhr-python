
import logging
import argparse
import sys
import os
import pprint
import asyncio
import json
import textwrap
import collections

from .control import ControlClient
from .client import HdhrClient
from .scan import ScanManager, ScanUploadClient
from .tuning import TunerMonitor

logger = logging.getLogger(__name__)

DEFAULT_PORT = 65001

LOG_VERBOSITY = {
    0: logging.WARN,
    1: logging.INFO,
    2: logging.DEBUG,
}

async def cliClient(args) -> int:
    logging.basicConfig(level=LOG_VERBOSITY.get(args.verbose, logging.DEBUG))

    logger.debug(f"CLI args: {args}")

    host = os.environ.get('HDHR_HOST')
    port = int(os.environ.get('HDHR_PORT', DEFAULT_PORT))

    if args.host is not None:
        host = args.host

    if args.port is not None:
        port = args.port

    # TODO: separate config for discoverPort
    client = await HdhrClient.create(host, controlPort=port, discoverPort=port)

    # n.b. we will change HdhrClient.host after it was already set
    if args.device:
        # TODO: Change DiscoverClient API to differentiate between directed unicast discovery
        # parameter queries and broadcast discovery searches
        host = await client.discoverDevice(args.device)
        if host is not None:
            client.host = host
            logger.info(f"Found host {host} for device ID {args.device}")
        else:
            logging.error(f"Unable to find device with ID {args.device} on local network.")
            return 1 # exit program
    #sys.exit(0)


    data = collections.defaultdict(dict)

    channels = [int(c.strip()) for c in args.channels.split(",") if len(c) > 0]

    logger.debug(f"host={host} scan={args.legacy_scan} scan_upload={args.legacy_scan_and_upload} "
                 f"endpoint={args.endpoint} value={args.value}")
    if not host or args.discover:
        # discovery mode
        async for reply in client.discover(): # HdhrClient.discover() sends to HdhrClient.host
            data[reply["DEVICE_ID"]].update(reply)

    elif args.legacy_scan_and_upload:
        # --legacy-scan-and-upload
        scanUploadOutput = await ScanManager(client).upload(channels=channels,
                                                            apiBase=args.upload_uri,
                                                            dryRun=args.upload_dry_run)
        if args.upload_dry_run:
            # in upload dry run, don't print normal format, print scanUploadJson format instead
            print(scanUploadOutput['lineup'].scanUploadJson(indent=2))
            return
        else:
            # otherwise, update output dict as usual
            data.update(scanUploadOutput)
    elif args.legacy_scan:
        # --legacy-scan
        data.update(await ScanManager(client).scan(channels=channels))

    elif args.tuner_status is not None:
        data.update({ f"tunerStatus{args.tuner_status}": await client.tunerStatus(f"/tuner{args.tuner_status}") })

    elif args.tuner_monitor is not None:
        await TunerMonitor(client, f"/tuner{args.tuner_monitor}").run()
        return

    elif args.endpoint is None:
        # no endpoint set, dumpe all variables
        data.update(await client.getAllFields())
    elif args.value is not None:
        # set
        data.update(await client.set(args.endpoint, args.value))
    else:
        # get
        data.update(await client.get(args.endpoint))

    handleOutput(data, outputJson=args.json)

def handleOutput(data, outputJson=False):
    if outputJson:
        print(json.dumps(dict(data), indent=2))
    else:
        print(textFormat(dict(data)))

def textFormat(data):
    '''
    Output custom format

    Keys followed by values on the next line, indented four spaces.
    '''
    output = []
    #output.append(str(type(data)))
    if type(data) == dict:
        for k,v in data.items():
            output.append(f"{k}")
            output.append(textwrap.indent(textFormat(v), "    "))
    elif type(data) == list:
        for v in data:
            # hanging indent beacuse of two characters of "- " bullet
            lines = textFormat(v).splitlines(True)
            for i in range(1, len(lines)):
                lines[i] = f"  {lines[i]}"
            output.append(f"- {''.join(lines)}")
    else:
        output.append(str(data).strip())
    return "\n".join(output)

async def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="IP address or hostname of HDHomerun device to connect to. "
             "Overrides HDHR_HOST environment variable.",
    )

    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=None,
        help="TCP port to connect to for Control Protocol API. "
             "Overrides HDHR_PORT environemnt variable. Default 65001.",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        default=0,
        action="count",
        help="Set logging verbosity. Specify multiple times for more detail.",
    )

    parser.add_argument(
        "--discover",
        default=0,
        action="store_true",
        help="Perform a discovery API request to --host."
             "Host can be a broadcast or multicast address, including a scoped IPv6 "
             "link-local address, e.g. fe80::1234%%eno1.",
    )

    parser.add_argument(
        "-j",
        "--json",
        default=0,
        action="store_true",
        help="Output JSON objects",
    )

    parser.add_argument(
        "-d",
        "--device",
        default=0,
        help="Connect to device by device id using broadcast/multicast discovery.",
    )

    parser.add_argument(
        "-s",
        "--legacy-scan",
        default=0,
        action="store_true",
        help="Perform a legacy device (i.e. client-controlled) channel scan and print "
             "the result to stdout. Any positional parameters will be ignored. Note that "
             "a legacy scan may be performed on but is NOT necessary and will NOT update "
             "scanned channel data on modern devices which support the /lineup/scan "
             "command. On those devices, run an on-device channel scan with "
             "hdhr --device <device id> /lineup/scan start"
    )
    parser.add_argument(
        "--channels",
        default="",
        help="Comma separated list of RF channels to use with --legacy-scan or "
             "--legacy-scan-and-upload. Optional. Scans default to all channels."
    )

    parser.add_argument(
        "--legacy-scan-and-upload",
        default=0,
        action="store_true",
        help="Perform a legacy device channel scan and upload the result to api.hdhomerun.com."
             "A legacy channel scan should only be needed on \"legacy\" tuner devices (i.e. HDHR3 "
             "and earlier). Devices which can run and store a channel scan on-device through the "
             "web interface do not need a legacy channel scan. Legacy devices must perform and "
             "upload a channel scan before modern HDHomeRun client apps can make use of them. "
             "The official way to perform and upload this channel scan is using the SiliconDust "
             "Windows client app."
             "WARNING, DESCTRUCTIVE: Will overwrite previous channel scan data for the device "
             "stored on the Silicon Dust servers."
             "Any positional parameters will be ignored.",
    )

    parser.add_argument(
        "--upload-uri",
        default=None,
        help="Base URI for legacy channel scan upload. Leave empty to use default "
             f"{ScanUploadClient.apiBase}"
    )
    parser.add_argument(
        "--upload-dry-run",
        default=False,
        action="store_true",
        help="Generate and print legacy channel scan upload JSON but don't upload to API server."
    )

    parser.add_argument(
        "--tuner-status",
        default=None,
        type=int,
        help="Display TunerStatus for specified tuner number"
    )

    parser.add_argument(
        "--tuner-monitor",
        default=None,
        type=int,
        help="Continuously monitor TunerStatus for specified tuner number. Ctrl-C to exit."
    )

    parser.add_argument(
        "endpoint",
        nargs="?",
        help="Control API endpoint/variable name to get or set. "
             "If neither endpoint nor value is provided, the default will be to "
             "query and print out values of all known endpoints.",
    )

    parser.add_argument(
        "value",
        nargs="?",
        default=None,
        help="Value to write to endpoint/variable. Optional. "
             "Leave empty to read rather than write.",
    )

    args = parser.parse_args()

    return await cliClient(args)

def run():
    sys.exit(asyncio.run(main()))

if __name__ == '__main__':
    run()
