# -*- coding: utf-8 -*-

import pandas as pd
import src.parse as parse
import src.gdrive.drivefolder as odf
import src.reports as reports
import os, json, datetime, time

class FinanceData(object):
    """ Object for general processing of finances through various utility
    methods and properties.

    :param folder_name: the name of the folder holding finance info,
        defaults to None (in which case "__default_folder_name" from config.ini
        is used)
    :type folder_name: str, optional
    """
    def __init__(self,folder_name=None):
        #Read in the config
        with open("config.ini","r") as configfile:
            config_txt = configfile.read()
        self.config = dict([
            item.split(":")
            for item in config_txt.split("\n")
            if len(item.split(":")) == 2])
        #Get folder name
        if folder_name is None:
            if "__default_folder_name" in self.config:
                folder_name = self.config["__default_folder_name"]
            else:
                errorcode = ("Unable to find a default folder name!"
                    + " Have you set up using the --setup argument"
                    + " or modified config.ini?")
                raise Exception(errorcode)
        self.folder_name = folder_name
        self.drive_folder = None
        self.raw_files = {}
        self.parsed_files = {}
        #Read in the database
        db_path = "databases/{}.h5".format(folder_name)
        self.payment_db = None
        if os.path.isfile(db_path):
            self.payment_db = pd.read_hdf(db_path)
        #Read in report config
        self.report_config = {}
        for item in os.listdir("report_json/"):
            name = item[:-5]
            with open("report_json/{}".format(item),"r") as myfile:
                try:
                    self.report_config[name] = json.load(myfile)
                except:
                    print("Error raised parsing report '{}'".format(name))
                    raise

    def read_drive_files(self):
        """ Reads in all up-to-date information from the user's Google Drive
        """
        print("Reading files from drive...")
        self.drive_folder = odf.DriveFolder(self.folder_name)
        for key in ["Shortcuts","Balances"]:
            self.raw_files[key] = self.drive_folder.child_file(key)
            self.parsed_files[key] = parse.autoparse(key,self.raw_files[key])
        for key in ["Payments","Scheduled"]:
            self.raw_files[key] = self.drive_folder.child_file(key)
            self.parsed_files[key] = parse.autoparse(
                key,
                self.raw_files[key],
                self.shortcuts.dict)
        print("Pulling data from 'Payments' into dataframe...")
        if self.payment_db is not None:
            if not self.payment_db.empty:
                self.payment_db.drop(
                    self.payment_db[
                        self.payment_db.id_time == self.payments.timestamp
                        ].index,
                    inplace=True)
                if not self.payment_db.empty:
                    self.payment_db = self.payment_db.append(
                        self.payments.read_payments,
                        ignore_index = True)
                else:
                    self.payment_db = self.payments.read_payments
            else:
                self.payment_db = self.payments.read_payments
        else:
            self.payment_db = self.payments.read_payments
        print("Pulling data from 'Scheduled' into dataframe...")
        if not self.payment_db.empty:
            self.payment_db.drop(
                self.payment_db[
                    self.payment_db.id_time == self.scheduled.datetimestamp
                    ].index,
                inplace=True)
            if not self.payment_db.empty:
                self.payment_db = self.payment_db.append(
                    self.scheduled.read_payments,
                    ignore_index = True)
            else:
                self.payment_db = self.scheduled.read_payments
        else:
            self.payment_db = self.scheduled.read_payments
        print("Inserting default accounts into dataframe...")
        for key,col in [
            ("__default_payment","from"),
            ("__default_from_account","from"),
            ("__default_to_account","to")]:
            key_arr = self.payment_db[col] == key
            self.payment_db.loc[key_arr,col] = self.config[key]
        print("Calculating account balances...")
        self.calculate_account_balances()
        print("Executing commands from 'Balances'...")
        #Init commands
        for item in self.balances.init_args:
            account_name = item[0].strip()
            init_balance = float(item[1].strip())
            print("Setting initial balance of account '{}' to {}".format(
                account_name,
                init_balance))
            init_time = datetime.datetime.now()
            self.set_initial_balance(account_name,expected_balance,init_time)
        #Check commands
        for item in self.balances.check_args:
            account_name = item[0].strip()
            expected_balance = float(item[1].strip())
            self.check_discrepancy(account_name,expected_balance)
        print("Saving payments database...")
        self.save_database()
        if self.payments.send_bool:
            print("Uploading updated payments sheet...")
            self.clear_payments_doc()
        if self.scheduled.send_bool:
            print("Uploading updated schedule sheet...")
            self.update_schedule_doc()
        if len(self.balances.check_args+self.balances.init_args) > 0:
            print("Uploading cleared balance sheet...")
            self.clear_balance_doc()
        print("Done reading drive files!")

    #Calculation functions
    def set_initial_balance(self,account_name,balance,init_time):
        """ Sets the initial balance for a specified account to a particular 
        given amount

        :param account_name: the name of the account
        :type account_name: str
        :param balance: how much, in £, the account's initial balance is
        :type balance: float
        :param init_time: the time of balance initialisation
        :type init_time: class: `datetime.datetime`
        """
        #remove previous initial balances
        query_str = "type != 'balance_init' or to != '{}'"
        query_str = query_str.format(account_name)
        self.payment_db.query(query_str)
        #add new initial balance
        row = {
            "amount": balance,
            "from": "the void",
            "to": account_name,
            "id_time": datetime.datetime.now(),
            "date_made": init_time,
            "type": "balance_init"
        }
        df_row = pd.DataFrame(row,index=[0.5])[[
            "amount","from","to",
            "id_time","date_made","type"]]
        self.payment_db = self.payment_db \
                              .append(df_row, ignore_index=True) \
                              .sort_index() \
                              .reset_index(drop=True)
        self.calculate_account_balances()

    def check_discrepancy(self,account_name,expected_balance):
        """ Allows the user to input the current real-world balance of an
        account and creates a discrepancy item accounting how much it differs 
        from DriveFinance's calculated balance for this account

        :param account_name: the name of the account
        :type account_name: str
        :param expected_balance: how much, in £, the account should have in it
        :type expected_balance: float
        """
        current_balance = float(self.account_balances \
            [self.account_balances["from"]==account_name] \
            .get("amount") \
            .tolist()[0])
        #difference between current and expected
        discrepancy = round(current_balance - expected_balance,2)
        if (discrepancy == 0):
            announce_str = ("Balance check for account '{}'"
                + " came out with no discrepancy!")
            announce_str = announce_str.format(account_name)
            print(announce_str)
        else:
            #find previous discrepancy - either a "from" or a "to"
            previous_discrepancy = 0
            query_str = "type == 'discrepancy' and to == '{}'"
            query_str = query_str.format(account_name)
            discrep_q = self.payment_db.query(query_str)
            if not discrep_q.empty:
                response_str = "type != 'discrepancy' or to != '{}'"
                response_str = response_str.format(account_name)
                previous_discrepancy = -discrep_q.get("amount").tolist()[0]
                self.payment_db.query(response_str,inplace=True)
            query_str = "type == 'discrepancy' and frmo == '{}'"
            query_str = query_str.format(account_name)
            discrep_q = self.payment_db.rename(columns={"from","frmo"}) \
                                       .query(query_str)
            if not discrep_q.empty:
                response_str = "type != 'discrepancy' or frmo != '{}'"
                response_str = response_str.format(account_name)
                previous_discrepancy = discrep_q.get("amount").tolist()[0]
                self.payment_db.rename(columns={"from","frmo"},inplace=True)
                self.payment_db.query(response_str,inplace=True)
                self.payment_db.rename(columns={"frmo","from"},inplace=True)
            #get id time
            id_time = datetime.datetime.now()
            #create new discrepancy
            total_discrepancy = round(discrepancy + previous_discrepancy,2)
            if (total_discrepancy == 0):
                announce_str = ("Total discrepancy of account '{}' now 0."
                    + " Clearing past discrepancies.")
                announce_str = announce_str.format(account_name)
                print(announce_str)
            else:
                announce_str = ("Setting current balance of account '{}'"
                    + " from {} to {} (total discrepancy {})")
                announce_str = announce_str.format(
                    account_name,current_balance,
                    expected_balance,total_discrepancy)
                print(announce_str)
                row = {
                    "id_time": id_time,
                    "date_made": id_time,
                    "type": "discrepancy"}
                if (total_discrepancy < 0):
                    row["amount"] = -total_discrepancy
                    row["from"] = account_name
                    row["to"] = "the void"
                else:
                    row["amount"] = total_discrepancy
                    row["from"] = "the void"
                    row["to"] = account_name
                df_row = pd.DataFrame(row,index=[0.5])[[
                    "amount","from","to",
                    "id_time","date_made","type"]]
                self.payment_db = self.payment_db \
                                      .append(df_row, ignore_index=True) \
                                      .sort_index() \
                                      .reset_index(drop=True)
        self.calculate_account_balances()

    def calculate_account_balances(self):
        """ Updates 'self.account_balances' with the most up to date
        calculations of what the balance in each account should be
        """
        to_transfers = self.payment_db.copy()
        from_transfers = to_transfers.copy()
        to_transfers.query("type != 'purchase'",inplace=True)
        to_transfers["from"] = to_transfers["to"]
        from_transfers.query("type != 'balance_init'",inplace=True)
        from_transfers["amount"] = -from_transfers["amount"]
        account_balances = pd.concat(
            [to_transfers,from_transfers],
            ignore_index=True)
        #Sort out columns
        account_balances.drop(
            inplace=True,
            columns=["to","id_time","date_made","type"])
        account_balances.rename(
            columns={"from":"account","amount":"balance"},
            inplace=True)
        #Group by account and sum together
        account_balances["balance"] = account_balances.groupby(["account"]) \
                                                      ["balance"] \
                                                      .transform("sum")
        self.account_balances = account_balances.drop_duplicates(
            subset=["account"])

    #Saving to database
    def save_database(self):
        """ Updates the .h5 file with the information currently stored in the
        'self.payment_db' database
        """
        db_name = "databases/{}.h5".format(self.folder_name)
        self.payment_db.to_hdf(db_name,"payments",mode='a')

    #Methods for saving to drive
    def clear_payments_doc(self):
        """ Replaces the Payments file in the user's Drive with a clear file
        (leaving all text after a [send] tag if one was present)
        """
        time.sleep(0.1) #Settles my unreasonable worry about timestamp clashes
        currtime = datetime.datetime.now()
        self.raw_files["Payments"].write_from_string(
            self.payments.new_text(currtime))

    def update_schedule_doc(self):
        """ Updates the Schedule file in the user's Drive with an updated file
        """
        self.raw_files["Scheduled"].write_from_string(self.scheduled.new_text)

    def clear_balance_doc(self):
        """ Replaces the Balances file in the user's Drive with a clean sheet
        """
        self.raw_files["Balances"].write_from_string(self.balances.new_text)

    def generate_report(self,report_name):
        """ Generates and uploads the specified report

        :param report_name: the name of the report
        :type report_name: str
        """
        errorcode = "No frequency tag found in report {}".format(report_name)
        assert "frequency" in self.report_config[report_name], errorcode
        freq = self.report_config[report_name]["frequency"]
        offset = 0
        if "offset" in self.report_config[report_name]:
            offset = self.report_config[report_name]["offset"]
        report_period = pd.Timestamp.now().to_period(freq)
        report_period -= offset
        self.calculate_account_balances()
        with open("templates/latex_file.tex","r") as my_file:
            header = my_file.read()
        header = header.decode("utf8")
        report = reports.TexReport(report_name,freq,offset,header=header)
        for item in self.report_config[report_name]["sections"]:
            report.add_section(item)
        report.generate_doctext(self)
        report.produce_pdf("temptex")
        self.drive_folder.save_pdf("tmp/temptex.pdf",report_name+".pdf")
        report.clear_tmp("temptex")

    def generate_default_reports(self):
        print("Generating default reports...")
        for key in self.report_config:
            if ("autodo" in self.report_config[key]
                and self.report_config[key]["autodo"] == 1):
                print("Generating report {}".format(key))
                self.generate_report(key)
        print("Done generating default reports!")

    #Convenience property stuff
    def _parsed_property(self,key):
        """ Convenience function for properties giving parsed files

        :param key: name of parsed file to access
        :type key: str

        :returns: parsed file
        :rtype: object: `src.parse.shortcuts.ParsedShortcuts` or
            object: `src.parse.balances.ParsedBalances` or
            object: `src.parse.payments.ParsedPayments` or
            object: `src.parse.scheduled.ParsedSchedule`
        """
        if key in self.parsed_files:
            return self.parsed_files[key]
        else:
            errorcode = ("Key '{}' not found in parsed files!"
                + " Are you sure this is a valid key,"
                + " and that payments have been read in?")
            raise Exception(errorcode)

    @property
    def shortcuts(self):
        return self._parsed_property("Shortcuts")

    @property
    def balances(self):
        return self._parsed_property("Balances")

    @property
    def payments(self):
        return self._parsed_property("Payments")

    @property
    def scheduled(self):
        return self._parsed_property("Scheduled")

    #Raw data functions
    def subdf(self,frequency,period):
        """ Returns a DataFrame including only rows in a given
        time period of given frequency

        :param frequency: a pandas frequency string representing the
            period that data is requested for
        :type frequency: str
        :param period: the pandas Period object which should be included
        :type period: class: `pd.Period`

        :returns: dataframe of all elements in the given period
        :rtype: class: `pd.DataFrame`
        """
        period_keys = self.payment_db.date_made.dt.to_period(frequency)
        return self.payment_db.loc[period_keys == period]

    def subdf_purchases(self,frequency,period):
        """ Returns a DataFrame including only purchases in a given
        time period of given frequency

        :param frequency: a pandas frequency string representing the
            period that data is requested for
        :type frequency: str
        :param period: the pandas Period object which should be included
        :type period: class: `pd.Period`

        :returns: outgoing payments in given period
        :rtype: class: `pd.DataFrame`
        """
        in_period_df = self.subdf(frequency,period)
        purchase_keys = in_period_df["type"].isin([
            "purchase",
            "scheduled_purchase"])
        return in_period_df.loc[
            purchase_keys,
            ["amount","from","to","date_made"]]

    def subdf_transfers(self,frequency,period):
        """ Returns a DataFrame including only transfers in a given
        time period of given frequency

        :param frequency: a pandas frequency string representing the
            period that data is requested for
        :type frequency: str
        :param period: the pandas Period object which should be included
        :type period: class: `pd.Period`

        :returns: outgoing payments in given period
        :rtype: class: `pd.DataFrame`
        """
        in_period_df = self.subdf(frequency,period)
        purchase_keys = in_period_df["type"].isin([
            "transfer",
            "scheduled_transfer"])
        return in_period_df.loc[
            purchase_keys,
            ["amount","from","to","date_made"]]

    def subdf_item_breakdown(self,frequency,period,no_categories):
        """ Returns a DataFrame of outgoing purchases in the given period
        broken down by category spent on

        :param frequency: a pandas frequency string representing the
            period that data is requested for
        :type frequency: str
        :param period: the pandas Period object which should be included
        :type period: class: `pd.Period`
        :param no_categories: the maximum number of categories
            (including 'Other') to show.
            A value of '0' or any negative number sets no maximum.
        :type no_categories: int

        :returns: item breakdown for given period, with 'Other' category if the
            number of items spent on exceeds no_categories
        :rtype: class: `pd.DataFrame`
        """
        payment_df = self.subdf_purchases(frequency,period)
        payment_df["amount"] = payment_df.groupby(["to"])["amount"] \
                                         .transform("sum")
        payment_df = payment_df.drop_duplicates(subset=["to"]) \
                               .sort_values(by=["amount"],ascending=False) \
                               .loc[:,["amount","to"]]
        if no_categories > 0 and no_categories < len(payment_df.index):
            included = payment_df.iloc[range(no_categories)]
            other = payment_df.iloc[range(no_categories,len(payment_df.index))]
            other = other.agg("sum")
            other["to"] = "other"
            included.append(other,ignore_index=True)
            return included
        return payment_df
