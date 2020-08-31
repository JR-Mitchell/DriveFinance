# -*- coding: utf-8 -*-
import basicinput as input

def shortcut_setup_flow(shortcuts):
    """ Interactive setup for adding payment shortcuts

    :param shortcuts: the parsed shortcuts file
    :type shortcuts: class: `src.parse.shortcuts.ParsedShortcuts`
    """
    #Get shortcut key
    input_fine = False
    while not input_fine:
        print("What would you like the shortcut to be named?")
        print("(Note: all shortcuts start with an asterisk (*)."
            + " One will be added if not given.)")
        shortcut_key = input.text_input()
        if shortcut_key[0] != "*":
            shortcut_key = "*" + shortcut_key
        print("Shortcut key: '{}'. Is this fine? (y/N)".format(shortcut_key))
        input_fine = input.yes_no_input()
    #Is the shortcut a purchase or a transfer?
    input_fine = False
    while not input_fine:
        print("Is the shortcut a purchase or is it a transfer?")
        shortcut_type = input.text_input().lower().strip()
        if shortcut_type in ["purchase","transfer"]:
            print("Shortcut type: '{}'. Is this fine? (y/N)".format(shortcut_type))
            input_fine = input.yes_no_input()
        else:
            print("Please type either 'purchase' or 'transfer'.")
    isTransfer = shortcut_type == "transfer"
    #To account (leave blank for default)
    input_fine = False
    while not input_fine:
        if isTransfer:
            print("Which account are you transferring to?"
                + " (Leave blank for default transfer account)")
        else:
            print("What are you purchasing?")
        to_account = input.text_input().lower().strip()
        if to_account == "":
            if isTransfer:
                to_account = "__default_to_account"
                print("Transferring to default account. Is this fine? (y/N)")
                input_fine = input.yes_no_input()
            else:
                print("Please input a valid (non-blank) purchase item.")
        else:
            if isTransfer:
                print("Transferring to account '{}'.".format(to_account)
                    + " Is this fine? (y/N)")
            else:
                print("Purchasing '{}'.".format(to_account)
                    + " Is this fine? (y/N)")
            input_fine = input.yes_no_input()
    #Get shortcut amount
    input_fine = False
    while not input_fine:
        if isTransfer:
            print("How much money is this transfer?")
        else:
            print("How much does this purchase cost?")
        shortcut_amount = input.money_input()
        print("Amount: '£{}'. Is this fine? (y/N)".format(shortcut_amount))
        input_fine = input.yes_no_input()
    #From account (leave blank for default)
    input_fine = False
    while not input_fine:
        if isTransfer:
            print("Which account are you transferring from?"
                + " (Leave blank for default transfer account)")
        else:
            print("Which account are you using to pay?"
                + " (Leave blank for default payment account)")
        from_account = input.text_input().lower().strip()
        if from_account == "":
            if isTransfer:
                from_account = "__default_from_account"
                print("Transferring from default account. Is this fine? (y/N)")
                input_fine = input.yes_no_input()
            else:
                from_account = "__default_payment"
                print("Paying with default payment account."
                    + " Is this fine? (y/N)")
                input_fine = input.yes_no_input()
        else:
            if isTransfer:
                print("Transferring from account '{}'.".format(from_account)
                    + " Is this fine? (y/N)")
            else:
                print("Paying with account '{}'.".format(from_account)
                    + " Is this fine? (y/N)")
            input_fine = input.yes_no_input()
    #Create shortcut code
    if isTransfer:
        #Transfer: £{amount} transferred from {from_account} to {to_account}
        shortcut_code = "£{} transferred".format(shortcut_amount)
        if from_account != "__default_from_account":
            shortcut_code += " from {}".format(from_account)
        if to_account != "__default_to_account":
            shortcut_code += " to {}".format(to_account)
    else:
        #Payment: £{amount} spent on {item} paid by {account}
        shortcut_code = "£{} spent on {}".format(shortcut_amount,to_account)
        if from_account != "__default_payment":
            shortcut_code += " paid by {}".format(from_account)
    #Add shortcut to file
    shortcuts.add_line(shortcut_key,shortcut_code)
