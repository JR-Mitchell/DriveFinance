import src.interface as interface
import pandas as pd
import subprocess as sub
import figures as fig
import os

class TexReport(interface.BaseParser):
    report_funcs = {}
    """ Object for creation of a LaTeX report

    :param title: the name of the report
    :type title: str
    :param frequency: a pandas frequency string representing the span of the
        period that the report covers
    :type frequency: str
    :param offset: how many periods before the current period
        this report covers
    :type offset: int
    :param spacer: text representing the LaTeX spacing used between sections,
        defaults to '5mm'
    :type spacer: str, optional
    :param header: text representing the LaTex header used in the report,
        defaults to (too long to show here, but sets up article with booktabs,
        graphicx and longtable imported)
    :type header: str, optional
    """
    def __init__(
        self,title,frequency,
        offset,spacer='5mm',
        header="""\\documentclass[12pt]{article}
   \\usepackage{booktabs}
   \\usepackage{graphicx}
   \\usepackage{longtable}"""):
        """ Constructor method
        """
        super(TexReport,self).__init__(1)
        self.title = title
        self.spacer = spacer
        self.header = header
        self.sections = []
        self.time_period = pd.Timestamp.now().to_period(frequency)
        self.time_period -= offset
        self.doctext = None
        self.frequency = frequency
        self.report_calls = []
        self.figure_names = []

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
        errorcode = ("ReportError: function '{}'"
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
        errorcode = ("ReportError: function '{}'"
            + " encountered an error trying to convert argument '{}'"
            + " with method {}. Raising error:")
        errorcode = errorcode.format(func_name,argument,type)
        print(errorcode)
        raise error

    def _parser_handle_func_result(self,result):
        """ Handles a successful runtime call, converting it into a curly
        bracketed string of args such that it can be applied to a LaTeX method

        :param result: the return value of the call
        :type result: str or unicode or list
        """
        if isinstance(result,list):
            return "{" + "}{".join(result) + "}"
        else:
            return "{" + result + "}"

    #General functions
    def add_section(self,data):
        """ Adds a section to the report based on json data for the section

        :param data: the json data for the section, formatted
            [section_name,
            section param 1,
            section param 2,
            ...]
            the params may be calls to report functions, in which case they are
            given as a list with function name followed by params in
            similar style
        :type data: list
        """
        latex_func = data[0]
        for item in data[1:]:
            #Params
            latex_func += "{"
            if isinstance(item,list):
                #function call
                func_name = item[0]
                func_params = item[1:]
                func_params = [
                    param[0]
                    + "("
                    + ",".join([str(subparam) for subparam in param[1:]])
                    + ")"
                    if isinstance(param,list)
                    else str(param)
                    for param in func_params]
                self.report_calls.append([func_name,func_params])
                latex_func += func_name + "(" + ",".join(func_params) + ")}"
            else:
                #raw arg; ensure curly brackets escaped
                latex_func += "{" + str(arg) + "}}"
        self.sections.append(latex_func)

    def generate_doctext(self,finance_data):
        """ Goes through all sections and runs all relevant function calls to
            fill in the blanks on the LaTeX file

            :param finance_data: the FinanceData object to calculate with
            :type finance_data: class: `src.financedata.FinanceData`
        """
        format_dict = {}
        #populate the format_dict via function calls
        for function,args in self.report_calls:
            key = function + "(" + ",".join(args) + ")"
            errorcode = ("ReportError: No function named '{}'"
                + " found for line '{}'")
            errorcode = errorcode.format(function,key)
            assert function in self.report_funcs, errorcode
            format_dict[key] = self.report_funcs[function](
                self,
                finance_data,
                *args)
        #construct the document text
        self.doctext = (self.header
            + "\n\n\\title{"
            + self.title
            + "}\n\n\\begin{document}\n\\maketitle\n")
        #adding each section
        for section in self.sections:
            self.doctext += "\\"
            self.doctext += section.format(**format_dict)
        self.doctext += "\\end{document}"
        #replacements - table envs and vspace text
        self.doctext = self.doctext.replace(
            "begin{tabular}",
            "begin{longtable}")
        self.doctext = self.doctext.replace("end{tabular}","end{longtable}")
        self.doctext = self.doctext.replace(
            "[vspacetxt]",
            "\n\\vspace{"+self.spacer+"}")

    def produce_pdf(self,input_name):
        """ Makes subprocess calls to generate a pdf report

        :param input_name: the name of the tex file to render
        :type input_name: str
        """
        if self.doctext is None:
            self.generate_doctext()
        if ".tex" in input_name and input_name[-4:] == ".tex":
            file_name = input_name
        else:
            file_name = input_name + ".tex"
        with open("tmp/"+file_name,"w") as texfile:
            texfile.write(self.doctext.encode("utf-8"))
        tex_process = sub.Popen(
            "pdflatex {}".format(file_name),
            cwd = os.path.join(os.getcwd(),"tmp"),
            shell = True)
        tex_process.wait()

    def clear_tmp(self,input_name):
        """ Cleans up all generated files from tmp file

        :param input_name: the name of the tex file to clear
        :type input_name: str
        """
        if ".tex" in input_name and input_name[-4:] == ".tex":
            general_name = input_name[:-4]
        else:
            general_name = input_name
        cleanup_process = sub.Popen(
            "rm tmp/{}.*".format(general_name),
            shell = True)
        cleanup_process.wait()
        self.doctext = None
        for figure in self.figure_names:
            cleanup_process = sub.Popen(
                "rm tmp/{}.png".format(figure),
                shell=True)
            cleanup_process.wait()

    #Functions that may be included in a report json
    @interface.BaseParser._parseMethod(report_funcs)
    def all_purchases(self,finance_data):
        """ Convenience function for default \allPurchases LaTeX section

        :param finance_data: the FinanceData object to calculate with
        :type finance_data: class: `src.financedata.FinanceData`

        :returns: [
            total amount spent on purchases in period,
            number of purchases in period,
            table of purchases in period,
            name of bar graph for purchases in period]
        :rtype: list
        """
        purchases_raw = finance_data.subdf_purchases(
            self.frequency,
            self.time_period)
        latex_table = purchases_raw.to_latex(
                header = ["Amount","From","To","Date"],
                index = False)
        return [
            str(list(purchases_raw.agg('sum'))[0]),
            str(len(purchases_raw.index)),
            self._table_cleanup(latex_table),
            self.generate_figure(
                finance_data,
                "purchases_raw()",
                "time_bar_chart(to)")]

    @interface.BaseParser._parseMethod(report_funcs)
    def purchases_total(self,finance_data):
        """ Returns the total amount spent on purchases in the time period

        :param finance_data: the FinanceData object to calculate with
        :type finance_data: class: `src.financedata.FinanceData`

        :returns: total amount spent on purchases
        :rtype: str
        """
        purchases_raw = finance_data.subdf_purchases(
            self.frequency,
            self.time_period)
        return str(list(purchases_raw.agg('sum'))[0])

    @interface.BaseParser._parseMethod(report_funcs)
    def purchases_table(self,finance_data):
        """ Returns a table of all purchases in this period

        :param finance_data: the FinanceData object to calculate with
        :type finance_data: class: `src.financedata.FinanceData`

        :returns: LaTeX code for purchases table
        :rtype: unicode
        """
        purchases_raw = finance_data.subdf_purchases(
            self.frequency,
            self.time_period)
        latex_table = purchases_raw.to_latex(
                header = ["Amount","From","To","Date"],
                index = False)
        return self._table_cleanup(latex_table)

    @interface.BaseParser._parseMethod(report_funcs)
    def purchases_count(self,finance_data):
        """ Returns the total number of purchases made in the time period

        :param finance_data: the FinanceData object to calculate with
        :type finance_data: class: `src.financedata.FinanceData`

        :returns: number of purchases in the period
        :rtype: str
        """
        purchases_raw = finance_data.subdf_purchases(
            self.frequency,
            self.time_period)
        return str(len(purchases_raw.index))

    @interface.BaseParser._parseMethod(report_funcs)
    def current_balances(self,finance_data):
        """ Returns a table of up-to-date account balances

        :param finance_data: the FinanceData object to calculate with
        :type finance_data: class: `src.financedata.FinanceData`

        :returns: LaTeX code for balances table
        :rtype: unicode
        """
        latex_table = finance_data.account_balances.to_latex(
            header=["Balance","Account"],
            index=False)
        return self._table_cleanup(latex_table)

    @interface.BaseParser._parseMethod(report_funcs)
    def transfers_table(self,finance_data):
        """ Returns a table of all transfers in this period

        :param finance_data: the FinanceData object to calculate with
        :type finance_data: class: `src.financedata.FinanceData`

        :returns: LaTeX code for transfer table
        :rtype: unicode
        """
        transfers_raw = finance_data.subdf_transfers(
            self.frequency,
            self.time_period)
        latex_table = transfers_raw.to_latex(
                header = ["Amount","From","To","Date"],
                index = False)
        return self._table_cleanup(latex_table)

    @interface.BaseParser._parseMethod(report_funcs,str,str)
    def generate_figure(self,finance_data,data_name,graph_name):
        """ Creates a figure of specific data and graph type,
            returning LaTeX code to include this figure

        :param finance_data: the FinanceData object to calculate with
        :type finance_data: class: `src.financedata.FinanceData`
        :param data_name: figures function to be used for getting data
        :type data_name: str
        :param graph_name: figures graph type identifier
        :param data_name: str

        :returns: LaTeX code to include this figure
        :rtype: str
        """
        data_name = data_name.split("(")
        data_name,data_args = data_name[0],data_name[1]
        data_args = data_args.strip(")").split(",")
        if len(data_args) == 1 and data_args[0] == "":
            data_args = []
        graph_name = graph_name.split("(")
        graph_name,graph_args = graph_name[0],graph_name[1]
        graph_args = graph_args.strip(")").split(",")
        if len(graph_args) == 1 and graph_args[0] == "":
            graph_args = []
        name = (data_name + "_"
            + "_".join(data_args) + "_"
            + graph_name + "_"
            + "_".join(graph_args))
        if name not in self.figure_names:
            self.figure_names.append(name)
            graph = fig.Figure(name,self.frequency,self.time_period)
            graph.generate_data(finance_data,data_name,*data_args)
            graph.save_graph_png(graph_name,*graph_args)
        return "\\includegraphics{}".format("{"+name+".png}")

    @interface.BaseParser._parseMethod(report_funcs,int)
    def item_breakdown_table(self,finance_data,no_categories):
        """ Returns a table of payments in this period
        broken down by category spent on

        :param finance_data: the FinanceData object to calculate with
        :type finance_data: class: `src.financedata.FinanceData`
        :param no_categories: the maximum number of categories
            (including 'Other') to show
        :type no_categories: int

        :returns: LaTeX code for transfer table
        :rtype: unicode
        """
        breakdown_raw = finance_data.subdf_item_breakdown(
            self.frequency,
            self.time_period,
            no_categories)
        latex_table = breakdown_raw.to_latex(
                header = ["Amount","To"],
                index = False)
        return self._table_cleanup(latex_table)

    #Misc convenience functions
    @staticmethod
    def _table_cleanup(latex_table):
        """ Convenience function to remove annoying dates from tables

        :param latex_table: the table to cleanup
        :type latex_table: unicode

        :returns: LaTeX code for cleaned up table
        :rtype: unicode
        """
        latex_table = latex_table.replace(" 12:00:00","")
        latex_table = latex_table.replace(" 00:00:00","")
        return latex_table
