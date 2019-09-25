import subprocess,os

class TexSection():
    def __init__(self,filename):
        self.innertext = ""
        with open("templates/{}.template".format(filename),"r") as myFile:
            self.innertext = myFile.read()

    def doctext(self,spacer,info_dict):
        return self.innertext.replace("[vspacetxt]","\n\\vspace{{"+spacer+"}}\n").format(**info_dict)

class TexReport():
    def __init__(self,title,datetime,spacer='5mm',header="\\documentclass[12pt]{article}\n\\usepackage{booktabs}\n\\usepackage{graphicx}\n\\usepackage{longtable}",info_dict = {}):
        """
        Creates and allows generation of a latex report
        """
        self.title = title
        self.spacer = spacer
        self.header = header
        self.sections = []
        self.datetime = datetime
        self.info_dict = info_dict
        self.complete_dictionary()

    def complete_dictionary(self):
        if "raw_dataframe" in self.info_dict:
            raw_df = self.info_dict["raw_dataframe"]
            self.info_dict["purchases_only"]=raw_df.loc[raw_df["type"]=="purchase",["amount","from","to","date_made"]].to_latex(header=["Amount","From","To","Date"],index=False).replace(" 12:00:00","")
            self.info_dict["transfers_only"]=raw_df.loc[raw_df["type"]=="transfer",["amount","from","to","date_made"]].to_latex(header=["Amount","From","To","Date"],index=False).replace(" 12:00:00","")
            if "account_details" in self.info_dict:
                bal_dict = self.info_dict["account_details"]
                self.info_dict["balances_only"] = bal_dict.reindex(columns=["from","amount"]).to_latex(index=False,header=["Account","Balance"])
            raw_df["amount"] = raw_df.groupby(["from","to"])["amount"].transform("sum")
            raw_df = raw_df.drop_duplicates(subset=["from","to"])
            raw_df.sort_values(by=["to","from"],inplace=True)
            self.info_dict["grouped_purchases_only"]=raw_df.loc[raw_df["type"]=="purchase",["amount","from","to"]].to_latex(header=["Total","From","To"],index=False).replace(" 12:00:00","")
            raw_df["amount"] = raw_df.groupby(["to"])["amount"].transform("sum")
            raw_df = raw_df.drop_duplicates(subset=["to"])
            raw_df.sort_values(by="amount",inplace=True,ascending=False)
            self.info_dict["purchases_by_item"]=raw_df.loc[raw_df["type"]=="purchase",["to","amount"]].to_latex(header=["To","Total"],index=False).replace(" 12:00:00","")

    def generate_doctext(self):
        self.doctext = self.header+"\n\n\\title{"+self.title+"}\n\n\\begin{document}\n\\maketitle\n"
        self.doctext += "Generated at: {}\n".format(self.datetime)
        for section in self.sections:
            self.doctext += section.doctext(self.spacer,self.info_dict).replace("begin{tabular}","begin{longtable}").replace("end{tabular}","end{longtable}")
        self.doctext += "\\end{document}"

    def produce_pdf(self,output_name):
        with open("tmp/{}.tex".format(output_name),"w") as outFile:
            outFile.write(self.doctext)
        tex_process = subprocess.Popen("pdflatex {}.tex".format(output_name),cwd=os.path.join(os.getcwd(),"tmp"),shell=True)
        tex_process.wait()

    @classmethod
    def clear_tmp(cls,name):
        cleanup_process = subprocess.Popen("rm tmp/{}.*".format(name),shell=True)
        cleanup_process.wait()
