# -*- coding: utf-8 -*-

import src.openDocFiles as odf
import re, datetime
from collections import OrderedDict
import pandas as pd

DEFAULT_TIME = [("hour",12),("minute",0),("second",0)]

###
# {amount} (spent) on {object} (paid) (by|from|using) {payment method}
# {amount} (transferred) from {account} (transferred) to {target}

class ParsedFinanceFolder():
    def __init__(self,folder_name):
        self.odf_folder = odf.DocFolder(folder_name)
        self.payment_file = self.odf_folder.child_file("Payments")
        self.read_payments,self.timestamp,self.send_bool = self.parse_string_text(self.payment_file.initial_content)

    @classmethod
    def parse_string_text(cls,text):
        text = text.lower()
        lines = text.strip("\xef").strip("\xbb").strip("\xbf").split("\r\n")
        lines = [line.split("#")[0].strip() for line in lines]
        lines = [line for line in lines if line != ""]
        timestamp = None
        timestampindex = None
        time_and_date_stamp = None
        date_stamp = None
        send_bool = False
        control_indices = []
        for index, line in enumerate(lines):
            if line[0] == "[": #a control tag
                control_indices.insert(0,index)
                if "timestamp of last calculation:" in line:
                    if timestamp is not None:
                        raise Exception("Timestamp defined multiple times!")
                    timestamp = line.strip("[]").replace("timestamp of last calculation:","").strip()
                    timestamp = timestamp.replace(".",":").split(":")
                    timestamp = zip(("hour","minute","second","microsecond"),[int(item) for item in timestamp])
                    timestampindex = index
                elif "datenow:" in line:
                    date_stamp = line.strip("[]").replace("datenow:","").strip().split("/")
                    date_stamp = zip(("day","month","year"),[int(item) for item in date_stamp])
                    if time_and_date_stamp is None:
                        if timestamp is None: raise Exception("No valid timestamp found before first datenow!")
                        time_and_date_stamp = dict(list(date_stamp)+list(timestamp))
                        time_and_date_stamp["year"] += 2000
                        time_and_date_stamp = pd.Timestamp(**time_and_date_stamp)
                    date_stamp = dict(list(date_stamp)+list(DEFAULT_TIME))
                    date_stamp["year"] += 2000
                    date_stamp = pd.Timestamp(**date_stamp)
                elif line.lower() == "[send]":
                    send_bool = True
                else:
                    raise Exception("No valid format for the line '{}'".format(line))
            else:
                purchase = re.search(r"^(?:spent\s)?(£?\d+(?:.\d\d)?)(?:\sspent)?\son\s(.+?)(?:(?:\spaid)?\s(?:by|from|using)(\s.+?)?)?$",line.strip())
                if purchase:
                    #Purchase. Format: {amount} (spent) on {object} (paid) (by|from|using) {payment method}
                    amountSpent = float(purchase.group(1).strip("£"))
                    spentOn = purchase.group(2).strip()
                    payMethod = "__default_payment"
                    if purchase.group(3) is not None:
                        payMethod = purchase.group(3).strip()
                    lines[index] = [amountSpent,payMethod,spentOn,time_and_date_stamp,date_stamp,"purchase"]
                else:
                    transfer = re.search(r"^(£?\d+(?:.\d\d)?)(?:(?:\stransferred|\staken(?:\sout)?)?\sfrom\s(.+?))?(?:(?:\stransferred)?\sto\s(.+?))?(\staken\sout)?$",line.strip())
                    if transfer:
                        #Transfer. Format: {amount} (transferred|taken (out)) from {account} (transferred) to {target}
                        amountTransferred = float(purchase.group(1).strip("£"))
                        if purchase.group(2) is None and purchase.group(3) is None and purchase.group(4) is None:
                            raise Exception("No valid format for the line '{}'".format(line))
                        outAccount = "__default_from_account"
                        inAccount = "__default_to_account"
                        if purchase.group(2) is not None:
                            outAccount = purchase.group(2).strip()
                        if purchase.group(3) is not None:
                            inAccount = purchase.group(3).strip()
                        lines[index] = [amountSpent,payMethod,spentOn,time_and_date_stamp,date_stamp,"transfer"]
                    else:
                        raise Exception("No valid format for the line '{}'".format(line))
        for index in control_indices:
            del lines[index]
        finance_grid = zip(*lines)
        finance_grid = zip(("amount","from","to","id_time","date_made","type"),finance_grid)
        finance_grid = pd.DataFrame(OrderedDict(finance_grid))
        return finance_grid,time_and_date_stamp,send_bool
