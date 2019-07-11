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
            other_data = pd.read_hdf("databases/{}.h5".format(foldername))
            if not other_data.empty:
                other_data = other_data.drop(other_data[other_data.id_time == self.timestamp].index)
                if not other_data.empty:
                    self.all_payments = other_data.append(self.read_payments,idgnore_index=True)
                else:
                    self.all_payments = self.read_payments
        else:
            pd.DataFrame().to_hdf("databases/{}.h5".format(foldername),"cash_transfer")
            self.all_payments = self.read_payments
