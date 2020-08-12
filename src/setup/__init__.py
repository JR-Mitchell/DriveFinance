import config
import basicinput as input
import src.gdrive.drivefolder as odf

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
    #Generate missing drive files &/ folders
    for item in ["Shortcuts","Balances","Payments","Scheduled"]:
        if item not in drive_folder.subitem_dict:
            assert False, "Not yet implemented!"
    #Create missing files &/ folders in the drive
    #Create missing subdirectories and files on machine
    #Opt: modify defaults
    if not config_already_done:
        print("Do you wish to modify the values in config.ini? (y/N)")
        if input.yes_no_input():
            config.config_setup_flow(config_dict)
    #Opt: initialise financial account(s)
    #Opt: initialise shortcut(s)
    #Opt: initialise report(s)
