# -*- coding: utf-8 -*-

##When run without args this calls the default reading in - report out protocol as configured
##When run with args:
#   -h --help: shows help info
#   -t --tamper: allows access to data in order to make changes
#   -d --defaults: provides config.ini with the default config options

import src.readMoneyUpdates as rmu

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-t','--tamper',action='store_const',const=True,help='open a UI for modifying stored financial data')
    parser.add_argument('-d','--defaults',action='store_const',const=True,help='reset config.ini to contain the default configuration options')
    args = vars(parser.parse_args())
    args = [item for item in args if args[item]]
    if len(args) == 0:
        myFolder = rmu.FinanceInfoObject("JR Finances")
        print(myFolder.read_payments.to_string())
    elif len(args) == 1:
        if args[0] == "tamper":
            print("not yet implemented!")
            parser.print_help()
        elif args[0] == "defaults":
            print("not yet implemented!")
            parser.print_help()
        else:
            print("something has gone horribly wrong...")
            parser.print_help()
    else:
        print("use zero or one optional arguments")
        parser.print_help()
