#!/usr/bin/python

import sys
import os


def do_trans(input, output):

    i_file = open(input, 'r')
    o_file = open(output, 'w')

    count = 0
    try:
        for line in i_file:
            count += 1
            new = line

            # TODO: check if line is in code block
            if line.startswith('#+SETUPFILE') or line.startswith('#+DATE') \
               or line.startswith('#+TITLE'):
                continue
            # TODO: use regex to improve performance
            if line.startswith('*'):
                # The translation of title is:
                # '* title' ==> '===== title ====='
                # '** title' ==> '==== title ===='
                # '*** title' ==> '=== title ==='
                # '**** title' ==> '== title =='
                # '***** title' ==> '= title ='
                # We only allow 5 level title now
                count = len(line.split()[0])
                title = line[count:].strip()
                s = '=' * (6 - count)

                new = '%s %s %s\n' % (s, title, s)
            elif line.lower().startswith('#+begin_src'):
                new = '<code>\n'
            elif line.lower().startswith('#+end_src'):
                new = '</code>\n'
            elif line.lower().startswith('#+begin_example'):
                new = '<code>\n'
            elif line.lower().startswith('#+end_example'):
                new = '</code>\n'
            else:
                new = new.lstrip()

            o_file.write(new)
    except:
        print 'error with line %d:\n%s' % (count, line)
        pass
    finally:
        i_file.close()
        o_file.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print 'please provide org filename'
        sys.exit(1)

    input = sys.argv[1]
    output = os.path.basename(input) + '.ts'
    do_trans(input, output)
