#!/usr/bin/python3

# copy: scp -i thb-key.pem /Users/maxriedel/dev/uni/s3/gcc/bottletube/server/bottletube.py ubuntu@3.236.205.40:/home/ubuntu/bt/bottletube.py

import os
import time
import uuid
import psycopg2
import json
import requests
from boto3 import resource, session
from bottle import route, run, template, request, default_app

BUCKET_NAME = 'img-bottletube'  # Replace with your bucket name
SAVE_PATH = '/tmp/images/'


@route('/healthcheck')
def health():
    hostname = requests.get('http://169.254.169.254/latest/meta-data/public-hostname').text
    return hostname

@route('/home')
@route('/')
def home():
    # SQL Query goes here later, now dummy data only
    items = []
    cursor.execute('SELECT * FROM image_uploads ORDER BY id')
    for record in cursor.fetchall():
        items.append({'id': record[0],
                      'filename': record[1],
                      'category': record[2]})
    return template('home.tpl', name='BoTube Home', items=items)


@route('/upload', method='GET')
def do_upload_get():
    return template('upload.tpl', name='Upload Image')

@route('/delete', method='GET')
def do_post_delete():
    items = []
    id = request.query['id']
    try:
        cursor.execute(f'SELECT * FROM image_uploads WHERE id = {id};')
        for record in cursor.fetchall():
            items.append({'id': record[0],
                          'filename': record[1],
                          'category': record[2]})
    except:
        return template('delete_failure.tpl', error_message='error in fetch', name='BoTube Delete Failure')
    try:
        s3_resource.Object(BUCKET_NAME, items[0].get('filename')).delete()
    except:
        return template('delete_failure.tpl', error_message='error in S3 Delete', name='BoTube Delete Failure')
    try:
        cursor.execute(f'DELETE FROM image_uploads WHERE id = {id};')
        connection.commit()
    except:
        return template('delete_failure.tpl', error_message='error in DB delete', name='BoTube Delete Failure')
    return template('delete_success.tpl', name='BoTube Delete Success')

@route('/upload', method='POST')
def do_upload_post():
    category = request.forms.get('category')
    upload = request.files.get('file_upload')

    # Check for errors
    error_messages = []
    if not upload:
        error_messages.append('Please upload a file.')
    if not category:
        error_messages.append('Please enter a category.')

    try:
        name, ext = os.path.splitext(upload.filename)
        if ext not in ('.png', '.jpg', '.jpeg'):
            error_messages.append('File Type not allowed.')
    except:
        error_messages.append('Unknown error.')

    if error_messages:
        return template('upload.tpl', name='Upload Image', error_messages=error_messages)

    # Save to SAVE_PATH directory
    if not os.path.exists(SAVE_PATH):
        os.makedirs(SAVE_PATH)
    save_filename = f'{name}_{time.strftime("%Y%m%d-%H%M%S")}{ext}'
    with open(f'{SAVE_PATH}{save_filename}', 'wb') as open_file:
        open_file.write(upload.file.read())

    if ext == '.png':
        content_type = 'image/png'
    else:
        content_type = 'image/jpeg'

    # Upload to S3
    data = open(SAVE_PATH + save_filename, 'rb')
    s3_resource.Bucket(BUCKET_NAME).put_object(Key=f'user_uploads/{save_filename}',
                                               Body=data,
                                               Metadata={'Content-Type': content_type},
                                               ACL='public-read')

    # Write to DB
    # some code has to go here later

    cursor.execute(f"INSERT INTO image_uploads (url, category) VALUES ('user_uploads/{save_filename}','{category}');")
    connection.commit()

    # Return template
    return template('upload_success.tpl', name='Upload Image')


if True:


    # Connect to DB
    # some code has to go here
    sm_session = session.Session()
    client = sm_session.client(service_name='secretsmanager',
                      region_name='us-east-1')
    secret = json.loads(client.get_secret_value(SecretId='db-secrets')
                        .get('SecretString'))
    connection = psycopg2.connect(user=secret['RDS_USERNAME'],
                                  host=secret['RDS_HOSTNAME'],
                                  password=secret['RDS_PASSWORD'], database=secret['RDS_DBNAME'])
    cursor = connection.cursor()
    cursor.execute("SET SCHEMA 'bottletube';")
    connection.commit()

    # Connect to S3
    s3_resource = resource('s3', region_name='us-east-1')

    # Needs to be customized
    # run(host='your_public_dns_name',
    #run(host='0.0.0.0',
    #    port=80)
    os.chdir(os.path.dirname(__file__))
    application = default_app()
