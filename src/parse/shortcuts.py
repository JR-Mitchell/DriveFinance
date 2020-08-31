# -*- coding: utf-8 -*-

import filereader

class ParsedShortcuts(filereader.InputFileReader):
    """ Object for parsing the Shortcuts file

    :param child_file: The DocFile (or ChildDocFile) to read
    :type child_file: class: `src.gdrive.docfile.DocFile`
    """
    def __init__(self,child_file):
        super(ParsedShortcuts,self).__init__(child_file)
        self.dict = dict([
            [item.strip() for item in line.split(":")]
            for line in self._lines])

    """ Adds a shortcut to the file

    :param key: The shortcut key, beginning with an asterisk
    :type key: string
    :param code: The payment code
    :type code: string
    """
    def add_line(self,key,code):
        if key in self.dict:
            #Modifying codes not yet implemented
            errorcode = "This shortcut key already exists!"
            raise Exception(errorcode)
        else:
            self.dict[key] = code
            self._lines.append("{}: {}".format(key,code))
