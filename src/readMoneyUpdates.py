# -*- coding: utf-8 -*-

import datetime
import src.parseFinanceFolder as pff

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
