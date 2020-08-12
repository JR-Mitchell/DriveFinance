# -*- coding: utf-8 -*-

import re, datetime
import pandas as pd
import src.regex.patterns as patterns
import filereader
import collections as col

class ParsedPayments(filereader.InputFileReader):
    """ Object for parsing the Payments file

    :param child_file: the DocFile (or ChildDocFile) to read
    :type child_file: class: `src.doc.docfile.DocFile`
    :param replacement_dict: dictionary of command shortcuts
    :type replacement_dict: dict
    """
    def __init__(self,child_file,replacement_dict):
        """Constructor method
        """
        super(ParsedPayments,self).__init__(child_file)
        self.additional_text = ""
        time_lock_object = {
            "last_calc_time":None,
            "last_calc_ts_index":None,
            "datenow":None
        }
        self.timestamp = None
        self.send_bool = False
        control_indices = []
        #go through lines
        for index,line in enumerate(self._lines):
            if self.send_bool: #ignore lines after a [send]
                control_indices.insert(0,index)
                self.additional_text += line
                self.additional_text += "\n"
            elif line[0] == "[": #a control tag
                control_indices.insert(0,index)
                self._parse_control_tag(line,time_lock_object,index)
            elif line[0] == "*": #a shortcut
                if line.strip() in replacement_dict:
                    self._parse_payment_line(
                        replacement_dict[line.strip()],
                        time_lock_object,
                        index)
                else:
                    errorcode = "Shortcut command {} not recognised"
                    errorcode = errorcode.format(line)
                    raise Exception(errorcode)
            else:
                self._parse_payment_line(line,time_lock_object,index)
        #get rid of control tags
        for index in control_indices:
            del self._lines[index]
        #store object variables
        finance_list = zip(*self._lines)
        finance_grid = zip(
            ("amount","from","to","id_time","date_made","type")
            ,finance_list)
        self.read_payments = pd.DataFrame(col.OrderedDict(finance_grid))

    def _regex_timestamp(self,tocheck,start,end):
        """ Convenience function for turning a string formatted as
        "DD/MM/YY hh:mm:ss.uuuuuu" (or only part of this) into list of pairs

        :param tocheck: the string to convert
        :type tocheck: str
        :param start: index to begin on
        :type start: int
        :param end: index to end on

        :raises Exception: Exception if regex match fails

        :return: a list of pairs (key,value) for date/time/whatever
        :rtype: list
        """
        regex_pattern_list = patterns.DATELIST[start:end]
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
        keys = keys[start:end]
        timestamp_pairs = zip(
            keys,
            [int(regex_result.group(i+1)) for i in range(end-start)])
        for i in range(len(timestamp_pairs)):
            timestamp_pairs[i] = list(timestamp_pairs[i])
            if timestamp_pairs[i][0] == "year":
                timestamp_pairs[i][1] += 2000
        return timestamp_pairs

    def _parse_control_tag(self,line,timelock,index):
        """ Function to process a particular control tag during init

        :param line: the line payment/transfer command
        :type line: str
        :param timelock: dict with info about times
        :type timelock: dict
        :param index: index of the line in self._lines
        :type index: int
        """
        if "timestamp of last calculation:" in line:
            if timelock["last_calc_time"] is not None:
                errorcode = "Timestamp defined multiple times in Payments!"
                raise Exception(errorcode)
            #last_calc_time is hh:mm:ss.ffffff
            text = ":".join(line.split(":")[1:]).strip("]").strip()
            timelock["last_calc_time"] = self._regex_timestamp(text,3,7)
        elif "datenow" in line:
            text = line.split(":")[1].strip("]").strip()
            timelock["datenow"] = self._regex_timestamp(text,0,3)
            if self.timestamp is None:
                if timelock["last_calc_time"] is None:
                    errorcode = ("First datenow tag appears"
                        + "before valid timestamp!")
                    raise Exception(errorcode)
                self.timestamp = pd.Timestamp(**dict(
                    timelock["datenow"]
                    + timelock["last_calc_time"]))
        elif line == "[send]":
            self.send_bool = True
            datenowtxt = timelock["datenow"].strftime("%d/%m/%y")
            self.additional_text += "[datenow: {}]\n".format(datenowtxt)
        else:
            errorcode = "Control tag '{}' not recognised in Payments"
            errorcode = errorcode.format(line)
            raise Exception(errorcode)

    def _parse_payment_line(self,line,timelock,index):
        """ Function to process a particular line during init

        :param line: the line payment/transfer command
        :type line: str
        :param timelock: dict with info about times
        :type timelock: dict
        :param index: index of the line in self._lines
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
            self._lines[index] = [
                amount, account,
                spent_on, self.timestamp,
                pd.Timestamp(**dict(timelock["datenow"])), "purchase"]
        else:
            transfer = re.search(patterns.TRANSFER,line.strip())
            if transfer:
                #1: amount 2: from 3: to 4: "taken out"
                amount = float(purchase.group(1).strip("£"))
                if all([transfer.group(i+2) is None for i in range(3)]):
                    errorcode = ("No valid format found for"
                        + " payment command '{}'")
                    errorcode = errorcode.format(line)
                    raise Exception(errorcode)
                from_acc = "__default_from_account"
                to_acc = "__default_to_account"
                if transfer.group(2) is not None:
                    from_acc = transfer.group(2).strip()
                if transfer.group(3) is not None:
                    to_acc = transfer.group(3).strip()
                self._lines[index] = [
                    amount, from_acc,
                    to_acc, self.timestamp,
                    pd.Timestamp(**dict(timelock["datenow"])), "transfer"]
            else:
                errorcode = "No valid format found for payment command '{}'"
                errorcode = errorcode.format(line)
                raise Exception(errorcode)

    def new_text(self,time):
        """ Generates the text for a clean payment sheet to be written to the 
        drive

        :param time: timestamp representing now, used for the timestamp
        :type time: class: `datetime.datetime`

        :returns: the text for a clean payment sheet
        :rtype: str
        """
        last_date = now.strftime("%d/%m/%y")
        if "[datenow: " in self.additional_text:
            remaining_time_text = self.additional_text
        else:
            remaining_time_text = "[datenow: {}]\n".format(last_date)
        timestamp = now.time()
        #TODO this current bit is old and nonfunctional and needs replacing.
        #Perhaps could use similar stuff to LaTeX generation to get stuff.
        format_dict = {
            "dbudget": "£10",
            "dremain": "£5",
            "wremain": "£5",
            "remtext": remaining_time_text,
            "timestamp": timestamp}
        ##
        with open("templates/basic_file.txt","r") as template:
            template_str = template.read()
        return template_str.format(**format_dict)
