#!/usr/bin/env python

from __future__ import print_function

import glob
import re
import os.path as op
import string
import sys
import os, fnmatch

def locate(pattern, root=os.curdir):
    '''Locate all files matching supplied filename pattern in and below
    supplied root directory.'''
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for filename in fnmatch.filter(files, pattern):
            yield os.path.join(path, filename)

subre = re.compile('\s+(subroutine|function)\s+(\w+)\s*\(', re.IGNORECASE)
fsymsepre = re.compile('[^' + string.ascii_letters + string.digits + '_' + ']+')

def catalog(filenames):
    topdir = op.dirname(op.dirname(op.abspath(filenames[0])))
    filenames.sort()
    subs = []
    # for each sub found we record:
    #   'flpt'
    #   'lnno'
    #   'type'
    #   'name'
    #   'type'
    #   'name'
    for filename in filenames:
        subs += extractsubinfo(filename)
    # get set of names, unique
    allnames = set([sub['name'] for sub in subs])
    # create set for each sub
    for sub in subs:
        sub['call'] = set()
    # find subs called by each sub
    for filename in set([x['flpt'] for x in subs]):
        with open(filename) as infile:
            lins = infile.readlines()
            # pick out subs defined in this file
            for sub in filter(lambda x: x['flpt'] == filename, subs):
                # error if already encountered this sub and populated subs called
                if len(sub['call']) > 0:
                    raise RuntimeError('duplicate sub definition found: ' + sub['name'])
                # start searching after first line of sub definition
                for i, lin in enumerate(lins[(sub['lnno'] + 1):]):
                    lin = lin[:-1] # remove newline
                    # are we at the end of the sub definition?
                    if lin.strip().lower() == 'end':
                        sub['leng'] = i
                        break
                    # do we need to check this line?
                    if len(lin) == 0 or (lin[0] == 'C') or (lin[0] == '*'): continue
                    # union with ALL symbols found in this line (we intersect with known subs later)
                    sub['call'] |= set([x.lower() for x in fsymsepre.split(lin)])
                # intersect known sub names, discarding all other symbols
                sub['call'] &= allnames
                # discard recursive calls
                sub['call'].discard(sub['name'])
    # reverse look-up, for each sub, who calls this sub
    for sub in subs:
        sub['clby'] = set([y['name'] for y in filter(lambda x: sub['name'] in x['call'], subs)])
    # for each sub we now have:
    #   'flpt'
    #   'lnno'
    #   'type'
    #   'name'
    #   'type'
    #   'name'
    #   'call'
    #   'clby'
    return subs

def findinc(cfilenames, subs):
    cfilenames.sort()
    for sub in subs:
        sub['ccal'] = set()
    for cfilename in cfilenames:
        with open(cfilename) as infile:
            lines = infile.readlines()
            for sub in subs:
                for lineno, line in enumerate(lines):
                    if line.find(sub['name'] + '_') > 0:
                        sub['ccal'].add((op.basename(cfilename), lineno))
    # for each sub we now have:
    #   'flpt'
    #   'lnno'
    #   'type'
    #   'name'
    #   'type'
    #   'name'
    #   'call'
    #   'clby'
    #   'ccal' set of pairs: [(c file name, line number)]
    return subs

def markcalled(sub, subs):
    if sub['anyc'] == True:
        return
    sub['anyc'] = True
    map(lambda x: markcalled(x, subs), (i for i in subs if i['name'] in sub['call']))

def findindirectc(subs):
    for sub in subs:
        sub['anyc'] = False
    for sub in subs:
        if len(sub['ccal']) > 0:
            sub['anyc'] = True
            map(lambda x: markcalled(x, subs), (i for i in subs if i['name'] in sub['call']))
    # for each sub we now have:
    #   'flpt'
    #   'lnno'
    #   'type'
    #   'name'
    #   'type'
    #   'name'
    #   'call'
    #   'clby'
    #   'ccal'
    #   'anyc' bool: sub called either directy or indirectly from c file
    return subs

def strccallsreport(subs):
    direct = set(y['name'] for y in filter(lambda x: len(x['ccal']) != 0, subs))
    indirectonly = set(y['name'] for y in filter(lambda x: len(x['ccal']) == 0 and x['anyc'], subs))
    notused = set(y['name'] for y in subs) - (direct | indirectonly)
    lines = []
    lines.append(u'called directly from c\n')
    for subname in direct:
        sub = (x for x in subs if x['name'] == subname).next() # find sub with name we want
        line = u''
        fname = op.basename(op.dirname(sub['flpt'])) + '/' + op.basename(sub['flpt'])
        line += '{0:14} : {1:22} '.format(sub['name'], fname)
        line += '('
        for cfile in sub['ccal']:
            line += cfile[0] + ', '
        line = line[:-2] + ')\n'
        lines.append(line)
    lines.append(u'\n')
    lines.append(u'\n')
    lines.append(u'called only indirectly from c\n')
    for subname in indirectonly:
        sub = (x for x in subs if x['name'] == subname).next() # find sub with name we want
        line = u''
        fname = op.basename(op.dirname(sub['flpt'])) + '/' + op.basename(sub['flpt'])
        line += '{0:14} : {1:22} '.format(sub['name'], fname)
        line += '('
        for clby in sub['clby']:
            line += clby + ', '
        line = line[:-2] + ')\n'
        lines.append(line)
    lines.append(u'\n')
    lines.append(u'\n')
    lines.append(u'not called, either directly or indirectly, from c\n')
    for subname in notused:
        sub = (x for x in subs if x['name'] == subname).next() # find sub with name we want
        line = u''
        fname = op.basename(op.dirname(sub['flpt'])) + '/' + op.basename(sub['flpt'])
        line += '{0:14} : {1}'.format(sub['name'], fname)
        line += '\n'
        lines.append(line)
    return lines

def strccalls(subs):
    lines = []
    for sub in subs:
        for ccall in sub['ccal']:
            fname = op.basename(op.dirname(sub['flpt'])) + '/' + op.basename(sub['flpt'])
            lines.append('{0:22} : {1:14}     {2}({3})'.format(fname, sub['name'], ccall[0], ccall[1]))
    lines.sort()
    return lines

def struniqueccalls(subs):
    usubs = set()
    for sub in subs:
        if len(sub['ccal']) > 0:
            fname = op.basename(op.dirname(sub['flpt'])) + '/' + op.basename(sub['flpt'])
            usubs.add((sub['name'], fname))
    lines = []
    for sub in usubs:
        lines.append('{0:22} : {1}'.format(sub[1], sub[0]))
    lines.sort()
    return lines

def struniquenotccalls(subs):
    usubs = set()
    for sub in subs:
        if len(sub['ccal']) == 0:
            fname = op.basename(op.dirname(sub['flpt'])) + '/' + op.basename(sub['flpt'])
            usubs.add((sub['name'], fname))
    lines = []
    for sub in usubs:
        lines.append('{0:22} : {1}'.format(sub[1], sub[0]))
    lines.sort()
    return lines

def printsubs(subs, uncalled=[]):
    for sub in subs:
        if sub['name'] in uncalled: print('*', end='')
        else: print(' ', end='')

        print(subasstr(sub))

def printsubsfromnames(subnames, subs):
    mysubs = filter(lambda x: x['name'] in subnames, subs)
    printsubs(mysubs)

def gvdot(subs):
    lins = []
    for sub in subs:
        if len(sub['call']) == 0:
            lins.append(sub['name'] + ';')
        else:
            for c in sub['call']:
                lins.append(sub['name'] + ' -> ' + c + ';')
    for sub in subs:
        if len(sub['ccal']) > 0:
            lins.append(sub['name'] + ' [color=lightblue,style=filled];')
        elif sub['anyc']:
            lins.append(sub['name'] + ' [color=palegreen,style=filled];')
        else:
            lins.append(sub['name'] + ' [color=pink,style=filled];')
    res = u''
    res += 'digraph g {\n'
    res += 'rankdir=LR;\n'
    res += 'ranksep=3;\n'
    res += 'page="8.5,11";\n'
    res += 'size="16,30";\n'
    res += '\n'.join(lins)
    res += '\n}'
    return res

def extractsubinfo(filename):
    res = []
    with open(filename) as infile:
        lins = infile.readlines()
        for lnno, lin in enumerate(lins):
            lin = lin[:-1]
            match = subre.match(lin)
            if match:
                sub = dict()
                sub['flpt'] = filename
                sub['lnno'] = lnno
                sub['type'], sub['name'] = match.groups()
                sub['type'] = sub['type'].lower()
                sub['name'] = sub['name'].lower()
                res.append(sub)
    return res

def unused(subs):
    allnames = set([sub['name'] for sub in subs])
    allcalls = set(sum([list(sub['call']) for sub in subs], []))
    return allnames - allcalls

def subasstr(sub):
    sub['flnm'] = op.basename(op.dirname(sub['flpt'])) + '/' + op.basename(sub['flpt'])
    res = u''
    res += '{0[name]:20}{1:4}{0[leng]:4d} lns {0[flnm]:22}:{0[lnno]:>4d}'.format(sub, sub['type'][:3])
    if len(sub['call']) > 0:
        res += ' <' + ' '.join(sub['call']) + '>'
    if len(sub['clby']) > 0:
        res += ' >' + ' '.join(sub['clby']) + '<'
    return res

def main(args):
    subs = catalog(args[1:])
    printsubs(subs, unused(subs))

# usage: python fortsubs.py file1 file2 ...
# example: python fortsubs.py /Users/jra/prj/MCS_Linux/DMCS-TPS/{applib2000,ftn}/*.f
if __name__=="__main__":
    main(sys.argv)
