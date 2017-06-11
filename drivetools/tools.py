# tools.py

import httplib2
import os
import io
import shutil as sh

from apiclient import discovery
from apiclient.http import MediaIoBaseDownload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import argparse

# try:
#     import argparse
#     flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
# except ImportError:
#     flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES_READONLY = 'https://www.googleapis.com/auth/drive.readonly'
APPLICATION_NAME = 'Drive API Python Download'


MIME_CSV_SHEETS = 'text/csv'
MIME_FILE = 'application/vnd.google-apps.file'


def get_credentials(client_secret):
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'drive-downloads.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(client_secret,
                                              SCOPES_READONLY)
        # flow.user_agent = APPLICATION_NAME

        flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:
            # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def download(client_secret, file_id, destination):
    """
    Download a specific file.
    """
    credentials = get_credentials(client_secret)
    print('Got credentials.')
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)

    request = service.files().get_media(fileId=file_id)
    # backup existing file
    if os.path.exists(destination):
        backup = destination + '.bak'
        sh.copyfile(destination, backup)
        print('Backup file: {}'.format(backup))
        # fh = io.BytesIO()
    fh = io.open(destination, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print("Download %d%%." % int(status.progress() * 100))
    print('File saved as {}'.format(destination))

    # results = service.files().list(
    #     pageSize=10, fields="nextPageToken, files(id, name)").execute()
    # items = results.get('files', [])
    # if not items:
    #     print('No files found.')
    # else:
    #     print('Files:')
    #     for item in items:
    #         print('{0} ({1})'.format(item['name'], item['id']))


def export(client_secret, file_id, mimeType, destination):
    """
    Download a specific file.
    """
    credentials = get_credentials(client_secret)
    print('Got credentials.')
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)

    request = service.files().export_media(fileId=file_id,
                                           mimeType=mimeType)
    # request = service.files().get_media(fileId=file_id)
    # backup existing file
    if os.path.exists(destination):
        backup = destination + '.bak'
        sh.copyfile(destination, backup)
        print('Backup file: {}'.format(backup))
        # fh = io.BytesIO()
    fh = io.open(destination, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print("Download %d%%." % int(status.progress() * 100))
    print('File saved as {}'.format(destination))


def _add_query_condition(query, condition, field, op, value):
    if len(query) > 0:
        query += ' {} '.format(condition)
    query = query + "{} {} '{}'".format(field, op, value)
    return query


def _add_and_query(query):
    if len(query) > 0:
        return query + ' and '
    else:
        return query


def search(client_secret,
           name=None, parent_id=None, mimeType=None,
           modified_time=None):
    """
    Search for a file in Goolge Drive
    """
    credentials = get_credentials(client_secret)
    print('Got credentials.')
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)

    query = ''

    if name is not None:
        query += "name = '{}'".format(name)

    if parent_id is not None:
        if len(query) > 0:
            query += ' and '
        query += "'{}' in parents".format(parent_id)

    if modified_time is not None:
        query = _add_and_query(query)
        query += "modifiedTime > '{}'".format(modified_time)

    if mimeType is not None:
        if len(query) > 0:
            query += ' and '
        query += "mimeType={}".format(mimeType)

    print('Query: {}'.format(query))
    page_token = None
    while True:
        request = service.files().list(q=query,
                                       spaces='drive',
                                       fields='nextPageToken, files(id, name)',
                                       pageToken=page_token).execute()
        for file in request.get('files', []):
            # Process change
            print('Found file: %s (%s)' % (file.get('name'), file.get('id')))
        page_token = request.get('nextPageToken', None)
        if page_token is None:
            break
