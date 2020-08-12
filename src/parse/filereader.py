# -*- coding: utf-8 -*-

import src.gdrive.drivefolder as odf

class InputFileReader(object):
    """ General file for parsing a doc file as a series of lower case lines,
    ignoring blank lines and comments past #

    :param child_file: The DocFile (or ChildDocFile) to read
    :type child_file: class: `src.gdrive.docfile.DocFile`
    """
    def __init__(self,child_file):
        """Constructor method
        """
        text = child_file.initial_content.lower()
        lines = text.strip("\xef\xbb\xbf").split("\r\n")
        lines = [line.split("#")[0].strip() for line in lines]
        self._lines = [line for line in lines if line != ""]

    def __getitem__(self,index):
        """ Gets a specific line by index

        :param index: the line index
        :type index: int
        :return: The line at given index
        :rtype: str
        """
        return self.lines[arg]

    def __iter__(self):
        return iter(self.lines)
