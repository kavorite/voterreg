import csv
from collections import Counter
import pandas as pd
import numpy as np
from sys import stdout


class BoEIndices(object):
    '''
    enumerate various useful data from the Monroe County BoE's DB schema
    '''
    vid = 0
    surname = 1
    givenName = 2
    middleInitial = 3
    suffix = 4
    houseNumber = 5
    street = 6
    party = 25


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


def stratify(oldPath, newPath, by=BoEIndices.vid, key=BoEIndices.party):
    '''
    Stratify unique voter registrations by given affiliation column, with their
    party affiliation as the default; returns a np.ndarray representing the
    adjacency matrix of various affiliations between snapshots
    '''
    with open(args.old) as istrm:
        oldReg = {r[by]: r[key] for r in csv.reader(istrm)}

    with open(args.new) as istrm:
        newReg = {r[by]: r[key] for r in csv.reader(istrm)}

    for k in newReg:
        if k not in oldReg:
            oldReg[k] = 'New'

    oldHist = Hist(oldReg.values())
    newHist = Hist(newReg.values())
    keys = list(set(oldReg.values()).union(set(newReg.values())))
    keys.sort(key=lambda k: newHist[k], reverse=True)
    keyidx = {k: i for i, k in enumerate(keys)}
    for k in newReg:
        if k not in oldReg:
            oldReg[k] = 'New'

    J = np.zeros((len(keys), len(keys)), dtype='int32')
    for vid in set(oldReg.keys()).intersection(set(newReg.keys())):
        i = keyidx[oldReg[vid]]
        j = keyidx[newReg[vid]]
        J[i, j] += 1
    df = pd.DataFrame(J, index=keys, columns=keys)
    drops = Hist(v for k, v in oldReg.items() if k not in newReg)
    df.loc['Total'] = df.sum()
    df.loc['Previous'] = np.array([oldHist[k] for k in keys])
    df.loc['Net Change'] = np.array([newHist[k]-oldHist[k] for k in keys])
    df.loc['Dropped'] = np.array([drops[k] for k in keys])
    df.drop('New', axis=1, inplace=True)
    return df


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser('catalog changes between two voter'
                            ' registration snapshots')
    parser.add_argument('--old', help=('path from which to read the ascendant'
                                       ' snapshot'), required=True)
    parser.add_argument('--new', help=('path from which to read the descendant'
                                       ' snapshot'), required=True)
    parser.add_argument('--summarize', help='summarize changes',
                        action='store_true')
    args = parser.parse_args()

    # if args.summarize:
    ledger = stratify(args.old, args.new)
    if stdout.isatty():
        print('Adjacency:')
        print(ledger)
    else:
        stdout.write(ledger.to_csv().replace('\r\n', '\n'))
    exit()
