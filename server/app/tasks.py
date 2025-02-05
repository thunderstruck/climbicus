import os

import datetime

import uuid
import werkzeug

from app import celery, s3_client, io
from app.utils.encoding import b64str_to_bytes, bytes_to_b64str
from app.utils.io import S3InputOutputProvider


@celery.task()
def upload_test_file_task(b64_str, filepath):
    filedir = os.path.dirname(filepath)
    if not os.path.exists(filedir):
        os.makedirs(filedir)

    fb = b64str_to_bytes(b64_str)
    with open(filepath, "wb") as f:
        f.write(fb)

    return filepath


@celery.task()
def upload_file_task(b64_str, bucket, remote_path, content_type):
    fb = b64str_to_bytes(b64_str)
    resp = s3_client.put_object(
        Body=fb,
        Bucket=bucket,
        Key=remote_path,
        ContentType=content_type,
    )

    assert resp["ResponseMetadata"]["HTTPStatusCode"] == 200

    return f"s3://{bucket}/{remote_path}"


def upload_file(fbytes_image, file_content_type, remote_path):
    filepath =  io.provider.upload_filepath(remote_path)
    b64_str = bytes_to_b64str(fbytes_image)

    if isinstance(io.provider, S3InputOutputProvider):
        bucket = io.provider.bucket
        upload_file_task.delay(b64_str, bucket, remote_path, file_content_type)
    else:
        upload_test_file_task.delay(b64_str, filepath)
    return filepath


def store_image(fbytes_image, file_content_type, dir_name, gym_id, image_size):
    now = datetime.datetime.utcnow()
    hex_id = uuid.uuid4().hex
    imagepath = f"{dir_name}/from_users/gym_id={gym_id}/year={now.year}/month={now.month:02d}/{image_size}/{hex_id}.jpg"

    saved_image_path = upload_file(fbytes_image, file_content_type, imagepath)
    return saved_image_path


