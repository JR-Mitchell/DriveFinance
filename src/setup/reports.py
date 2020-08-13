import basicinput as input
import json, os

def report_setup_flow():
    """ Interactive setup for creating, cloning or modifying a report
    """
    report_names = [item[:-5] for item in os.listdir("report_json/")]
    print("\nReport Setup\n============\n")
    print("You may create, clone or modify a report,"
        + " or cancel out of this dialogue.")
    dokey = ""
    modify_name = None
    while True:
        print("Do you want to create a new report? (y/N)")
        if input.yes_no_input():
            dokey = "create"
            break
        print("Do you want to clone an existing report? (y/N)")
        if input.yes_no_input():
            dokey = "clone"
            break
        print("Do you want to modify an existing report? (y/N)")
        if input.yes_no_input():
            dokey = "modify"
            break
        print("Do you want to exit this dialogue? (y/N)")
        if input.yes_no_input():
            dokey = "leave"
            break
    if dokey == "create":
        print("What should the new report be named?")
        new_name = input.text_input()
        while new_name in report_names:
            print("The name you gave ({})".format(clone_name)
                + " is already a recognised report name."
                + " Please input an original name.")
            print("Existing reports are:")
            print(report_names)
        report_creation_flow(new_name)
    if dokey == "clone":
        print("Existing reports are:")
        print(report_names)
        print("Which report would you like to clone?")
        clone_name = input.text_input()
        while clone_name not in report_names:
            print("The name you gave ({})".format(clone_name)
                + " is not a recognised report name.")
            print("Existing reports are:")
            print(report_names)
        print("Selected '{}' to clone".format(clone_name))
        print("What should the cloned report be named?")
        new_name = input.text_input()
        while new_name in report_names:
            print("The name you gave ({})".format(clone_name)
                + " is already a recognised report name."
                + " Please input an original name.")
            print("Existing reports are:")
            print(report_names)
        with open("report_json/{}.json".format(clone_name),"r") as infile:
            clone_file_txt = infile.read()
        with open("report_json/{}.json".format(new_name),"w") as outfile:
            outfile.write(clone_file_txt)
        print("Successfully cloned '{}' to '{}'.".format(clone_name,new_name)
            + " Would you like to further modify '{}'? (y/N)".format(new_name))
        if input.yes_no_input():
            dokey = "modify"
            modify_name = new_name
    if dokey == "modify":
        if modify_name is None:
            print("Existing reports are:")
            print(report_names)
            print("Which report would you like to modify?")
            modify_name = input.text_input()
            while modify_name not in report_names:
                print("The name you gave ({})".format(modify_name)
                    + " is not a recognised report name.")
                print("Existing reports are:")
                print(report_names)
        report_modification_flow(modify_name)

def report_creation_flow(report_name):
    """ Interactive setup for creating a report

    :param report_name: the name of the report to create
    :type report_name: str
    """
    print("Creating report '{}'\n".format(report_name))
    report_json = {}
    print("Do you want this report to be generated automatically? (y/N)")
    if input.yes_no_input():
        report_json["autodo"] = 1
    print("What period of time should this report cover?")
    report_json["frequency"] = input.frequency_input()
    print("Should this report be offset a certain number of periods from the"
        + " current date? (y/N)")
    if input.yes_no_input():
        print("How many periods in the past should this report be?")
        report_json["offset"] = input.int_input()
    report_json["sections"] = []
    report_sections_flow(report_json)
    print("Saving report...")
    with open("report_json/{}.json".format(report_name),"w") as outfile:
        json.dump(report_json,outfile)
    print("Successfully created report '{}'\n".format(report_name))

def report_modification_flow(report_name):
    """ Interactive setup for modifying a report

    :param report_name: the name of the report to modify
    :type report_name: str
    """
    with open("report_json/{}.json".format(report_name),"r") as infile:
        report_json = json.load(infile)
    print("Modifying report '{}'\n".format(report_name))
    if "autodo" in report_json:
        print("'autodo' is set to '{}'. Change it to '{}'? (y/N)".format(
            report_json["autodo"],
            1 - report_json["autodo"]))
        if input.yes_no_input():
            report_json["autodo"] = 1 - report_json["autodo"]
    else:
        print("No 'autodo' tag found."
            + " Do you want this report to be generated automatically? (y/N)")
        if input.yes_no_input():
            report_json["autodo"] = 1
    if "frequency" in report_json:
        announce_str = ("'frequency' is set to '{}'."
            + " This represents the period of the time that the report covers."
            + " Do you wish to change it? (y/N)")
        announce_str = announce_str.format(report_json["frequency"])
        print(announce_str)
        if input.yes_no_input():
            print("What period of time should this report cover?")
            report_json["frequency"] = input.frequency_input()
    else:
        print("No 'frequency' tag found."
            + " What should the frequency tag be?")
        report_json["frequency"] = input.frequency_input()
    if "offset" in report_json:
        announce_str = ("'offset' is set to '{}'."
            + " Do you wish to change it? (y/N)")
        announce_str = announce_str.format(report_json["offset"])
        print(announce_str)
        if input.yes_no_input():
            print("What should the new offset tag be?")
            report_json["offset"] = input.int_input()
    else:
        print("No 'offset' tag found."
            + " Should this report be offset a certain number of periods from"
            + " the current date? (y/N)")
        if input.yes_no_input():
            print("How many periods in the past should this report be?")
            report_json["offset"] = input.int_input()
    print("Do you wish to modify the sections in this report? (y/N)")
    if input.yes_no_input():
        if "sections" not in report_json:
            report_json["sections"] = []
        report_sections_flow(report_json)
    print("Saving report...")
    with open("report_json/{}.json".format(report_name),"w") as outfile:
        json.dump(report_json,outfile)
    print("Done modifying report '{}'\n".format(report_name))

def report_sections_flow(report_json):
    """ Interactive setup for modifying sections of a report

    :param report_json: the loaded json of the report
    :type report_json: dict
    """
    print("\nModifying report sections\n=========================\n")
    while True:
        print("Current sections:")
        for i,item in enumerate(report_json["sections"]):
            print("{}: {}".format(i,item[0]))
        print("\nYou may add, modify or delete a section,"
            + " or cancel out of this dialogue.")
        print("Do you want to add a section? (y/N)")
        if input.yes_no_input():
            print("At which index should this section be added?")
            modify_index = input.int_input()
            report_json["sections"].insert(modify_index,create_section_flow())
            continue
        if len(report_json["sections"]) == 0:
            print("No sections left to modify / delete!")
        else:
            print("Do you want to modify a section? (y/N)")
            if input.yes_no_input():
                print("Which number section would you like to modify?")
                modify_index = input.int_input()
                while True:
                    try:
                        sec_to_modify = report_json["sections"][modify_index]
                        break
                    except:
                        print("The index you gave ({})".format(modify_index)
                            + " is not a valid index.")
                        modify_index = input.int_input()
                report_json["sections"] \
                           [modify_index] = modify_section_flow(sec_to_modify)
                continue
            print("Do you want to delete a section? (y/N)")
            if input.yes_no_input():
                print("Which number section would you like to delete?")
                delete_index = input.int_input()
                while True:
                    try:
                        del report_json["sections"][delete_index]
                        break
                    except:
                        print("The index you gave ({})".format(delete_index)
                            + " is not a valid index.")
                        delete_index = input.int_input()
                continue
        print("Do you want to finish editing sections? (y/N)")
        if input.yes_no_input():
            break

#TODO docstrings
#TODO there's a lot of duplicated code below.
# I'm sure this could be made much neater.
def create_section_flow():
    print("What LaTeX function should this section call?")
    new_section = [input.text_input()]
    print("How many arguments does {} take?".format(new_section[0]))
    no_args = input.int_input()
    for i in range(no_args):
        print("Is {} argument {} a value (y),".format(new_section[0],i)
            + "or is it a report function (N)?")
        if input.yes_no_input():
            print("What is the value of argument {}?".format(i))
            new_section.append(input.text_input())
        else:
            new_section.append(create_report_func_flow(i))
            print("Returned to section creation"
                + " for section {}\n".format(new_section[0]))
    return new_section

def create_report_func_flow(index):
    print("What report function is argument {}?".format(index))
    report_function = [input.text_input()]
    print("How many arguments does"
        + " {} take?".format(report_function[0]))
    no_args = input.int_input()
    for i in range(no_args):
        print("Is {} argument {} a value (y),".format(report_function[0],i)
            + "or is it a figure function (N)?")
        if input.yes_no_input():
            print("What is the value of argument {}?".format(i))
            report_function.append(input.text_input())
        else:
            report_function.append(create_figure_func_flow(index,i))
            print("Returned to report function creation"
                + " for report function {}\n".format(report_function[0]))
    return report_function

def create_figure_func_flow(*indices):
    print("What figure function is argument {}?".format(indices))
    figure_function = [input.text_input()]
    print("How many arguments does"
        + " {} take?".format(figure_function[0]))
    no_args = input.int_input()
    for i in range(no_args):
        print("What is the value of argument {}?".format(i))
        figure_function.append(input.text_input())
    return figure_function

def modify_section_flow(section):
    print("This section calls the function {}".format(section[0])
        + "\nWould you like to change that? (y/N)")
    if input.yes_no_input():
        return create_section_flow()
    else:
        while True:
            print("Current arguments:")
            for i,item in enumerate(section[1:]):
                if isinstance(item,list):
                    print("{}: report function '{}'".format(i,item[0]))
                else:
                    print("{}: value '{}'".format(i,item))
            print("Do you wish to modify an argument (y)"
                + " or stop modifying this section (N)?")
            if input.yes_no_input():
                print("Which index argument do you wish to modify?")
                modify_index = input.int_input()
                while True:
                    try:
                        val_to_change = section[modify_index+1]
                        break
                    except:
                        print("The index you gave ({})".format(modify_index)
                            + " is not a valid index.")
                        modify_index = input.int_input()
                replace = True
                if isinstance(val_to_change,list):
                    print("This argument is the"
                        + " report function {}".format(val_to_change[0])
                        + "\nDo you wish to modify this report function (y)"
                        + " or replace it with something else (N)?")
                    if input.yes_no_input():
                        replace = False
                if replace:
                    print("Is argument {} a value (y),".format(modify_index)
                        + "or is it a report function (N)?")
                    if input.yes_no_input():
                        print("What is the value of"
                            + " argument {}?".format(modify_index))
                        section[modify_index+1] = input.text_input()
                    else:
                        section[modify_index+1] = create_report_func_flow(
                            modify_index)
                        print("Returned to section modification"
                            + " for section {}\n".format(section[0]))
                else:
                    section[modify_index+1] = modify_report_func_flow(
                        val_to_change)
                    print("Returned to section modification"
                        + " for section {}\n".format(section[0]))
            else:
                break
    return section

def modify_report_func_flow(report_func):
    print("Now modifying the report function {}".format(report_func[0]))
    while True:
        print("Current report function arguments:")
        for i,item in enumerate(report_func[1:]):
            if isinstance(item,list):
                print("{}: figure function '{}'".format(i,item[0]))
            else:
                print("{}: value '{}'".format(i,item))
        print("Do you wish to modify an argument (y)"
            + " or stop modifying this report function (N)?")
        if input.yes_no_input():
            print("Which index argument do you wish to modify?")
            modify_index = input.int_input()
            while True:
                try:
                    val_to_change = report_func[modify_index+1]
                    break
                except:
                    print("The index you gave ({})".format(modify_index)
                        + " is not a valid index.")
                    modify_index = input.int_input()
            replace = True
            if isinstance(val_to_change,list):
                print("This argument is the"
                    + " figure function {}".format(val_to_change[0])
                    + "\nDo you wish to modify this figure function (y)"
                    + " or replace it with something else (N)?")
                if input.yes_no_input():
                    replace = False
            if replace:
                print("Is argument {} a value (y),".format(modify_index)
                    + "or is it a figure function (N)?")
                if input.yes_no_input():
                    print("What is the value of"
                        + " argument {}?".format(modify_index))
                    report_func[modify_index+1] = input.text_input()
                else:
                    report_func[modify_index+1] = create_figure_func_flow(
                        modify_index)
                    print("Returned to report function modification"
                        + " for report function {}\n".format(report_func[0]))
            else:
                report_func[modify_index+1] = modify_figure_func_flow(
                    val_to_change)
                print("Returned to report function modification"
                    + " for report function {}\n".format(report_func[0]))
        else:
            break
    return report_func

def modify_figure_func_flow(figure_func):
    print("Now modifying the figure function {}".format(figure_func[0]))
    while True:
        print("Current figure function arguments:")
        for i,item in enumerate(figure_func[1:]):
            print("{}: value '{}'".format(i,item))
        print("Do you wish to replace an argument (y)"
            + " or stop modifying this figure function (N)?")
        if input.yes_no_input():
            print("Which index argument do you wish to modify?")
            modify_index = input.int_input()
            while True:
                try:
                    val_to_change = figure_func[modify_index+1]
                    break
                except:
                    print("The index you gave ({})".format(modify_index)
                        + " is not a valid index.")
                    modify_index = input.int_input()
            print("What is the value of argument {}?".format(modify_index))
            figure_func[modify_index+1] = input.text_input()
        else:
            break
    return figure_func
