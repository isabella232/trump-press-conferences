import app_config
import os

from app_config import authomatic
from authomatic.adapters import WerkzeugAdapter
from exceptions import KeyError

SPREADSHEET_URL_TEMPLATE = 'https://docs.google.com/feeds/download/spreadsheets/Export?exportFormat=xlsx&key=%s'

def get_credentials():
    """
    Read Authomatic credentials object from disk and refresh if necessary.
    """
    file_path = os.path.expanduser(app_config.GOOGLE_OAUTH_CREDENTIALS_PATH)

    try:
        with open(file_path) as f:
            serialized_credentials = f.read()
    except IOError:
        return None

    credentials = authomatic.credentials(serialized_credentials)

    if not credentials.valid:
        credentials.refresh()
        save_credentials(credentials)

    return credentials

def save_credentials(credentials):
    """
    Take Authomatic credentials object and save to disk.
    """
    file_path = os.path.expanduser(app_config.GOOGLE_OAUTH_CREDENTIALS_PATH)
    with open(file_path, 'w') as f:
        f.write(credentials.serialize())

def get_document(key, file_path):
    """
    Uses Authomatic to get the google doc
    """
    credentials = get_credentials()
    url = SPREADSHEET_URL_TEMPLATE % key
    response = app_config.authomatic.access(credentials, url)

    if response.status != 200:
        if response.status == 404:
            raise KeyError("Error! Your Google Doc does not exist or you do not have permission to access it.")
        else:
            raise KeyError("Error! Google returned a %s error" % response.status)

    with open(file_path, 'wb') as writefile:
        writefile.write(response.content)

def _has_api_credentials():
    """
    Test for API credentials
    """
    client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
    client_secret = os.environ.get('GOOGLE_OAUTH_CONSUMER_SECRET')
    salt = os.environ.get('AUTHOMATIC_SALT')
    return bool(client_id and client_secret and salt)