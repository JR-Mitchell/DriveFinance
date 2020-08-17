# -*- coding: utf-8 -*-

import src.financedata as fdat
import src.setup as setup

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t", "--tinker",
        action = "store_const", const = True,
        help = ("open a UI for calling commands,"
            + " allowing modification of stored financial data"))
    parser.add_argument(
        "-s", "--setup",
        action = "store_const", const = True,
        help=("run setup flow, performing initial setup and/or"
            + " modifying config, initialising accounts,"
            + " initialising shortcuts and "
            + "creating, modifying or cloning reports"))
    mutual_group = parser.add_mutually_exclusive_group()
    mutual_group.add_argument(
        "-nr", "--noreport",
        action = "store_const", const = True,
        help=("suppress generation of default reports."
            + " cannot be used with -r/--report"))
    parser.add_argument(
        "-ni", "--noinput",
        action = "store_const", const = True,
        help="suppress the reading of drive input files")
    mutual_group.add_argument(
        "-r", "--report",
        help = ("generate and upload report with name REPORT."
            + " cannot be used with -nr/--noreport"))
    parser.add_argument(
        "-f", "--foldername",
        help = "run with non-default drive folder FOLDERNAME")
    args = vars(parser.parse_args())
    args = {item:args[item] for item in args if args[item] is not None}

    if "setup" in args:
        if "foldername" in args:
            setup.default_setup_flow(args["foldername"])
        else:
            setup.default_setup_flow()
    if "foldername" in args:
        finance_data = fdat.FinanceData(args["foldername"])
    else:
        finance_data = fdat.FinanceData()
    if "defaults" in args:
        print("Argument '--defaults' not yet implemented.")
        parser.print_help()
    if "noinput" not in args:
        finance_data.read_drive_files()
    if "noreport" not in args and "report" not in args:
        finance_data.generate_default_reports()
    if "report" in args:
        finance_data.generate_report(args["report"])
    if "tinker" in args:
        finance_data.open_dialogue()
    print("All commands processed. Thank you for running!")
