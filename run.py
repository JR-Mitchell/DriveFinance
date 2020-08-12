# -*- coding: utf-8 -*-

##When run without args this calls the default reading in - report out protocol as configured
##When run with args:
#   -h --help: shows help info
#   -t --tamper: allows access to data in order to make changes
#   -d --defaults: provides config.ini with the default config options

import src.financedata as fdat

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-t','--tamper',action='store_const',const=True,help='open a UI for modifying stored financial data')
    parser.add_argument('-d','--defaults',action='store_const',const=True,help='reset config.ini to contain the default configuration options')
    parser.add_argument('-nr','--noreport',action='store_const',const=True,help='override default behaviour to prevent the generation of reports')
    parser.add_argument('-ni','--noinput',action='store_const',const=True,help='override default behaviour to prevent the reading of drive input files')
    args = vars(parser.parse_args())
    args = [item for item in args if args[item]]

    my_folder = fdat.FinanceData("JR Finances")
    if "defaults" in args:
        print("Argument '--defaults' not yet implemented.")
        parser.print_help()
    if "noinput" not in args:
        my_folder.read_drive_files()
    if "noreport" not in args:
        my_folder.generate_default_reports()
    if "tamper" in args:
        my_folder.open_dialogue()
    print("All commands processed. Thank you for running!")
