import csv
from collections import Counter
import pandas as pd
import numpy as np
from sys import stdout


class Hist(Counter):
    def __init__(self, data):
        super().__init__(data)

    def normalize(self):
        sigma = sum(self.values())
        return {k: v/sigma for k, v in self.items()}
    
    def leaderboard(self):
        keys = tuple(sorted(self.keys(), key=lambda k: self[k], reverse=True))
        return '\n'.join(f'{k}: {self[k]}' for k in keys)

    def pie(self, width):
        hist = self.normalize()
        keys = list(hist.keys())
        keys.sort(key=lambda k: hist[k], reverse=True)
        return ''.join(k[0]*int(hist[k]*width) for k in keys)


def prnHist(label, hist):
    print(f'{label}: ')
    print(hist.leaderboard())
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
    oldHist = Hist(oldReg.values())
    newHist = Hist(newReg.values())
    # express new voters in old distribution before computing affiliation
    # deltas
    for k in newReg:
        if k not in oldReg:
            oldReg[k] = 'NEW'
    parties = list(set(oldReg.values()).union(set(newReg.values())))
    parties.sort(key=lambda party: newHist[party], reverse=True)
    partyidx = {party: i for i, party in enumerate(parties)}
    J = np.zeros((len(parties), len(parties)), dtype='int32')
    for vid in set(oldReg.keys()).intersection(set(newReg.keys())):
        i = partyidx[oldReg[vid]]
        j = partyidx[newReg[vid]]
        J[i, j] += 1
    df = pd.DataFrame(J, index=parties, columns=parties)
    df.loc['TOT'] = df.sum()
    df.loc['PRV'] = np.array([oldHist[k] for k in parties])
    df.loc['RET'] = np.array([newHist[k]-oldHist[k] for k in parties])
    df.drop('NEW', axis=1, inplace=True)
    if stdout.isatty():
        print('Adjacency:')
        print(df)
    else:
        stdout.write(df.to_csv().replace('\r\n', '\n'))
