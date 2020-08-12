import src.gdrive.docobject as obj
import StringIO
import googleapiclient.http as media

class DocFile(obj.DocObject):
    """ A class wrapping drive functionality to allow the easy saving &
    loading of a particular file stored within the user's Google Drive.

    :param filename: the name of the file
    :type filename: str

    :raises Exception: Exception thrown if 0 or multiple filename matches
    """
    def __init__(self,filename):
        """Constructor method
        """
        super(DocFile,self).__init__()
        self.filename = filename
        #Getting list of files named filename
        file_ids = self.get_all_results(
            fields="nextPageToken, files(id)",
            pageSize=50,
            q="name = {}".format(filename))
        if len(file_ids) == 0: #No files named filename
            errorcode = "No files with the name {} found.".format(filename)
            raise Exception(errorcode)
        elif len(file_ids) > 1: #Multiple files named filename
            errorcode = "Multiple files with the name {} found."
            errorcode = errorcode.format(filename)
            errorcode += (" Please specify a unique filename"
                + " or access via a folder.")
            raise Exception(errorcode)
        self.file_id = file_ids[0]["id"]
        self.__initial_content = self._read_to_string()

    def write_from_string(self,string,mimetype="text/plain"):
        """ Writes a string to the Google Docs file

        :param string: the information to write to the file
        :type string: str
        :param mimetype: the mimetype to interpret the string as,
            defaults to "text/plain"
        :type mimetype: str, optional

        :raises Exception: Exception if the file has been modified since
            the object initialisation
        """
        my_file = StringIO.StringIO()
        my_file.write(string)
        media_body = media.MediaIoBaseUpload(
            my_file,
            mimetype=mimetype,
            resumable=True)
        self.assert_no_changes()
        request = self.service.files().update(
            fileId = self.file_id,
            media_body = media_body) #Google inconsistent with kwarg casing
        response = None
        while response is None:
            status, response = request.next_chunk()
        my_file.close()

    def _read_to_string(self,mimetype="text/plain"):
        """ Reads the file to a string

        :param mimetype: the mimetype to interpret the file as,
            defaults to "text/plain"
        :type mimetype: str, optional

        :return: the text stored inside this document on drive
        :rtype: str
        """
        my_file = StringIO.StringIO()
        request = self.service.files().export_media(
            fileId = self.file_id,
            mimeType=mimetype)
        downloader = media.MediaIoBaseDownload(my_file,request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        return_str = my_file.getvalue()
        my_file.close()
        return return_str

    @property
    def initial_content(self):
        return self._initial_content

    def assert_no_changes(self):
        """ Ensures that the file has not been modified since reading

        :raises AssertionError: If the file has been modified since
            the object initialisation
        """
        new_str = self._read_to_string()
        errorcode = ("In the time between initialising its DocFile object and"
            + " calling this function, the document {}".format(self.filename)
            + " has been modified.")
        assert new_str == self.initial_content, errorcode
