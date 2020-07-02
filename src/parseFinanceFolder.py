# -*- coding: utf-8 -*-

import src.openDocFiles as odf
import re, datetime
from collections import OrderedDict
import pandas as pd

DEFAULT_TIME = [("hour",12),("minute",0),("second",0)]


class InputFileReader(object):
    def __init__(self,child_file):
        text = child_file.initial_content.lower()
        lines = text.strip("\xef").strip("\xbb").strip("\xbf").split("\r\n")
        lines = [line.split("#")[0].strip() for line in lines]
        self.lines = [line for line in lines if line != ""]

    def __getitem__(self,arg):
        return self.lines[arg]

    def __iter__(self):
        return iter(self.lines)

###
# {amount} (spent) on {object} (paid) (by|from|using) {payment method}
# {amount} (transferred) from {account} (transferred) to {target}
class InputPaymentData(InputFileReader):
    """
        self.read_payments
        self.send_bool
        self.timestamp
        self.additional_text
        self.lines
    """
    def __init__(self,child_file):
        super(InputPaymentData,self).__init__(child_file)
        #Setting up variables for this initialisation that will have values set to them
        self.additional_text = ""
        self._time_lock_object = {
            "lastCalculationTime":None,
            "indexOfLastCalculationTimestamp":None,
            "lastCalculationDateTime":None,
            "dateNow":None
        }
        self.send_bool = False
        control_indices = []
        #Passing through the lines and parsing them one by one
        for index, line in enumerate(self.lines):
            if self.send_bool: #Ensures only lines before the send token are processed for the current run and removed from the drive-facing file
                control_indices.insert(0,index)
                self.additional_text += line
                self.additional_text += "\n"
            elif line[0] == "[": #a control tag
                control_indices.insert(0,index)
                self.parse_control_tag(line,index)
            else:
                self.parse_payment_line(line,index)
        #getting rid of the "control indices"
        for index in control_indices:
            del self.lines[index]
        #storing object variables
        finance_grid = zip(*self.lines)
        finance_grid = zip(("amount","from","to","id_time","date_made","type"),finance_grid)
        self.read_payments = pd.DataFrame(OrderedDict(finance_grid))
        self.timestamp = self._time_lock_object["lastCalculationDateTime"]

    def parse_control_tag(self,line,index):
        if "timestamp of last calculation:" in line: #modifies timestamp, timestampindex
            if self._time_lock_object["lastCalculationTime"] is not None:
                raise Exception("Timestamp defined multiple times!")
            self._time_lock_object["lastCalculationTime"] = line.strip("[]").replace("timestamp of last calculation:","").strip()
            self._time_lock_object["lastCalculationTime"] = self._time_lock_object["lastCalculationTime"].replace(".",":").split(":")
            self._time_lock_object["lastCalculationTime"] = zip(("hour","minute","second","microsecond"),[int(item) for item in self._time_lock_object["lastCalculationTime"]])
            self._time_lock_object["indexOfLastCalculationTimestamp"] = index
        elif "datenow:" in line: #modifies date_stamp, time_and_date_stamp
            self._time_lock_object["dateNow"] = line.strip("[]").replace("datenow:","").strip().split("/")
            self._time_lock_object["dateNow"] = zip(("day","month","year"),[int(item) for item in self._time_lock_object["dateNow"]])
            if self._time_lock_object["lastCalculationDateTime"] is None:
                if self._time_lock_object["lastCalculationTime"] is None: raise Exception("No valid timestamp found before first datenow!")
                self._time_lock_object["lastCalculationDateTime"] = dict(list(self._time_lock_object["dateNow"])+list(self._time_lock_object["lastCalculationTime"]))
                self._time_lock_object["lastCalculationDateTime"]["year"] += 2000
                self._time_lock_object["lastCalculationDateTime"] = pd.Timestamp(**self._time_lock_object["lastCalculationDateTime"])
            self._time_lock_object["dateNow"] = dict(list(self._time_lock_object["dateNow"])+list(DEFAULT_TIME))
            self._time_lock_object["dateNow"]["year"] += 2000
            self._time_lock_object["dateNow"] = pd.Timestamp(**self._time_lock_object["dateNow"])
        elif line.lower() == "[send]": #modifies self.send_bool, additional_text
            self.send_bool = True
            self.additional_text += "[datenow: {}]\n".format(self._time_lock_object["dateNow"].strftime("%d/%m/%y"))
        else:
            raise Exception("No valid format for the line '{}'".format(line))

    def parse_payment_line(self,line,index):
        purchase = re.search(r"^(?:spent\s)?(£?\d+(?:.\d\d)?)(?:\sspent)?\son\s(.+?)(?:(?:\spaid)?\s(?:by|from|using)(\s.+?)?)?$",line.strip())
        if purchase:
            #Purchase. Format: {amount} (spent) on {object} (paid) (by|from|using) {payment method}
            amountSpent = float(purchase.group(1).strip("£"))
            spentOn = purchase.group(2).strip()
            payMethod = "__default_payment"
            if purchase.group(3) is not None:
                payMethod = purchase.group(3).strip()
            self.lines[index] = [amountSpent,payMethod,spentOn,self._time_lock_object["lastCalculationDateTime"],self._time_lock_object["dateNow"],"purchase"]
        else:
            transfer = re.search(r"^(£?\d+(?:.\d\d)?)(?:(?:\stransferred|\staken(?:\sout)?)?\sfrom\s(.+?))?(?:(?:\stransferred)?\sto\s(.+?))?(\staken\sout)?$",line.strip())
            if transfer:
                #Transfer. Format: {amount} (transferred|taken (out)) from {account} (transferred) to {target}
                amountTransferred = float(transfer.group(1).strip("£"))
                if transfer.group(2) is None and transfer.group(3) is None and transfer.group(4) is None:
                    raise Exception("No valid format for the line '{}'".format(line))
                outAccount = "__default_from_account"
                inAccount = "__default_to_account"
                if transfer.group(2) is not None:
                    outAccount = transfer.group(2).strip()
                if transfer.group(3) is not None:
                    inAccount = transfer.group(3).strip()
                self.lines[index] = [amountTransferred,outAccount,inAccount,self._time_lock_object["lastCalculationDateTime"],self._time_lock_object["dateNow"],"transfer"]
            else:
                raise Exception("No valid format for the line '{}'".format(line))


class ParsedFinanceFolder(object):
    def __init__(self,folder_name):
        self.folder_name = folder_name
        self.odf_folder = odf.DocFolder(folder_name)
        self.payment_file = self.odf_folder.child_file("Payments")
        self.parsed_payment_file = InputPaymentData(self.payment_file)

    #Following code should, at some point, be deprecated

    @property
    def read_payments(self):
        return self.parsed_payment_file.read_payments

    @property
    def timestamp(self):
        return self.parsed_payment_file.timestamp

    @property
    def send_bool(self):
        return self.parsed_payment_file.send_bool

    @property
    def additional_text(self):
        return self.parsed_payment_file.additional_text

