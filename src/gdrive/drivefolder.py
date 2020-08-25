import src.gdrive.docobject as obj
import src.gdrive.docfile as file
import googleapiclient.http as media

class DriveFolder(obj.DocObject):
    """ A class wrapping drive functionality to allow the easy saving &
    loading of particular files all stored with a particular folder in
    the user's Google Drive.

    :param folder_name: the name of the folder in the user's drive
    :type folder_name: str

    :raises Exception: Exception thrown if 0 or multiple foldername matches
    """
    def __init__(self,folder_name):
        """ Constructor method
        """
        super(DriveFolder,self).__init__()
        self.folder_name = folder_name
        #List of all items with this name
        folder_results = self.get_all_results(
            fields = "nextPageToken, files(id,capabilities)",
            pageSize = 50,
            q = "name = '{}'".format(folder_name))
        #List of ids for valid folders
        folder_ids = [
            item['id']
            for item in folder_results
            if item['capabilities']['canListChildren']]
        if len(folder_ids) == 0:
            #Create a folder
            metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            file = drive_service.files().create(
                body = metadata,
                fields = 'id').execute()
            folder_ids.append(file.get('id'))
        elif len(folder_ids) > 1:
            errorcode = "Multiple folders with the name {} found."
            errorcode = errorcode.format(folder_name)
            raise Exception(errorcode)
        self.folder_id = folder_ids[0]
        self.refresh_dict()
        for item in ["Shortcuts","Balances","Payments","Scheduled"]:
            if item not in self.subitem_dict:
                metadata={
                    "name": item,
                    "parents": [self.folder_id],
                    "mimeType": "application/vnd.google-apps.document"
                }
                file = self.service.files().create(
                    body = metadata,
                    fields = 'id').execute()
                self.subitem_dict[item] = file.get('id')

    def refresh_dict(self):
        """ Provides internal dictionary with names and IDs of
        all files located inside the folder.
        """
        self.subitem_dict = {}
        results = self.get_all_results(
            fields = "nextPageToken, files(id,name)",
            pageSize = 50,
            q = "'{}' in parents".format(self.folder_id))
        for item in results:
            self.subitem_dict[item["name"]] = item["id"]

    def child_file(self,filename):
        """ Convenience function creating a ChildDocFile of a specified
        file within this folder

        :param filename: the name of the file to access
        :type filename: str

        :returns: A ChildDocFile of the given filename
        :rtype: class:`src.gdrive.drivefolder.ChildDocFile`
        """
        return ChildDocFile(self,filename)

    def save_pdf(self,name_on_disk,name_in_drive):
        """ Saves a PDF from the disk to the Google Drive

        :param name_on_disk: the name of the PDF to upload
        :type name_on_disk: str
        :param name_in_drive: the PDFs name on the Drive
        :type name_in_drive: str
        """
        tfid = None
        for key in self.subitem_dict:
            if key == name_in_drive:
                tfid = self.subitem_dict[key]
                break
        if tfid is None:
            media_body = media.MediaFileUpload(name_on_disk,resumable=True,mimetype="application/pdf")
            metadata={
                "name": name_in_drive,
                "parents": [self.folder_id]
            }
            self.service.files().create(
                body = metadata,
                media_body = media_body).execute()
            self.refresh_dict()
        else:
            media_body = media.MediaFileUpload(name_on_disk,resumable=True)
            self.service.files().update(
                fileId = tfid,
                media_body = media_body).execute()

    def __getitem__(self,key):
        """ Returns a file ID from internal dictionary

        :param key: the file name
        :type key: str
        """
        return self.subitem_dict[key]

class ChildDocFile(file.DocFile):
    """ Extension of DocFile for a file inside a given DriveFolder

    :param parent: the DriveFolder within which this file exists
    :type parent: class:`src.gdrive.drivefolder.DriveFolder`
    :param filename: the name of the file
    :type filename: str
    """
    def __init__(self,parent,filename):
        """Constructor method
        """
        self.parent = parent
        self.filename = filename
        self.file_id = parent[filename]
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
