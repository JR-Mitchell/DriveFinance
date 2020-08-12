# -*- coding: utf-8 -*-

##When run without args this calls the default reading in - report out protocol as configured
##When run with args:
#   -h --help: shows help info
#   -t --tinker: allows access to data in order to make changes
#   -d --defaults: provides config.ini with the default config options

import src.financedata as fdat

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-t','--tinker',action='store_const',const=True,help='open a UI for modifying stored financial data')
    parser.add_argument('-d','--defaults',action='store_const',const=True,help='reset config.ini to contain the default configuration options')
    parser.add_argument('-nr','--noreport',action='store_const',const=True,help='override default behaviour to prevent the generation of reports')
    parser.add_argument('-ni','--noinput',action='store_const',const=True,help='override default behaviour to prevent the reading of drive input files')
    args = vars(parser.parse_args())
    args = [item for item in args if args[item]]

    finance_data = fdat.FinanceData("JR Finances")
    if "defaults" in args:
        print("Argument '--defaults' not yet implemented.")
        parser.print_help()
    if "noinput" not in args:
        finance_data.read_drive_files()
    if "noreport" not in args:
        finance_data.generate_default_reports()
    if "tinker" in args:
        finance_data.open_dialogue()
    print("All commands processed. Thank you for running!")
