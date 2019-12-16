import csv
from collections import Counter


def hist(keys):
    C = Counter(iter(keys))
    sigma = sum(C.values())
    return {k: v/sigma for k, v in C.items()}


def fmtHistLeaderboard(width, hist):
    keys = list(hist.keys())
    keys.sort(key=lambda k: hist[k], reverse=True)
    bars = (f'{k} ({hist[k]*100:05.2f}%) ' + '#'*int(hist[k]*width)
            for k in keys)
    return '\n'.join(bars)


def fmtHistPie(width, hist):
    keys = list(hist.keys())
    keys.sort(key=lambda k: hist[k], reverse=True)
    return ''.join(k[0]*int(hist[k]*width) for k in keys)


def prnHist(label, width, hist):
    print(f'{label}: ')
    print(fmtHistLeaderboard(width, hist))
    # print(fmtHistPie(width, hist))
    print()


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser('build a historgram of changing party affiliations'
                            ' between two voter registration snapshots')
    parser.add_argument('--old', help=('path from which to read the ascendant'
                                       ' snapshot'), required=True)
    parser.add_argument('--new', help=('path from which to read the descendant'
                                       ' snapshot'), required=True)
    args = parser.parse_args()
    oldReg: dict = {}
    newReg: dict = {}
    
    BOEIDX_VID = 38
    BOEIDX_PTY = 25
    with open(args.old) as istrm:
        oldReg = {r[BOEIDX_VID]: r[BOEIDX_PTY] for r in csv.reader(istrm)}

    with open(args.new) as istrm:
        newReg = {r[BOEIDX_VID]: r[BOEIDX_PTY] for r in csv.reader(istrm)}

    # describe changes:
    # 1. build histograms of old and new snapshots
    # 2. build a "delta" leaderboard and "pie chart" the number of registrants
    # of each party that originated from each other
    oldHist = hist(oldReg.values())
    prnHist('Old distribution', 64, oldHist)
    newHist = hist(newReg.values())
    prnHist('New distribution', 64, newHist)
    parties = set(oldReg.values()).union(set(newReg.values()))

    # set new voters in old distribution before computing affiliation deltas
    for k in newReg:
        if k not in oldReg:
            oldReg[k] = 'NEW'

    for party in parties:
        deltas = hist(oldReg[vid] for vid in newReg.keys()
                      if newReg[vid] == party)
        prnHist(f'Affiliation changes for {party}', 64, deltas)
