# -*- coding: utf-8 -*-

##When run without args this calls the default reading in - report out protocol as configured
##When run with args:
#   -h --help: shows help info
#   -t --tinker: allows access to data in order to make changes
#   -d --defaults: provides config.ini with the default config options

import src.financedata as fdat
import src.setup as setup

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-t','--tinker',action='store_const',const=True,help='open a UI for modifying stored financial data')
    parser.add_argument('-s','--setup',action='store_const',const=True,help='perform initial setup, and/or initialise accounts, create reports etc.')
    parser.add_argument('-nr','--noreport',action='store_const',const=True,help='override default behaviour, preventing generation of default reports')
    parser.add_argument('-ni','--noinput',action='store_const',const=True,help='override default behaviour to prevent the reading of drive input files')
    parser.add_argument('-r','--report',help='generates report with name REPORT')
    parser.add_argument('-f','--foldername',help='use non-default drive folder FOLDERNAME')
    args = vars(parser.parse_args())
    args = {item:args[item] for item in args if args[item] is not None}

    if "foldername" in args:
        finance_data = fdat.FinanceData(args["foldername"])
    else:
        finance_data = fdat.FinanceData()
    if "setup" in args:
        setup.default_setup_flow()
    if "defaults" in args:
        print("Argument '--defaults' not yet implemented.")
        parser.print_help()
    if "noinput" not in args:
        finance_data.read_drive_files()
    if "noreport" not in args:
        finance_data.generate_default_reports()
    if "report" in args:
        finance_data.generate_report(args["report"])
    if "tinker" in args:
        finance_data.open_dialogue()
    print("All commands processed. Thank you for running!")
