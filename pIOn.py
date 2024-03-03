#!/usr/bin/python3
import sys
import Options as op
import Checker as check
from Parser import to_parse_blk_info
from CSVParser import traces_to_csv
from TraceProcess import trace_process
from PostProcess import post_process


def main(argv):
    g = op.pIONOptions()
    print("pIOn is running, VERSION: ", g.version)

    check.check_args(g, argv)

    match g.mode:
        case 'parse':
            to_parse_blk_info(g)
        case 'csv':
            traces_to_csv(g)
        case 'trace':
            trace_process(g)
        case 'post':
            post_process(g)
        case _:
            print("ERROR")

    sys.exit()


if __name__ == "__main__":
    main(sys.argv[1:])
