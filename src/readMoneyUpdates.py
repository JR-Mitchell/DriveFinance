# -*- coding: utf-8 -*-

import datetime,os
import src.parseFinanceFolder as pff
import pandas as pd

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
    def __init__(self,foldername):
        super(FinanceInfoObject,self).__init__(foldername)
        if os.path.isfile("databases/{}.h5".format(foldername)):
            other_data = pd.read_hdf("databases/{}.h5".format(foldername),"payments")
            if not other_data.empty:
                other_data = other_data.drop(other_data[other_data.id_time == self.timestamp].index)
                if not other_data.empty:
                    self.all_payments = other_data.append(self.read_payments,idgnore_index=True)
                else:
                    self.all_payments = self.read_payments
        else:
            self.all_payments = self.read_payments
        self.all_payments.to_hdf("databases/{}.h5".format(foldername),"payments",mode='a')

    def clear_payments(self):
        self.payment_file.write_from_string(get_new_blank_doc)
