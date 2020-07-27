# -*- coding: utf-8 -*-

from __future__ import print_function
import datetime,os
import src.parseFinanceFolder as pff
import src.createTexReports as tex
import pandas as pd
import re
import time

def get_clean_slate(additional_str):
    """
    Creates a clean payment sheet to be fed back to the drive.
    """
    now = datetime.datetime.now()
    lastdate = now.strftime("%d/%m/%y")
    if "[datenow: " in additional_str:
        remaining_time_text = additional_str
    else:
        remaining_time_text = "[datenow: {}]\n".format(lastdate)
    timestamp=now.time()
    fdict = {"dbudget":"£10","dremain":"£5","wremain":"£5","remtext":remaining_time_text,"timestamp":timestamp}
    with open("templates/basic_file.txt","r") as myFile:
        template_str = myFile.read()
    return template_str.format(**fdict)

class FinanceInfoObject():
    dialogue_functions = {}
    def __init__(self,foldername):
        self.folder_name = foldername
        self.parsed_folder = None
        self.all_payments = None
        #Get the database
        if os.path.isfile("databases/{}.h5".format(foldername)):
            self.all_payments = pd.read_hdf("databases/{}.h5".format(foldername),"payments")
        #Read in the config
        self.config = {}
        configtxt = ""
        with open("config.ini","r") as configFile:
            configtxt = configFile.read()
        self.config = dict([item.split(":") for item in configtxt.split("\n") if len(item.split(":")) == 2])
        self.report_config = {}
        configtxt = ""
        #Reading in report config
        with open("report_config.ini","r") as configFile:
            configtxt = configFile.read()
        self.report_config = dict([item.split(":") for item in configtxt.split("\n") if len(item.split(":")) == 2])
        for key in self.report_config:
            self.report_config[key] = [item.split("=") for item in self.report_config[key].split(",")]
        #Working out account balances
        self.calculate_account_details()

    @property
    def read_payments(self):
        if self.parsed_folder is None:
            self.parsed_folder = pff.ParsedFinanceFolder(self.folder_name)
        return self.parsed_folder.read_payments

    @property
    def timestamp(self):
        if self.parsed_folder is None:
            self.parsed_folder = pff.ParsedFinanceFolder(self.folder_name)
        return self.parsed_folder.timestamp

    @property
    def scheduled_payments(self):
        if self.parsed_folder is None:
            self.parsed_folder = pff.ParsedFinanceFolder(self.folder_name)
        return self.parsed_folder.scheduled_payments

    @property
    def scheduled_timestamp(self):
        if self.parsed_folder is None:
            self.parsed_folder = pff.ParsedFinanceFolder(self.folder_name)
        return self.parsed_folder.scheduled_timestamp


    @property
    def additional_text(self):
        if self.parsed_folder is None:
            self.parsed_folder = pff.ParsedFinanceFolder(self.folder_name)
        return self.parsed_folder.additional_text

    def _dialogueCallable(flist,*args):
        def decorator(function):
            def wrapped(*passedargs):
                if len(passedargs) != len(args) + 1:
                    print("ArgumentError: The incorrect number of arguments were passed.")
                    print(args)
                else:
                    newargs = [passedargs[0]]
                    failure = False
                    for i,arg in enumerate(passedargs[1:]):
                        try:
                            newargs.append(args[i](arg))
                        except:
                            print("ArgumentError: Failed to cast argument {} to the correct type".format(i))
                            failure = True
                    if not failure:
                        function(*newargs)
            flist[function.__name__] = wrapped
            return function
        return decorator

    @_dialogueCallable(dialogue_functions)
    def generate_default_reports(self):
        print("Generating default reports...")
        for key in self.report_config:
            if ["autodo","1"] in self.report_config[key] and ["autodo","0"] not in self.report_config[key]:
                self.generate_report(key)
        print("Done!")

    @_dialogueCallable(dialogue_functions)
    def read_drive_files(self):
        print("Reading files from drive...")
        self.parsed_folder = pff.ParsedFinanceFolder(self.folder_name)
        print("Inserting payment info...")
        if self.all_payments is not None:
            if not self.all_payments.empty:
                self.all_payments = self.all_payments.drop(self.all_payments[self.all_payments.id_time == self.timestamp].index)
                #specifically checking if the incoming payments need to overwrite
                if not self.all_payments.empty:
                    self.all_payments = self.all_payments.append(self.read_payments,ignore_index=True)
                else:
                    self.all_payments = self.read_payments
            else:
                self.all_payments = self.read_payments
        else:
            self.all_payments = self.read_payments
        print("Inserting scheduled payment info...")
        if not self.all_payments.empty:
            self.all_payments = self.all_payments.drop(self.all_payments[self.all_payments.id_time == self.scheduled_timestamp].index)
            #specifically checking if the incoming payments need to overwrite
            if not self.all_payments.empty:
                self.all_payments = self.all_payments.append(self.scheduled_payments,ignore_index=True)
            else:
                self.all_payments = self.scheduled_payments
        else:
            self.all_payments = self.scheduled_payments
        print("Applying post-processing...")
        #Post-processing
        self.all_payments.loc[self.all_payments["from"] == "__default_payment",'from'] = self.config["__default_payment"]
        self.all_payments.loc[self.all_payments["from"] == "__default_from_account",'from'] = self.config["__default_from_account"]
        self.all_payments.loc[self.all_payments["to"] == "__default_to_account",'to'] = self.config["__default_to_account"]
        print("Saving payment data...")
        self.save_payments()
        if self.parsed_folder.send_bool:
            print("Uploading updated payments sheet...")
            self.clear_payments()
        if self.parsed_folder.parsed_schedule_file.send_bool:
            print("Uploading updated schedule sheet...")
            self.parsed_folder.update_schedule_file()
        print("Done!")

    @_dialogueCallable(dialogue_functions)
    def print_names(self):
        print(sorted(self.all_payments["to"].unique()))

    @_dialogueCallable(dialogue_functions,str,str)
    def rename_name(self,oldname,newname):
        self.all_payments.loc[self.all_payments["to"] == oldname,'to'] = newname

    @_dialogueCallable(dialogue_functions)
    def print_froms(self):
        print(sorted(self.all_payments["from"].unique()))

    @_dialogueCallable(dialogue_functions,str,str)
    def rename_from(self,oldname,newname):
        self.all_payments.loc[self.all_payments["from"] == oldname,'from'] = newname

    @_dialogueCallable(dialogue_functions)
    def save_payments(self):
        self.all_payments.to_hdf("databases/{}.h5".format(self.folder_name),"payments",mode='a')

    @_dialogueCallable(dialogue_functions)
    def print_payments(self):
        print(self.all_payments.to_string())

    @_dialogueCallable(dialogue_functions,int,float,str,str,pd.Timestamp,pd.Timestamp,str)
    def insert_payment_row(self,index,amount,fro,to,id_time,date_made,type):
        line = pd.DataFrame({"amount":amount,"from":fro,"to":to,"id_time":id_time,"date_made":date_made,"type":type},index=[index-0.5])[["amount","from","to","id_time","date_made","type"]]
        self.all_payments = self.all_payments.append(line, ignore_index=False).sort_index().reset_index(drop=True)

    @_dialogueCallable(dialogue_functions,int)
    def print_payment_row(self,index):
        print(self.all_payments.loc[[index]])

    @_dialogueCallable(dialogue_functions)
    def print_account_details(self):
        self.calculate_account_details()
        print(self.account_details)

    @_dialogueCallable(dialogue_functions,str)
    def generate_report(self,key):
        if self.parsed_folder is None:
            self.parsed_folder = pff.ParsedFinanceFolder(self.folder_name)
        freq = None
        for item in self.report_config[key]:
            if item[0] == "frequency": freq=item[1]
        assert freq is not None, "No frequency tag!"
        offset = 0
        for item in self.report_config[key]:
            if item[0] == "offset": offset=int(item[1])
        todayperiod = pd.Timestamp.now().to_period(freq)
        todayperiod -= offset
        transfers_in_period = self.all_payments.loc[self.all_payments.date_made.dt.to_period(freq) == todayperiod]
        self.calculate_account_details()
        report = tex.TexReport(key,datetime.datetime.now(),info_dict={"raw_dataframe":transfers_in_period,"account_details":self.account_details})
        for item in self.report_config[key]:
            if item[0] == "section":
                report.sections.append(tex.TexSection(item[1]))
        report.generate_doctext()
        report.produce_pdf("temptex")
        self.parsed_folder.odf_folder.save_pdf("tmp/temptex.pdf","{}.pdf".format(key))
        report.clear_tmp("temptex")

    def open_dialogue(self):
        exit_code = False
        while not exit_code:
            print(">>>",end=' ')
            code = raw_input().strip()
            if code == "exit()":
                exit_code = True
            elif code == "ls()":
                print(self.dialogue_functions.keys())
            else:
                split = re.search(r"^(?:(\w+)\s*=)?\s*(\w+)\(((?:[a-zA-Z0-9_.:\- ]+,)*(?:[a-zA-Z0-9_.:\- ]+)?)\)\s*$",code)
                if split:
                    varname = split.group(1)
                    function = split.group(2)
                    args = []
                    if not (split.group(3) == None or split.group(3).strip() == ""):
                        args = [item.strip() for item in split.group(3).split(",")]
                    if function in self.dialogue_functions:
                        self.dialogue_functions[function](self,*args)
                    else:
                        print("CallError: No function of that name")
                else:
                    print("CallError: Input did not match function call form")

    def clear_payments(self):
        time.sleep(1)
        self.parsed_folder.payment_file.write_from_string(get_clean_slate(self.additional_text))

    def calculate_account_details(self):
        account_details = self.all_payments.copy()
        account_details.query("type != 'purchase'",inplace=True)
        account_details["from"] = account_details["to"]
        second_account_details = self.all_payments.copy()
        second_account_details["amount"] = -second_account_details["amount"]
        account_details = pd.concat([account_details,second_account_details],ignore_index=True)
        account_details.drop(inplace=True,columns=["to","id_time","date_made","type"])
        account_details["amount"] = account_details.groupby(["from"])["amount"].transform("sum")
        account_details = account_details.drop_duplicates(subset=["from"])
        self.account_details = account_details

    @classmethod
    def get_sorted_data(self,data,key,n):
        names = data[key]
        amounts = []
        for name in names: amounts.append(sum(data.loc[data[key] == name].amount))
        dictitems = zip(names,amounts)
        dictitems = sorted(dictitems,key=lambda item: item[1],reverse=True)
        if len(dictitems) > n:
            otheritems = dictitems[n-1:]
            dictitems = dictitems[:n-1]
            othersum = sum([item[1] for item in otheritems])
            dictitems.append(("other",othersum))
        return dictitems
