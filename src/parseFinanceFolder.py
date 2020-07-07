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

class InputShortcuts(InputFileReader):
    def __init__(self,child_file):
        super(InputShortcuts,self).__init__(child_file)
        self.dict = dict([[item.strip() for item in line.split(":")] for line in self.lines])

# date:command:recurrenceperiod:recurrencenumber:end
class InputScheduledData(object):
    def __init__(self,child_file,replacementDict):
        today = pd.Timestamp(datetime.datetime.now().date())
        text = child_file.initial_content.lower()
        self.lines = text.strip("\xef").strip("\xbb").strip("\xbf").split("\r\n")
        self.lines_to_process = []
        indices_to_remove = []
        self.send_bool = False
        #get datetimestamp
        dateTimeStampLine = self.lines.pop(0)
        dateTimeStamp = dateTimeStampLine.replace(" ","/").replace(":","/").replace(".","/").strip().split("/")
        dateTimeStamp = dict(zip(("day","month","year","hour","minute","second","microsecond"),[int(item) for item in dateTimeStamp]))
        dateTimeStamp["year"] += 2000
        self.date_time_stamp = pd.Timestamp(**dateTimeStamp)
        for index,line in enumerate(self.lines):
            validpart = line.split("#")[0].strip()
            if validpart != "":
                lineDate,lineCommand,linePeriod,lineNumber,endDate = validpart.split(":")
                ##Check if the date has passed
                endDateBkup = endDate
                lineDate = lineDate.strip().split("/")
                lineDate = dict(zip(("day","month","year"),[int(item) for item in lineDate]))
                lineDate["year"] += 2000
                lineDate = pd.Timestamp(**lineDate)
                endDateIsntNever = False
                if endDate.strip() != "never":
                    endDateIsntNever = True
                    endDate = endDate.strip().split("/")
                    endDate = dict(zip(("day","month","year"),[int(item) for item in endDate]))
                    endDate["year"] += 2000
                    endDate = pd.Timestamp(**endDate)
                if today > lineDate:
                    self.send_bool = True
                    ##Update the date
                    kwds = {linePeriod:int(lineNumber)}
                    diff = pd.tseries.offsets.DateOffset(**kwds)
                    newDate = lineDate + diff
                    if endDateIsntNever and newDate > endDate:
                        indices_to_remove.insert(0,index)
                    else:
                        self.lines[index] = ":".join([
                            newDate.strftime("%d/%m/%y"),
                            lineCommand,
                            linePeriod,
                            lineNumber,
                            endDateBkup
                        ])
                        if len(line.split("#")) > 1:
                            self.lines[index] += "#"
                            self.lines[index] += "#".join(line.split("#")[1:])
                    ##Add to lines_to_process
                    if lineCommand[0] == "*":
                        if lineCommand in replacementDict:
                            self.lines_to_process.append([replacementDict[lineCommand],lineDate])
                        else:
                            raise Exception("No valid shortcut for the line '{}'".format(line))
                    else:
                        self.lines_to_process.append([lineCommand,lineDate])
        for index in indices_to_remove:
            del self.lines[index]
        for index,line in enumerate(self.lines_to_process):
                self.parse_payment_line(line,index)
        #storing object variables
        finance_grid = zip(*self.lines_to_process)
        finance_grid = zip(("amount","from","to","id_time","date_made","type"),finance_grid)
        self.read_payments = pd.DataFrame(OrderedDict(finance_grid))
        if self.send_bool:
            self.new_file_text = pd.Timestamp.now().strftime("%d/%m/%y %H:%M:%S.%f")+"\n"
        else:
            self.new_file_text = self.date_time_stamp.strftime("%d/%m/%y %H:%M:%S.%f")+"\n"
        for line in self.lines:
            self.new_file_text += line + "\n"

    def parse_payment_line(self,lineobj,index):
        line,dateNow = lineobj
        purchase = re.search(r"^(?:spent\s)?(£?\d+(?:.\d\d)?)(?:\sspent)?\son\s(.+?)(?:(?:\spaid)?\s(?:by|from|using)(\s.+?)?)?$",line.strip())
        if purchase:
            #Purchase. Format: {amount} (spent) on {object} (paid) (by|from|using) {payment method}
            amountSpent = float(purchase.group(1).strip("£"))
            spentOn = purchase.group(2).strip()
            payMethod = "__default_payment"
            if purchase.group(3) is not None:
                payMethod = purchase.group(3).strip()
            self.lines_to_process[index] = [amountSpent,payMethod,spentOn,self.date_time_stamp,dateNow,"scheduled_purchase"]
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
                self.lines_to_process[index] = [amountTransferred,outAccount,inAccount,self.date_time_stamp,dateNow,"scheduled_transfer"]
            else:
                raise Exception("No valid format for the line '{}'".format(line))


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
    def __init__(self,child_file,replacementDict):
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
            elif line[0] == "*": #a shortcut
                if line.strip() in replacementDict:
                    self.parse_payment_line(replacementDict[line.strip()],index)
                else:
                    raise Exception("No valid shortcut for the line '{}'".format(line))
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
        self.shortcut_file = self.odf_folder.child_file("Shortcuts")
        self.schedule_file = self.odf_folder.child_file("Scheduled Payments")
        self.parsed_shortcut_file = InputShortcuts(self.shortcut_file)
        self.parsed_payment_file = InputPaymentData(self.payment_file,self.parsed_shortcut_file.dict)
        self.parsed_schedule_file = InputScheduledData(self.schedule_file,self.parsed_shortcut_file.dict)

    def update_schedule_file(self):
        self.schedule_file.write_from_string(self.parsed_schedule_file.new_file_text)

    @property
    def read_payments(self):
        return self.parsed_payment_file.read_payments

    @property
    def scheduled_payments(self):
        return self.parsed_schedule_file.read_payments

    @property
    def timestamp(self):
        return self.parsed_payment_file.timestamp

    @property
    def scheduled_timestamp(self):
        return self.parsed_schedule_file.date_time_stamp

    @property
    def send_bool(self):
        return self.parsed_payment_file.send_bool

    @property
    def additional_text(self):
        return self.parsed_payment_file.additional_text

