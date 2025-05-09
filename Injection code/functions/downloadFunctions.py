from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import os
import pickle
import json
import zipfile
from datetime import datetime
from functions.classTables import Business, Product, Reviewer, Social, Search, Contact, Metrics, PostProducts, Region, ReviewerAffiliates, Address, SupplierCustomer, Review, ShoppingCenterBusinesses, Post, ReviewerOwns, Detail
from .parsingFunctions import process_google_json, process_reviewerHistory
import ijson 
import psutil
from ijson import items
import traceback



SCOPES = ['https://www.googleapis.com/auth/drive']
TOKEN_PATH = 'token.pickle'
CREDENTIALS_PATH = 'client_secrets.json'

def get_drive_service():
    credentials = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            credentials = pickle.load(token)
    
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            raise Exception("Need to generate fresh token. Run auth_setup.py first")
    
    return build('drive', 'v3', credentials=credentials)

def get_zip_files(service, folder_id):
    """Get all ZIP files in a specific folder"""
    query = f"'{folder_id}' in parents and (mimeType = 'application/zip' or mimeType = 'application/x-zip-compressed')"

    
    try:
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)',
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        # print(results.get('files', []))
        return results.get('files', [])
    except Exception as e:
        print(f"Error getting ZIP files: {str(e)}")
        return []


def download_zip(service, file_id, filename):
    """Download a ZIP file from Google Drive to current directory"""
    request = service.files().get_media(fileId=file_id)
    download_dir = "fileDownloadLocation"
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    
    zip_path = os.path.join(download_dir, filename)
    
    
    with open(zip_path, 'wb') as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    
    return zip_path

# def extract_and_process_jsons(zip_path):
#     def extract_and_process_jsons_generator(zip_path):
#         """Extract JSONs from ZIP and process them one at a time"""
#         # returnTables = []
        
#         with zipfile.ZipFile(zip_path, 'r') as zf:
#             json_files = (
#                 f for f in zf.namelist() 
#                 if f.endswith('.json') and 
#                 not any(part.startswith('_') for part in f.split('/')) and
#                 f != "batch.json"
#             )
            
#             i = 0
#             for json_file in json_files:
#                 file_info = zf.getinfo(json_file)
#                 modified_time = datetime(*file_info.date_time)
                
#                 try:
#                     with zf.open(json_file) as f:
#                         # json_content = next(items(f, ''))
#                         json_content = json.loads(f.read().decode('utf-8'))
#                         # if next(json_content, None):
#                         if isinstance(json_content, dict):
#                             processed = process_google_json(json_content, modified_time)
#                             i += 1
#                             if i % 10000 == 0:
#                                 print(f"processing {json_file} {i}")
#                                 process = psutil.Process()
#                                 print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")
                                
#                             if processed:
#                                 yield processed
                                
#                 except Exception as e:
#                     print(f"Error processing {json_file}: {str(e)}")
        
#         os.remove(zip_path)

#     returnTables = []
#     for item in extract_and_process_jsons_generator(zip_path):
#         returnTables.append(item)
#         if len(returnTables)==100:
#             yield returnTables
#             returnTables= []

#     if returnTables:
#         yield returnTables


def extract_and_process_jsons(zip_path, firstRunThrough, typeParse="main"):
    def extract_and_process_jsons_generator(zip_path,firstRunThrough,typeParse):
        """Extract JSONs from ZIP and process them one at a time"""
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            json_files = (
                f for f in zf.namelist() 
                if f.endswith('.json') and 
                "MACOSX" not in f and 
                f != "batch.json"
            )
            
            
            i = 0
            
            for json_file in json_files:
                # print(json_file)
               
                file_info = zf.getinfo(json_file)
                modified_time = datetime(*file_info.date_time)
                
                try:
                    with zf.open(json_file) as f:
                        raw_content = f.read()
                        
                        # Diagnostic checks
                        if len(raw_content) == 0:
                            print(f"Warning: {json_file} is empty")
                            continue
                            
                        try:
                            decoded_content = raw_content.decode('utf-8')
                        except UnicodeDecodeError as ude:
                            print(f"Decoding error in {json_file}: {str(ude)}")
                            print(f"First 100 bytes: {raw_content[:100]}")
                            continue
                            
                        # Check if content starts with valid JSON characters
                        if not decoded_content.strip().startswith('{') and not decoded_content.strip().startswith('['):
                            print(f"Warning: {json_file} doesn't start with valid JSON")
                            print(f"Content starts with: {decoded_content.strip()[:100]}")
                            continue
                        
                        json_content = json.loads(decoded_content)
                        
                        if isinstance(json_content, dict):
                            if typeParse=="main":
                                processed = process_google_json(json_content, modified_time,firstRunThrough, json_file)
                            elif typeParse=="reviewers":
                                processed = process_reviewerHistory(json_content, modified_time)
                                
                            else:
                                print("check parsing type")
                            i += 1
                            if i % 1000 == 0:
                                print(f"processing {json_file} {i}")
                                process = psutil.Process()
                                print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")
                                
                            if processed:
                                
                                yield processed
                            else:
                                print("NOTHING RETURNED SOMEHOW")
                        else:
                            print("PROBLEM FILE:", json_file)
                                
                except json.JSONDecodeError as je:
                    print(f"JSON decode error in {json_file}: {str(je)}")
                    print(f"Content preview: {decoded_content[:200]}")
                except Exception as e:
                    traceback.print_exc()
                    print(f"Error3 processing {json_file}: {str(e)}")
        if not firstRunThrough:
            os.remove(zip_path)

    returnTables = []
    # j=0
    for item in extract_and_process_jsons_generator(zip_path,firstRunThrough,typeParse):
        returnTables.append(item)
        if len(returnTables)==100:
            yield returnTables
            returnTables= []

    if returnTables:
        yield returnTables



def process_drive_folder(folder_id):
    """Main function to process a Google Drive folder"""
    service = get_drive_service()
    
    # Get all ZIP files in the folder
    zip_files = get_zip_files(service, folder_id)
    all_tables = []
    
    for zip_file in zip_files:
        try:
            # Download ZIP
            zip_path = download_zip(service, zip_file['id'], zip_file['name'])
            
            # Process JSONs in the ZIP
            tables = extract_and_process_jsons(zip_path)
            all_tables.extend(tables)
            
        except Exception as e:
            print(f"Error processing ZIP file {zip_file['name']}: {str(e)}")
            continue
    
    return all_tables