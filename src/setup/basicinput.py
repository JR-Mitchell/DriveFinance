#-*- encoding: utf-8 -*-
import src.regex.patterns as patterns
import re
import pandas as pd

RESERVED_CHARACTERS = [
    ':','"','%','*',
    '(',')','{','}',
    '[',']','@','\'',
    '#','\\','|','.','/']

YES_ALTERNATIVES = ["yes"]
NO_ALTERNATIVES = ["no"]

def yes_no_input():
    """ Prompts the user for a yes/no response

    :returns: whether the user responded yes
    :rtype: bool
    """
    code = raw_input().strip().lower()
    while (
        code != 'y' and
        code != 'n' and
        code not in YES_ALTERNATIVES + NO_ALTERNATIVES):
        print("Unrecognised input!"
            + " Please type 'y' or 'Y' for yes, 'n' or 'N' for no")
        code = raw_input().strip().lower()
    return (code == 'y' or code in YES_ALTERNATIVES)

def text_input():
    """ Prompts the user to input text excluding reserved characters

    :returns: the user's valid input
    :rtype: str
    """
    code = raw_input().strip()
    while any([character in RESERVED_CHARACTERS for character in code]):
        print("Please refrain from using any of the"
            + " following reserved characters:")
        print(RESERVED_CHARACTERS)
        code = raw_input().strip()
    return code

def money_input():
    """ Prompts the user to input text denoting an amount of money

    :returns: the amount of money
    :rtype: float
    """
    code = raw_input().strip()
    while not(re.match(patterns.CASH_AMOUNT,code)):
        print("Please put in a valid amount of money (e.g '£15' or '103.32')")
        code = raw_input().strip()
    return float(code.strip("£"))

def frequency_input():
    """ Prompts the user to input text denoting a pandas frequency string

    :returns: the frequency string
    :rtype: str
    """
    code = raw_input().strip()
    while True:
        try:
            pd.Period(freq=code)
            break
        except ValueError:
            print("Please put in a valid pandas frequency string.")
            print("See relevant documentation at:")
            print("https://pandas.pydata.org/pandas-docs/stable/user_guide/"
                + "timeseries.html#offset-aliases")
            code = raw_input().strip()
    return code

def int_input():
    """ Prompts the user to input text denoting an integer

    :returns: the integer denoted
    :rtype: int
    """
    code = raw_input().strip()
    while True:
        try:
            value = int(code)
            break
        except ValueError:
            print("Please input a valid integer (whole number).")
            code = raw_input().strip()
    return value
