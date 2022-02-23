import io
import tempfile

import flask
from flask_cors import CORS


from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import googleapiclient.discovery
from drive_google_auth import build_credentials, get_user_info

from werkzeug.utils import secure_filename

# app = flask.Blueprint('drive_google', __name__)
# CORS(app)

def build_drive_api_v3(token):
    credentials = build_credentials(token)
    return googleapiclient.discovery.build('drive', 'v3', credentials=credentials)

def save_file(file_name, mime_type, file_data, token):
    drive_api = build_drive_api_v3(token)
    # generate_ids_result = drive_api.generateIds(count=1).execute()
    # file_id = generate_ids_result['ids'][0]

    body = {
        'name': file_name,
        'mimeType': mime_type,
    }
    media_body = MediaIoBaseUpload(file_data,
                                   mimetype=mime_type,
                                   resumable=True)

    store = drive_api.files().create(body=body,
                     media_body=media_body,
                     fields='id,name,mimeType,createdTime,modifiedTime').execute()
    return store.get('id')