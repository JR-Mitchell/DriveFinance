import config
import basicinput as input
import reports
import shortcuts
import src.gdrive.drivefolder as odf
import src.financedata as fdat
import os, datetime

def default_setup_flow(foldername=None):
    """ Interactive setup for the user.
    Called with --setup argument.

    :param foldername: the name of the drive folder,
        defaults to None (in which case, if a config.ini exists, the default
        folder name in it is used, and otherwise config setup is executed to
        get a default folder name set up.)
    :type foldername: str, optional
    """
    config_already_done = False
    #If necessary, generate defaults
    try:
        with open("config.ini","r") as configfile:
            config_txt = configfile.read()
        config_dict = dict([
            item.split(":")
            for item in config_txt.split("\n")
            if len(item.split(":")) == 2])
    except IOError:
        print("No config.ini found. Running config setup...")
        config_dict = {
            "__default_payment":"__default_payment",
            "__default_to_account":"__default_to_account",
            "__default_from_account":"__default_from_account"}
        config.config_setup_flow(config_dict)
        config_already_done = True
    if foldername is None:
        foldername = config_dict["__default_folder_name"]
    #Create an auth token
    drive_folder = odf.DriveFolder(foldername)
    #Create missing subdirectories and files on machine
    dirlist = os.listdir(os.getcwd())
    for folder_name in ["databases","templates","report_json"]:
        if folder_name not in dirlist:
            print("Creating '{}' folder".format(folder_name))
            os.mkdir(folder_name)
    #Opt: modify defaults
    if not config_already_done:
        print("Do you wish to modify the values in config.ini? (y/N)")
        if input.yes_no_input():
            config.config_setup_flow(config_dict)
    #Opt: initialise financial account(s)
    print("Do you wish to initialise a financial account? (y/N)")
    finance_init = input.yes_no_input()
    if finance_init:
        finance_data = fdat.FinanceData(foldername)
        while(finance_init):
            print("Which account would you like to set the"
                + " initial balance for?")
            account_name = input.text_input()
            print("What is the initial balance for '{}'".format(account_name))
            balance = input.money_input()
            init_time = datetime.datetime.now()
            finance_data.set_initial_balance(
                account_name,
                balance,
                init_time)
            print("Set initial balance of '{}' to {}".format(
                account_name,
                balance))
            print("Do you wish to initialise another financial account? (y/N)")
            finance_init = input.yes_no_input()
    #Opt: initialise shortcut(s)
    print("Do you want to set up payment shortcuts? (y/N)")
    shortcut_init = input.yes_no_input()
    if shortcut_init:
        #Get parsed payments file
        import src.parse.shortcuts as shortparse
        raw_shortcut_file = drive_folder.child_file("Shortcuts")
        parsed_shortcut_file = shortparse.ParsedShortcuts(raw_shortcut_file)
        #Do shortcuts flow
        while shortcut_init:
            shortcuts.shortcut_setup_flow(parsed_shortcut_file)
            print("Do you want to set up another payment shortcut? (y/N)")
            shortcut_init = input.yes_no_input()
        #Save to drive
        write_text = "\r\n".join([line for line in parsed_shortcut_file])
        raw_shortcut_file.write_from_string(write_text)
    #Opt: initialise report(s)
    print("Do you want to create/modify/clone a report? (y/N)")
    report_init = input.yes_no_input()
    while report_init:
        reports.report_setup_flow()
        print("Do you want to set up another report? (y/N)")
        report_init = input.yes_no_input()
