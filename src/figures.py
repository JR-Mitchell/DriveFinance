# -*- coding: utf-8 -*-
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.ioff()
import matplotlib.dates as mdates
import numpy as np
from datetime import timedelta
import src.inputparser as inputparser
import pandas as pd

class Figure(inputparser.BaseParser):
    figure_funcs = {}
    data_funcs = {}
    """ Object for creation of a figure for use in a LaTeX report

    :param name: the name to save the image to
    :type name: str
    :param frequency: a pandas frequency string representing the
        period that data is requested for
    :type frequency: str
    :param period: the pandas Period object which should be included
    :type period: class: `pd.Period`

    """
    def __init__(self,name,frequency,period):
        """ Constructor method
        """
        super(Figure,self).__init__(1)
        self.name = name
        self.frequency = frequency
        self.period = period

    #Overwriting BaseParser functions
    def _parser_handle_incorrect_argno(self,func_name,exp_len,passed):
        """ Function for handling a runtime call with the wrong number of
        arguments

        :param func_name: name of the function incorrectly called
        :type func_name: str
        :param exp_len: the number of arguments that should have been present
        :type exp_len: int
        :param passed: the arguments which were given
        :type passed: list
        """
        errorcode = ("FigureError: function '{}'"
            + " expected {} arguments, received {}"
            + " ({})")
        errorcode = errorcode.format(func_name,exp_len,len(passed),passed)
        raise Exception(errorcode)

    def _parser_handle_conversion_error(self,func_name,argument,type,error):
        """ Function for handling a runtime call which fails to convert an
        argument

        :param func_name: name of the function incorrectly called
        :type func_name: str
        :param argument: the argument which failed conversion
        :type argument: str
        :param type: the function used to try and convert 'argument' to a
            particular type
        :type type: method
        :param error: the Exception thrown when conversion was attempted
        :type error: class: `Exception`
        """
        errorcode = ("FigureError: function '{}'"
            + " encountered an error trying to convert argument '{}'"
            + " with method {}. Raising error:")
        errorcode = errorcode.format(func_name,argument,type)
        print(errorcode)
        raise error

    def _parser_handle_func_result(self,result):
        """ Handles a successful runtime call

        :param result: the return value of the call
        """
        return result

    #General functions
    def generate_data(self,finance_data,data_name,*args):
        """ Sets self._graph_data to the correct data for this figure

        :param finance_data: the FinanceData object to calculate with
        :type finance_data: class: `src.financedata.FinanceData`
        :param data_name: data_funcs function key to call to get data
        :type data_name: str
        :param \*args: further arguments to pass to data function
        """
        if data_name in self.data_funcs:
            self._graph_data = self.data_funcs[data_name](
                self,
                finance_data,
                *args)
        else:
            errorcode = ("FigureError: tried to generate a figure from unknown"
                + " data identifier: '{}'".format(data_name))
            raise Exception(errorcode)

    def save_graph_png(self,graph_name,*args):
        """ Generates a graph and exports as png

        :param graph_name: graph_funcs function key to call to generate graph
        :type graph_name: str
        :param \*args: further arguments to pass to graph function
        """
        if graph_name in self.figure_funcs:
            fig,ax = plt.subplots()
            fig.set_size_inches(5,5)
            self.figure_funcs[graph_name](self,ax,*args)
            fig.savefig("tmp/{}.png".format(self.name))
        else:
            errorcode = ("FigureError: tried to generate a figure from unknown"
                + " graph identifier: '{}'".format(graph_name))
            raise Exception(errorcode)

    #Data access methods
    #TODO write docstrings
    @inputparser.BaseParser._parseMethod(data_funcs)
    def purchases_raw(self,finance_data):
        return finance_data.subdf_purchases(self.frequency,self.period)

    @inputparser.BaseParser._parseMethod(data_funcs)
    def balances_raw(self,finance_data):
        return finance_data.account_balances

    @inputparser.BaseParser._parseMethod(data_funcs)
    def transfers_raw(self,finance_data):
        return finance_data.subdf_transfers(self.frequency,self.period)

    @inputparser.BaseParser._parseMethod(data_funcs,int)
    def item_breakdown_raw(self,finance_data,no_categories=0):
        return finance_data.subdf_item_breakdown(
            self.frequency,
            self.period,
            no_categories)

    #Graph creation methods
    @inputparser.BaseParser._parseMethod(figure_funcs,str,str)
    def pi_chart(self,ax,group_label,val_label):
        """ Creates a pi chart from self._graph_data given the category column
        label and value column labels

        :param ax: the axes to create the chart on
        :type ax: class: `matplotlib.axes.Axes`
        :param group_label: the column heading for different categories
        :type group_label: str
        :param val_label: the column heading for values
        :type val_label: str
        """
        errorcode = ("FigureError: tried to generate a pi chart"
            + " for data without an '{}' column".format(val_label))
        assert val_label in self._graph_data.columns, errorcode
        errorcode = ("FigureError: tried to generate a pi chart"
            + " for data without an '{}' column".format(group_label))
        assert group_label in self._graph_data.columns, errorcode
        new_data = self._graph_data.sort_values(by=[val_label],ascending=False)
        amounts = new_data[val_label].tolist()
        labels = new_data[group_label].tolist()
        ax.pie(amounts,labels=labels)

    @inputparser.BaseParser._parseMethod(figure_funcs,str)
    def time_bar_chart(self,ax,group_label):
        errorcode = ("FigureError: tried to generate a time bar chart"
            + " with no date_made column")
        assert "date_made" in self._graph_data.columns, errorcode
        new_data = self._graph_data.sort_values(by="date_made")
        grouped_data = new_data.groupby([group_label])
        #calculate all dates in period
        endperiod = self.period + 1
        date_range = pd.period_range(
            self.period,
            self.period + 1)
        date_arr = date_range.to_timestamp().to_pydatetime()
        date_frame = date_range.to_frame(index=False)
        date_frame.rename(columns={0:"date_made"},inplace=True)
        date_frame["before"] = 0
        date_frame["after"] = 0
        for group_key in grouped_data.groups:
            group = grouped_data.get_group(group_key)
            dates = group.loc[:,"date_made"].tolist()
            amounts = group.loc[:,"amount"].tolist()
            for date,amount in zip(dates,amounts):
                date_period = date.to_period("D")
                isdate = date_frame["date_made"] == date_period
                date_frame.loc[isdate,"after"] += amount
            ax.bar(
                date_arr,
                date_frame["after"].tolist(),
                bottom = date_frame["before"].tolist(),
                label = group_key)
            date_frame["before"] = date_frame["after"]
        ax.legend()
        for tick in ax.get_xticklabels():
            ticktext = tick.get_text()
            ticktext = ticktext.split("-")
            if len(ticktext) == 3:
                tick.set_text(ticktext[2]+"/"+ticktext[1]+"/"+ticktext[0])
            tick.set_rotation(45)
