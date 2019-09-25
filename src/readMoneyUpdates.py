# -*- coding: utf-8 -*-

from __future__ import print_function
import datetime,os
import src.parseFinanceFolder as pff
import src.createTexReports as tex
import pandas as pd
import re

def get_clean_slate():
    """
    Creates a clean payment sheet to be fed back to the drive.
    """
    now = datetime.datetime.now()
    lastdate = now.strftime("%d/%m/%y")
    timestamp=now.time()
    fdict = {"dbudget":"£10","dremain":"£5","wremain":"£5","lastdate":lastdate,"timestamp":timestamp}
    with open("templates/basic_file.txt","r") as myFile:
        template_str = myFile.read()
    return template_str.format(**fdict)

class FinanceInfoObject(pff.ParsedFinanceFolder):
    dialogue_functions = {}
    def __init__(self,foldername):
        super(FinanceInfoObject,self).__init__(foldername)
        if os.path.isfile("databases/{}.h5".format(foldername)):
            other_data = pd.read_hdf("databases/{}.h5".format(foldername),"payments")
            if not other_data.empty:
                other_data = other_data.drop(other_data[other_data.id_time == self.timestamp].index)
                if not other_data.empty:
                    self.all_payments = other_data.append(self.read_payments,ignore_index=True)
                else:
                    self.all_payments = self.read_payments
        else:
            self.all_payments = self.read_payments
        self.config = {}
        configtxt = ""
        with open("config.ini","r") as configFile:
            configtxt = configFile.read()
        self.config = dict([item.split(":") for item in configtxt.split("\n") if len(item.split(":")) == 2])
        self.report_config = {}
        configtxt = ""
        with open("report_config.ini","r") as configFile:
            configtxt = configFile.read()
        self.report_config = dict([item.split(":") for item in configtxt.split("\n") if len(item.split(":")) == 2])
        for key in self.report_config:
            self.report_config[key] = [item.split("=") for item in self.report_config[key].split(",")]
        self.all_payments.loc[self.all_payments["from"] == "__default_payment",'from'] = self.config["__default_payment"]
        self.all_payments.loc[self.all_payments["from"] == "__default_from_account",'from'] = self.config["__default_from_account"]
        self.all_payments.loc[self.all_payments["to"] == "__default_to_account",'to'] = self.config["__default_to_account"]
        self.save_payments()
        for key in self.report_config:
            if ["autodo","1"] in self.report_config[key] and ["autodo","0"] not in self.report_config[key]:
                self.generate_report(key)

    def _dialogueCallable(flist,*args):
        def decorator(function):
            def wrapped(*passedargs):
                if len(passedargs) != len(args) + 1:
                    print("ArgumentError: The incorrect number of arguments were passed")
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
    def save_payments(self):
        self.all_payments.to_hdf("databases/{}.h5".format(self.folder_name),"payments",mode='a')

    @_dialogueCallable(dialogue_functions)
    def print_payments(self):
        print(self.all_payments.to_string())

    @_dialogueCallable(dialogue_functions,int,float,str,str,pd.Timestamp,pd.Timestamp,str)
    def insert_payment_row(self,index,amount,fro,to,id_time,date_made,type):
        line = pd.DataFrame({"amount":amount,"from":fro,"to":to,"id_time":id_time,"date_made":date_made,"type":type},index=[index-0.5])[["amount","from","to","id_time","date_made","type"]]
        self.all_payments = self.all_payments.append(line, ignore_index=False).sort_index().reset_index(drop=True)

    @_dialogueCallable(dialogue_functions,str)
    def generate_report(self,key):
        freq = None
        for item in self.report_config[key]:
            if item[0] == "frequency": freq=item[1]
        assert freq is not None, "No frequency tag!"
        todayperiod = pd.Timestamp.now().to_period(freq)
        transfers_in_period = self.all_payments.loc[self.all_payments.date_made.dt.to_period(freq) == todayperiod]
        account_details = self.all_payments.copy()
        account_details.query("type != 'purchase'",inplace=True)
        account_details["from"] = account_details["to"]
        second_account_details = self.all_payments.copy()
        second_account_details["amount"] = -second_account_details["amount"]
        account_details = pd.concat([account_details,second_account_details],ignore_index=True)
        account_details.drop(inplace=True,columns=["to","id_time","date_made","type"])
        account_details["amount"] = account_details.groupby(["from"])["amount"].transform("sum")
        account_details = account_details.drop_duplicates(subset=["from"])
        report = tex.TexReport(key,datetime.datetime.now(),info_dict={"raw_dataframe":transfers_in_period,"account_details":account_details})
        for item in self.report_config[key]:
            if item[0] == "section":
                report.sections.append(tex.TexSection(item[1]))
        report.generate_doctext()
        report.produce_pdf("temptex")
        self.odf_folder.save_pdf("tmp/temptex.pdf","{}.pdf".format(key))
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
        self.payment_file.write_from_string(get_clean_slate())

    def get_purchases_time_period(self,):
        pass

    def get_budget_time_period(self,):
        pass

    def get_transfers_time_period(self,):
        pass

    def get_balances(self):
        """
        Returns the numerical balance for each account
        """
        pass #TODO

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

