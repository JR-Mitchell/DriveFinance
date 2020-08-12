# -*- coding: utf-8 -*-

import filereader

class ParsedBalances(filereader.InputFileReader):
    """ Object for parsing the Balances file

    :param child_file: The DocFile (or ChildDocFile) to read
    :type child_file: class: `src.doc.docfile.DocFile`

    :raises Exception: If the file features an unknown command
    """
    def __init__(self,child_file):
        super(ParsedBalances,self).__init__(child_file)
        self.init_args = []
        self.check_args = []
        for line in self._lines:
            linesplit = line.split(":")
            argsplit = linesplit[1].split(",")
            cmdname = linesplit[0].strip()
            if cmdname == "init":
                self.init_args.append(argsplit)
            elif cmdname == "check":
                self.check_args.append(argsplit)
            else:
                errorcode = "Unknown balance input command: {}".format(cmdname)
                raise Exception(errorcode)
        self.new_text = ("#Pattern 1: 'init:{account},{amount}' sets the"
            + " initial balance of account to amount.\n"
            + "#Pattern 2: 'check:{account},{amount}' checks if the current"
            + " balance of account is amount and if not, makes a discrepancy"
            + " transfer from/to the void.")
