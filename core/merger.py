#!/usr/bin/env python

'''

Konstantin Pankov <zbnnmf@onsemi.com>

Based on https://github.com/Rahul-Dhakade/python-3-way-merge/blob/master/three-way-merge.py

'''

import difflib
import sys
import re

def read_file(filename):
    try:
        f = open(filename, 'r')
        l = f.readlines()
        f.close()
    except IOError:
        print ("can't open file '" + filename + "'. aborting.")
        sys.exit(-1)
    else:
        return l

def drop_inline_diffs(diff):
    r = []
    for t in diff:
        if not t.startswith('?'):
            r.append(t)
    return r


'''
Params: my, base, other
Return: config flag and output file (lines)
'''
def merge(a, x, b):
    dxa = difflib.Differ()
    dxb = difflib.Differ()
    xa = drop_inline_diffs(dxa.compare(x, a))
    xb = drop_inline_diffs(dxb.compare(x, b))

    m = []
    index_a = 0
    index_b = 0
    had_conflict = 0

    while (index_a < len(xa)) and (index_b < len(xb)):
        # no changes or adds on both sides
        if (xa[index_a] == xb[index_b] and
            (xa[index_a].startswith('  ') or xa[index_a].startswith('+ '))):
            m.append(xa[index_a][2:])
            index_a += 1
            index_b += 1
            continue

        # removing matching lines from one or both sides
        if ((xa[index_a][2:] == xb[index_b][2:])
            and (xa[index_a].startswith('- ') or xb[index_b].startswith('- '))):
            index_a += 1
            index_b += 1
            continue

        # adding lines in A
        if xa[index_a].startswith('+ ') and xb[index_b].startswith('  '):
            m.append(xa[index_a][2:])
            index_a += 1
            continue

        # adding line in B
        if xb[index_b].startswith('+ ') and xa[index_a].startswith('  '):
            m.append(xb[index_b][2:])
            index_b += 1
            continue

        # conflict - list both A and B, similar to GNU's diff3
        m.append("<<<<<<< A\n")
        while (index_a < len(xa)) and not xa[index_a].startswith('  '):
            m.append(xa[index_a][2:])
            index_a += 1
        m.append("=======\n")
        while (index_b < len(xb)) and not xb[index_b].startswith('  '):
            m.append(xb[index_b][2:])
            index_b += 1
        m.append(">>>>>>> B\n")
        had_conflict = 1

    # append remining lines - there will be only either A or B
    for i in range(len(xa) - index_a):
        m.append(xa[index_a + i][2:])
    for i in range(len(xb) - index_b):
        m.append(xb[index_b + i][2:])

    return had_conflict, m

def merge_files(my, base, other, output) -> bool:
    my_file = read_file(my)
    base_file = read_file(base)
    other_file = read_file(other)
    (conflict, output_file) = merge(my_file, base_file, other_file)
    try:
        output_file = open(output, 'w')
        for line in output_file:
            output_file.write(line)
        output_file.close()
    except IOError:
        print ("ERROR: Can't write to merged file " + output)
        sys.exit(-1)
    return conflict

def merge_files_new(my, base, other, output) -> bool:
    a = read_file(my)
    x = read_file(base)
    b = read_file(other)

    

    dxa = difflib.Differ()
    dxb = difflib.Differ()
    xa = drop_inline_diffs(dxa.compare(x, a))
    xb = drop_inline_diffs(dxb.compare(x, b))

    index_a = 0
    index_b = 0
    had_conflict = False
    output_lines = []

    while (index_a < len(xa)) and (index_b < len(xb)):
        # Skip SVN keywords
        if (re.search("//[\s\t]*\$.*\$", xa[index_a][2:]) != None) and (re.search("//[\s\t]*\$.*\$", xb[index_b][2:]) != None):
            if xa[index_a].startswith('- '):
                index_a += 1
                continue
            if xb[index_b].startswith('- '):
                index_b += 1
                continue
            output_lines.append(xa[index_a][2:])
            index_a += 1
            index_b += 1
            continue

        # no changes or adds on both sides
        if (xa[index_a] == xb[index_b] and
            (xa[index_a].startswith('  ') or xa[index_a].startswith('+ '))):
            output_lines.append(xa[index_a][2:])
            index_a += 1
            index_b += 1
            continue

        # removing matching lines from one or both sides
        if ((xa[index_a][2:] == xb[index_b][2:])
            and (xa[index_a].startswith('- ') or xb[index_b].startswith('- '))):
            index_a += 1
            index_b += 1
            continue

        # adding lines in A
        if xa[index_a].startswith('+ ') and xb[index_b].startswith('  '):
            output_lines.append(xa[index_a][2:])
            index_a += 1
            continue

        # adding line in B
        if xb[index_b].startswith('+ ') and xa[index_a].startswith('  '):
            output_lines.append(xb[index_b][2:])
            index_b += 1
            continue

        # if re.search("//[\s\t]*\$.*\$", xa[index_a][2:0]):
            # print(re.search("//[\s\t]*\$.*\$", xa[index_a][2:0]))

        # conflict - list both A and B, similar to GNU's diff3
        # output_lines.append("<<<<<<< A\n")
        # counter_a = 0
        # while (index_a < len(xa)) and not xa[index_a].startswith('  '):
        #     if xa[index_a].startswith('- ') and xa[index_a+1].startswith('+ '):
        #         index_a += 1
        #         continue
        #     output_lines.append(xa[index_a][2:].replace("\n", "") + " >a:" + str(index_a) + ",b:" + str(index_b) + "\n")
        #     index_a += 1
        #     counter_a += 1
        # output_lines.append("=======\n")
        # counter_b = 0
        # while (index_b < len(xb)) and not xb[index_b].startswith('  '):
        #     if xb[index_b].startswith('- ') and xb[index_b+1].startswith('+ '):
        #         index_b += 1
        #         continue
        #     output_lines.append(xb[index_b][2:].replace("\n", "") + " >a:" + str(index_a) + ",b:" + str(index_b) + "\n")
        #     index_b += 1
        #     counter_b += 1
        #     if counter_b == counter_a:
        #             break
        # output_lines.append(">>>>>>> B\n")
        had_conflict = True
        break

    # append remining lines - there will be only either A or B
    for i in range(len(xa) - index_a):
        output_lines.append(xa[index_a + i][2:])
    for i in range(len(xb) - index_b):
        output_lines.append(xb[index_b + i][2:])

    if True: # TODO: Replace by not had_conflict
        output_file = open(output, 'w')
        for line in output_lines:
            output_file.write(line)
        output_file.close()

    return had_conflict
