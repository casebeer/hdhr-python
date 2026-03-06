
import logging
import argparse
import sys
import os
import pprint

from control import ControlClient
import fields

logger = logging.getLogger(__name__)

DEFAULT_PORT = 65001

LOG_VERBOSITY = {
    0: logging.WARN,
    1: logging.INFO,
    2: logging.DEBUG,
}

def cliClient(args) -> int:
    logging.basicConfig(level=LOG_VERBOSITY.get(args.verbose, logging.DEBUG))

    host = os.environ.get('HDHR_HOST')
    port = int(os.environ.get('HDHR_PORT', DEFAULT_PORT))

    if args.host is not None:
        host = args.host

    if args.port is not None:
        port = args.port

    client = ControlClient(host, port)

    data = {}

    logger.debug(f"{'get' if args.value is None else 'set'} {args.endpoint} {args.value if args.value is not None else ''}")
    if args.endpoint is None:
        # no endpoint set, dumpe all variables
        data.update(getAllFields(client))
    elif args.value is not None:
        # set
        data.update(client.set(args.endpoint, args.value))
    else:
        # get
        data.update(client.get(args.endpoint))

    pprint.pprint(data)

    # restart device
    #pprint.pprint(client.set(fields.ControlFields.SYS_RESTART, "self"))
    #return 0

def getAllFields(client):
    data = {}
    for field in fields.ControlFields:
        data.update(client.get(field.value))

    # n.b. need to get number of tuners via Discovery API or HTTP API /discover.json
    for tunerNumber in (0, 1):
        for field in fields.TunerFields:
            data.update(client.get(field.value.format(tunerNumber=tunerNumber)))
    return data


def main() -> int:
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

    return cliClient(args)

if __name__ == '__main__':
    sys.exit(main())
