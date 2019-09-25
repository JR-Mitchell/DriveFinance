from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload, MediaFileUpload
from httplib2 import Http
from oauth2client import file, client, tools
import StringIO, os, datetime, pytz, uuid

BST = pytz.timezone('Europe/London')
UTC = pytz.utc
SCOPES = 'https://www.googleapis.com/auth/drive'

class DocObject(object):
    def __init__(self):
        self.store = file.Storage('token.json')
        self.creds = self.store.get()
        if not self.creds or self.creds.invalid: ##If unable to authorise
            print("Unable to authorise google account! Please run with gui access so that a browser window can be opened.")
            flow = client.flow_from_clientsecrets('credentials.json',SCOPES)
            self.creds = tools.run_flow(flow,self.store)
        self.service = build('drive','v3',http=self.creds.authorize(Http()))

    def get_all_results(self,*args,**kwargs):
        """
        convenience funtion to scour through request results and return findings
        """
        if "fields" in kwargs:
            if "nextPageToken" not in kwargs["fields"]:
                kwargs["fields"] = kwargs["fields"] + ", nextPageToken"
        else:
            kwargs["fields"] == "nextPageToken"
        returnList = []
        nextPageToken = ""
        while nextPageToken is not None:
            if nextPageToken != "": kwargs['pageToken'] = nextPageToken
            results=self.service.files().list(*args,**kwargs).execute()
            items = results.get('files',[])
            nextPageToken = results.get('nextPageToken')
            if not items: pass
            else:
                for item in items: returnList.append(item)
        return returnList

class DocFolder(DocObject):
    def __init__(self,folder_name):
        """
        A class wrapping drive functionality to allow the easy saving & loading
        of particular files all stored within a particularly named folder in
        the user's google drive.

        :param: folder_name: a string identifying the name of the folder in the user's drive
        """
        super(DocFolder,self).__init__()
        self.folder_name = folder_name
        folderResults = self.get_all_results(fields="nextPageToken, files(id,capabilities)",pageSize=50,q="name = '{}'".format(folder_name))
        folderIds = [item['id'] for item in folderResults if item['capabilities']['canListChildren']]
        if len(folderIds) == 0:
            raise Exception("No folders with the name {} found.".format(folder_name))
        elif len(folderIds) > 1:
            raise Exception("Multiple folders with the name {} found. Please specify a unique folder name.".format(folder_name))
        self.folder_id = folderIds[0]
        self.refresh_dict()

    def refresh_dict(self):
        """
        Provides self.subitem_dict with a list of files located inside the folder.
        """
        self.subitem_dict = {}
        for item in self.get_all_results(fields="nextPageToken, files(id,name)",pageSize=50,q="'{}' in parents".format(self.folder_id)):
            self.subitem_dict[item["name"]] = item["id"]

    def child_file(self,filename):
        return ChildDocFile(self,filename)

    def get_metadata(self,filename):
        return self.service.files().get(fileId=self.subitem_dict[filename]).execute()

    def save_pdf(self,name_on_disk,name_in_drive):
        tfid = None
        for item in self.subitem_dict:
            if item == name_in_drive:
                tfid = self.subitem_dict[item]
        if tfid == None:
            raise Exception("No pdf of name {} found in this folder".format(name_in_drive))
        media_body = MediaFileUpload(name_on_disk,resumable=True)
        self.service.files().update(fileId=tfid,media_body=media_body).execute()

class DocFile(DocObject):
    def __init__(self,filename):
        """
        A class wrapping drive functionality to allow the easy saving & loading
        of a particular file stored within the user's google drive.

        :param: filename: the name of the file
        """
        super(DocFile,self).__init__()
        self.filename = filename
        fileIds = self.get_all_results(fields="nextPageToken, files(id)",pageSize=50,q="name = {}".format(filename))
        if len(fileIds) == 0:
            raise Exception("No files with the name {} found.".format(filename))
        elif len(fileIds) > 1:
            raise Exception("Multiple files with the name {} found. Please specify a unique file name or access via a folder.".format(filename))
        self.file_id = fileIds[0]["id"]
        self._initial_content = self._read_to_string()

    def write_from_string(self,string,mimeType="text/plain"):
        myFile = StringIO.StringIO()
        myFile.write(string)
        media_body = MediaIoBaseUpload(myFile,mimetype=mimeType,resumable=True)
        self.assert_no_changes()
        request = self.service.files().update(fileId = self.file_id,media_body=media_body)
        response = None
        while response is None:
            status,response = request.next_chunk()
        myFile.close()

    def _read_to_string(self,mimeType="text/plain"):
        myFile = StringIO.StringIO()
        request = self.service.files().export_media(fileId = self.file_id,mimeType=mimeType)
        downloader = MediaIoBaseDownload(myFile,request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        return_str = myFile.getvalue()
        myFile.close()
        return return_str

    @property
    def initial_content(self):
        return self._initial_content

    def read_to_rtf(self):
        return self._read_to_string("application/rtf")

    def assert_no_changes(self):
        new_str = self._read_to_string()
        if new_str != self.initial_content: raise Exception("In the time between initial load and function call, the file {} has been modified!".format(self.filename))

class ChildDocFile(DocFile):
    def __init__(self,parent,filename):
        """
        """
        self.parent = parent
        self.file_id = parent.subitem_dict[filename]
        self._initial_content = self._read_to_string()

    @property
    def store(self):
        return self.parent.store()

    @property
    def creds(self):
        return self.parent.creds

    @property
    def service(self):
        return self.parent.service
