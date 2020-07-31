import subprocess,os
import src.generateReportFigures as fig
import pandas as pd
import re, datetime

class TexReport():
    report_functions = {}
    data_functions = {}
    def __init__(self,key,frequency,offset,spacer='5mm',header="\\documentclass[12pt]{article}\n\\usepackage{booktabs}\n\\usepackage{graphicx}\n\\usepackage{longtable}"):
        """
        Creates and allows generation of a latex report
        """
        #do initial setup
        self.title = key
        self.spacer = spacer
        self.header = header
        self.sections = []
        self.time_period = pd.Timestamp.now().to_period(frequency)
        self.time_period -= offset
        self.doctext = None
        self.frequency = frequency
        self.report_calls = []
        self.figure_names = []

    def _reportCallable(flist,*args):
        def decorator(function):
            def wrapped(*passedargs):
                errorstr = "ReportError: function {} expected {} arguments, recieved {}.".format(function.__name__,len(args),len(passedargs)-2)
                assert len(passedargs) == len(args) + 2, errorstr
                newargs = [passedargs[0],passedargs[1]]
                for i,arg in enumerate(passedargs[2:]):
                    try:
                        newargs.append(args[i](arg))
                    except:
                        print("ReportError thrown when trying to convert argument '{}'".format(arg))
                        raise
                retval = function(*newargs)
                if isinstance(retval,str) or isinstance(retval,unicode):
                    return "{"+retval+"}"
                else:
                    try:
                        return "{" + "}{".join(retval) + "}"
                    except:
                        print("ReportError thrown when trying to understand function result as a string")
                        print("Attempting to print function result type before raising error:")
                        print type(retval)
                        print("Attempting to print function result before raising error:")
                        print retval
                        raise
            flist[function.__name__] = wrapped
            return function
        return decorator

    def _graphCallable(flist,*args):
        def decorator(function):
            def wrapped(*passedargs):
                errorstr = "ReportError: function {} expected {} arguments, recieved {}.".format(function.__name__,len(args),len(passedargs)-2)
                assert len(passedargs) == len(args) + 2, errorstr
                newargs = [passedargs[0],passedargs[1]]
                for i,arg in enumerate(passedargs[2:]):
                    try:
                        newargs.append(args[i](arg))
                    except:
                        print("ReportError thrown when trying to convert argument '{}'".format(arg))
                        raise
                return function(*newargs)
            flist[function.__name__] = wrapped
            return function
        return decorator

    def add_section(self,data):
        linear_function=data[0]
        for item in data[1:]:
            linear_function += "{"
            function_call = item[0]
            function_args = item[1:]
            function_args = [
                str(subitem) if (isinstance(subitem,str) or isinstance(subitem,unicode) or isinstance(subitem,float) or isinstance(subitem,int))
                else subitem[0] + "(" + ",".join(
                        [str(subsubitem) for subsubitem in subitem[1:]]
                    )
                    +")"
                for subitem in function_args]
            self.report_calls.append([function_call,function_args])
            linear_function += function_call
            linear_function += "("
            linear_function += ",".join(function_args)
            linear_function += ")}"
        self.sections.append(linear_function)

    def generate_doctext(self,financeInfo):
        #compile info dict
        info_dict = {}
        #making calls to report functions
        for function,args in self.report_calls:
            key = function + "(" + ",".join(args) + ")"
            errorstr = "ReportError: No function named {}".format(function)
            assert function in self.report_functions, errorstr
            try:
                info_dict[key] = self.report_functions[function](self,financeInfo,*args)
            except:
                print("ReportError: handled for function {}".format(function))
                raise
        self.doctext = self.header+"\n\n\\title{"+self.title+"}\n\n\\begin{document}\n\\maketitle\n"
        self.doctext += "Generated at: {}\n".format(datetime.datetime.now())
        for section in self.sections:
            self.doctext += "\\"
            self.doctext += section.format(**info_dict).replace("begin{tabular}","begin{longtable}").replace("end{tabular}","end{longtable}")
        self.doctext += "\\end{document}"
        self.doctext = self.doctext.replace("[vspacetxt]","\n\\vspace{"+self.spacer+"}")

    def produce_pdf(self,output_name):
        if self.doctext is None:
            self.generate_doctext()
        with open("tmp/{}.tex".format(output_name),"w") as outFile:
            outFile.write(self.doctext.encode("utf-8"))
        tex_process = subprocess.Popen("pdflatex {}.tex".format(output_name),cwd=os.path.join(os.getcwd(),"tmp"),shell=True)
        tex_process.wait()

    def clear_tmp(self,name):
        cleanup_process = subprocess.Popen("rm tmp/{}.*".format(name),shell=True)
        cleanup_process.wait()
        self.doctext = None
        for figure in self.figure_names:
            cleanup_process = subprocess.Popen("rm tmp/{}.png".format(figure),shell=True)
            cleanup_process.wait()

    @_graphCallable(data_functions)
    def purchases_raw(self,financeInfo):
        purchases_raw = financeInfo.all_payments.loc[financeInfo.all_payments.date_made.dt.to_period(self.frequency) == self.time_period]
        return purchases_raw.loc[purchases_raw["type"].isin(["purchase","scheduled_purchase"]),["amount","from","to","date_made"]]

    @_reportCallable(report_functions)
    def all_purchases(self,financeInfo):
        purchases_raw = self.purchases_raw(financeInfo)
        return [
            str(list(purchases_raw.agg('sum'))[0]),
            str(len(purchases_raw.index)),
            purchases_raw.to_latex(header=["Amount","From","To","Date"],index=False).replace(" 12:00:00","").replace(" 00:00:00",""),
            self.generate_graphic(financeInfo,"purchases_raw()","line_graph")
        ]

    @_reportCallable(report_functions)
    def purchases_total(self,financeInfo):
        return str(list(self.purchases_raw(financeInfo).agg('sum'))[0])

    @_reportCallable(report_functions)
    def purchases_table(self,financeInfo):
        return self.purchases_raw(financeInfo).to_latex(header=["Amount","From","To","Date"],index=False).replace(" 12:00:00","").replace(" 00:00:00","")

    @_reportCallable(report_functions)
    def purchases_count(self,financeInfo):
        return str(len(self.purchases_raw(financeInfo).index))

    @_reportCallable(report_functions)
    def current_balances(self,financeInfo):
        return financeInfo.account_details.to_latex(index=False).replace(" 12:00:00","").replace(" 00:00:00","")

    def transfers_raw(self,financeInfo):
        transfers_raw = financeInfo.all_payments.loc[financeInfo.all_payments.date_made.dt.to_period(self.frequency) == self.time_period]
        return transfers_raw.loc[transfers_raw["type"].isin(["transfer","scheduled_transfer"]),["amount","from","to","date_made"]]

    @_reportCallable(report_functions)
    def transfers_table(self,financeInfo):
        return self.transfers_raw(financeInfo).to_latex(header=["Amount","From","To","Date"],index=False).replace(" 12:00:00","").replace(" 00:00:00","")

    @_reportCallable(report_functions,str,str)
    def generate_graphic(self,financeInfo,dataName,graphName):
        dataName = dataName.split("(")
        dataName,args = dataName[0],dataName[1]
        args = args.strip(")").split(",")
        if len(args) == 1 and args[0] == "":
            args = []
        name = dataName+"_"+"_".join(args)+"_"+graphName
        if name not in self.figure_names:
            self.figure_names.append(name)
            data = self.data_functions[dataName](self,financeInfo,*args)
            fig.create_image(name,data,graphName)
        return "\\includegraphics{}".format("{"+name+".png}")

    @_graphCallable(data_functions)
    def current_balances_data(self,financeInfo):
        return financeInfo.account_details

    @_graphCallable(data_functions,int)
    def item_breakdown_data(self,financeInfo,no_categories):
        payments_raw = self.purchases_raw(financeInfo)
        payments_raw["amount"] = payments_raw.groupby(["to"])["amount"].transform("sum")
        payments_raw = payments_raw.drop_duplicates(subset=["from"])
        if no_categories > 0:
            #TODO - not yet fully implemented
            return payments_raw
        else:
            return payments_raw

    @_reportCallable(report_functions,int)
    def item_breakdown_table(self,financeInfo,no_categories):
        return self.item_breakdown_data(financeInfo,no_categories).to_latex(header=["Amount","From","To","Date"],index=False).replace(" 12:00:00","").replace(" 00:00:00","")
