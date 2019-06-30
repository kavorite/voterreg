import csv
import json
# import pdb
from xml.etree import ElementTree
from aiohttp import ClientSession as HTTP
from exclusion import MonroeCtRecord


async def is_valid(http: HTTP, hereIdent: str, hereKey: str, addr: MonroeCtRecord):
    query = {'app_id': hereIdent, 'app_code': hereKey, 'searchtext': str(addr)}
    async with http.get('https://geocoder.api.here.com/6.2/geocode.json',
            params=query) as rsp:
        # Verify the HERE API's confidence in its response and whether it threw any errors
        # https://developer.here.com/documentation/geocoder/topics/quick-start-geocode.html
        body = await rsp.read()
        if rsp.status != 200:
            root = ElementTree.fromstring(body)
            kind = root.attrib['type'] + '/' + root.attrib['subtype']
            desc = root[0].text
            raise ValueError('HERE API: {kind}: {desc}')
        try:
            payload = json.loads(body)['Response']
            result = payload['View'][0]['Result'][0]
            if result['MatchLevel'] != 'houseNumber':
                return False
            if result['Relevance'] != 1:
                return False
            return True
        except Exception:
            return False


# TODO: output whether all address ranges are on the same side of the street
# (evenness parity predicate)
def valid(universe, hereIdent, hereKey):
    universe = tuple(universe)
    with HTTP() as http:
        jobs = (is_valid(http, hereIdent, hereKey, ent) for ent in universe)
        valid = asyncio.run_until_complete(asyncio.gather(*jobs))

    for i in range(len(universe)):
        if valid[i]:
            yield universe[i]


if __name__ == '__main__':
    from argparse import ArgumentParser
    from exclusion import universe
    parser = ArgumentParser('unroll continuous address ranges from a data set')
    parser.add_argument('--ipath', help='input data path', default=None)
    parser.add_argument('--opath', help='output data path', default=None)
    parser.add_argument('--validate', help='if present, validate the input data', action='store_true')
    parser.add_argument('--id', help='HERE API ID', default=None)
    parser.add_argument('--key', help='HERE API Key', default=None)
    args = parser.parse_args()
    if args.ipath is not None:
        istrm = open(args.ipath)
    else:
        from sys import stdin
        istrm = stdin

    if args.opath is not None:
        ostrm = open(args.opath, 'w+')
    else:
        from sys import stdout
        ostrm = stdout

    stenographer = csv.writer(ostrm)
    spool = universe(istrm)
    stenographer.writerow(next(spool))  # copy header
    if args.validate:
        if args.id is None:
            raise Exception('cmdline: please pass --id to validate addresses')
        if args.key is None:
            raise Exception('cmdline: please pass --key to validaate addresses')
        spool = valid(spool, args.id, args.key)
    for ent in spool:
        stenographer.writerow(ent.tuple())


