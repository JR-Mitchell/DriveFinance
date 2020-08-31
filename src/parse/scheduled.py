# -*- coding: utf-8 -*-

import re, datetime
import collections as col
import pandas as pd
import src.regex.patterns as patterns

class ParsedSchedule(object):
    """ Object for parsing the Scheduled file

    :param child_file: the DocFile (or ChildDocFile) to read
    :type child_file: class: `src.gdrive.docfile.DocFile`
    :param replacement_dict: dictionary of command shortcuts
    :type replacement_dict: dict
    """
    def __init__(self,child_file,replacement_dict):
        """Constructor method
        """
        today = pd.Timestamp(datetime.datetime.now().date())
        text = child_file.initial_content.lower()
        lines = text.strip("\xef\xbb\xbf").split("\r\n")
        self._lines_to_process = []
        indices_to_remove = []
        self.send_bool = False
        #get datetimestamp
        datetimestamp_line = lines.pop(0)
        self.datetimestamp = self._regex_timestamp(datetimestamp_line,7)
        #go through lines
        for index,line in enumerate(lines):
            validpart = line.split("#")[0].strip()
            if validpart != "":
                linesplit = validpart.split(":")
                #check if the date has passed
                enddate = linesplit[4].strip()
                linedate = self._regex_timestamp(linesplit[0].strip(),3)
                if today > linedate:
                    self.send_bool = True
                    #update the date
                    kwds = {linesplit[2].strip():int(linesplit[3].strip())}
                    dateoffset = pd.tseries.offsets.DateOffset(**kwds)
                    newdate = linedate + dateoffset
                    enddate_not_never = (enddate != "never")
                    if enddate_not_never:
                        enddate_ts = self._regex_timestamp(enddate,3)
                    if enddate_not_never and newdate > enddate_ts:
                        #end of payment period, remove the line
                        indices_to_remove.insert(0,index)
                    else:
                        #update the line
                        linesplit[0] = newdate.strftime("%d/%m/%y")
                        lines[index] = ":".join(linesplit)
                        if len(line.split("#")) > 1:
                            lines[index] += "#"
                            lines[index] += "#".join(
                                line.split("#")[1:])
                    #add to _lines_to_process
                    linecommand = linesplit[1].strip()
                    if linecommand[0] == "*": #a shortcut
                        if linecommand in replacement_dict:
                            self._lines_to_process.append([
                                replacement_dict[linecommand],
                                linedate])
                        else:
                            errorcode = "Shortcut command {} not recognised"
                            errorcode = errorcode.format(linecommand)
                            raise Exception(errorcode)
                    else:
                        self._lines_to_process.append([linecommand,linedate])
        for index in indices_to_remove:
            del lines[index]
        for index,line in enumerate(self._lines_to_process):
            self._parse_payment_line(line[0],line[1],index)
        #store object variables
        finance_list = zip(*self._lines_to_process)
        finance_grid = zip(
            ("amount","from","to","id_time","date_made","type")
            ,finance_list)
        self.read_payments = pd.DataFrame(col.OrderedDict(finance_grid))
        if self.send_bool:
            newstamp = pd.Timestamp.now()
        else:
            newstamp = self.datetimestamp
        self.new_text = newstamp.strftime("%d/%m/%y %H:%M:%S.%f")
        for line in lines:
            self.new_text += "\n" + line

    def _regex_timestamp(self,tocheck,noitems):
        """ Convenience function for turning a string formatted as
        "DD/MM/YY hh:mm:ss.uuuuuu" (or only part of this) into timestamp

        :param tocheck: the string to convert
        :type tocheck: str
        :param noitems: the number of items in the timestamp
        :type noitems: int

        :raises Exception: Exception if regex match fails

        :returns: a timestamp representing the input string
        :rtype: class:`pd.Timestamp`
        """
        regex_pattern_list = patterns.DATELIST[:noitems]
        regex_pattern = r"^"
        for item in regex_pattern_list:
            regex_pattern += item
        regex_pattern += r"$"
        regex_result = re.search(
            regex_pattern,
            tocheck)
        if not regex_result:
            errorcode = "Scheduler date '{}' does not match format"
            errorcode = errorcode.format(tocheck)
            raise Exception(errorcode)
        keys = ["day","month","year","hour","minute","second","microsecond"]
        keys = keys[:noitems]
        timestamp_dict = dict(zip(
            keys,
            [int(regex_result.group(i+1)) for i in range(noitems)]))
        timestamp_dict["year"] += 2000
        return pd.Timestamp(**timestamp_dict)

    def _parse_payment_line(self,line,datenow,index):
        """ Function to process a particular line during init

        :param line: the line payment/transfer command
        :type line: str
        :param datenow: the date associated with the command
        :type datenow: class:`pd.Timestamp`
        :param index: index of the line in self._lines_to_process
        :type index: int
        """
        purchase = re.search(patterns.PURCHASE,line.strip())
        if purchase:
            #1: amount 2: spent on 3: paid by
            amount = float(purchase.group(1).strip("£"))
            spent_on = purchase.group(2).strip()
            account = "__default_payment"
            if purchase.group(3) is not None:
                account = purchase.group(3).strip()
            self._lines_to_process[index] = [
                amount, account, spent_on,
                self.datetimestamp, datenow, "scheduled_purchase"]
        else:
            transfer = re.search(patterns.TRANSFER,line.strip())
            if transfer:
                #1: amount 2: from 3: to 4: "taken out"
                amount = float(purchase.group(1).strip("£"))
                if all([transfer.group(i+2) is None for i in range(3)]):
                    errorcode = ("No valid format found for"
                        + " scheduler command '{}'")
                    errorcode = errorcode.format(line)
                    raise Exception(errorcode)
                from_acc = "__default_from_account"
                to_acc = "__default_to_account"
                if transfer.group(2) is not None:
                    from_acc = transfer.group(2).strip()
                if transfer.group(3) is not None:
                    to_acc = transfer.group(3).strip()
                self._lines_to_process[index] = [
                    amount, from_acc, to_acc,
                    self.datetimestamp, datenow, "scheduled_transfer"]
            else:
                errorcode = "No valid format found for scheduler command '{}'"
                errorcode = errorcode.format(line)
                raise Exception(errorcode)
