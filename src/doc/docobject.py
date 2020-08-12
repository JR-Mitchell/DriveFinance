import googleapiclient.discovery as discovery
import httplib2 as http
from oauth2client import file, client, tools
import pytz

BST = pytz.timezone('Europe/London')
UTC = pytz.utc
SCOPES = 'https://www.googleapis.com/auth/drive'

class DocObject(object):
    """Convenience object for interfacing with Google Drive API v3
    """

    def __init__(self):
        """Constructor method
        """
        self.store = file.Storage('token.json')
        self.creds = self.store.get()
        if not self.creds or self.creds.invalid: #If unable to authorise
            print("Unable to authorise Google account! "
                  +"If possible, a browser window will pop up "
                  +"enabling authorisation.")
            flow = client.flow_from_clientsecrets(
                'credentials.json',
                SCOPES)
            #Running client authorisation flow (opens browser)
            self.creds = tools.run_flow(flow,self.store)
        self.service = discovery.build(
            'drive',
            'v3',
            http = self.creds.authorize(http.Http()))

    def get_all_results(self,**kwargs):
        """Convenience function returning results of a particular google client
        request. Keyword arguments are identical to those documented at:
        https://developers.google.com/drive/api/v3/reference/files/list
        """
        if "fields" in kwargs:
            if "nextPageToken" not in kwargs["fields"]:
                kwargs["fields"] = kwargs["fields"] + ", nextPageToken"
        else:
            kwargs["fields"] = "nextPageToken"
        return_list = []
        nextPageToken = "" #mixedCase as this is a drive keyword
        while nextPageToken is not None:
            if nextPageToken != "":
                kwargs["pageToken"] = nextPageToken
            results = self.service.files() \
                                  .list(**kwargs) \
                                  .execute()
            items = results.get('files',[])
            nextPageToken = results.get('nextPageToken')
            if not items: pass
            else:
                for item in items:
                    return_list.append(item)
        return return_list
