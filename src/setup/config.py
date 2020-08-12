import basicinput as input

def config_setup_flow(config_dict):
    """ Interactive setup for changing key-value pairs in config_dict

    :param config_dict: the config dictionary
    :type config_dict: dict
    """
    mod_folder_bool = False
    if "__default_folder_name" in config_dict:
        print("Modify default folder name? (y/N)")
        mod_folder_bool = input.yes_no_input()
    else:
        print("No default folder name found.")
        mod_folder_bool = True
    if mod_folder_bool:
        print("Please type the new default folder name...")
        config_dict["__default_folder_name"] = input.text_input()
    print("Add/modify default payment account? (y/N)")
    if input.yes_no_input():
        print("Please type the new default payment account...")
        config_dict["__default_payment"] = input.text_input().lower()
    print("Add/modify default transfer sending account? (y/N)")
    if input.yes_no_input():
        print("Please type the new default transfer sending account...")
        config_dict["__default_from_account"] = input.text_input().lower()
    print("Add/modify default transfer receiving account? (y/N)")
    if input.yes_no_input():
        print("Please type the new default transfer receiving account...")
        config_dict["__default_to_account"] = input.text_input().lower()
    print("Saving updated config...")
    outstr = ""
    for key in config_dict:
        outstr += key + ":" + config_dict[key] + "\n"
    with open("config.ini","w") as configfile:
        configfile.write(outstr)
