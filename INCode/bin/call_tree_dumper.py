#!/usr/bin/env python3

from INCode.call_tree_manager import CallTreeManager
from optparse import OptionParser


# TODO(KNR): rewrite to use tui's view model
def main():
    parser = OptionParser('usage: %prog [options] entry-point {file.cpp|compile_commands.json} [extra-clang-args*]')
    parser.add_option('', '--include-system-headers', action="store_true",
                      dest='include_system_headers', default=False,
                      help='Include calls into system headers from the call-tree')
    # parser.add_option('', '--max-depth', dest='maxDepth',
    #                   help='Limit cursor expansion to depth N',
    #                   metavar='N', type=int, default=None)
    parser.disable_interspersed_args()
    (opts, args) = parser.parse_args()

    if len(args) < 2:
        parser.error('invalid number arguments')

    manager = CallTreeManager()
    extra_arguments = args[2:] if len(args) > 2 else None
    print(manager.dump(entry_point=args[0], file_name=args[1],
                       include_system_headers=opts.include_system_headers,
                       extra_arguments=extra_arguments))


if __name__ == '__main__':
    main()
