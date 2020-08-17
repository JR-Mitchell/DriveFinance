import interact
import inputparser

class TinkerObject(interact.InteractivePrompt):
    """ Object for interactive tinkering with finance data

    :param finance_data: the FinanceData object to tinker with
    :type finance_data: class: `src.financedata.FinanceData`
    """
    tinker_dict = {}
    def __init__(self,finance_data):
        super(TinkerObject,self).__init__(
            "Interactive tinker prompt. Call 'exit()' to exit.", #header_text
            self.tinker_dict, #function_dict
            0) #offset
        self._finance_data = finance_data
        self._command_history = []
        self._command_history_spot = 0

    def run_once_preprocessing(self):
        print ">>> ",

    def no_command_return(self,text):
        print("No recognised command: '{}'".format(text))
