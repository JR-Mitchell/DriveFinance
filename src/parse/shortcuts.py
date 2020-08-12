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
