#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
* Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
* SPDX-License-Identifier: MIT-0
*
* Permission is hereby granted, free of charge, to any person obtaining a copy of this
* software and associated documentation files (the "Software"), to deal in the Software
* without restriction, including without limitation the rights to use, copy, modify,
* merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
* permit persons to whom the Software is furnished to do so.
*
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
* INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
* PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
* HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
* OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
* SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import base64
from dataclasses import dataclass
import hashlib
import os
from typing import Dict, TYPE_CHECKING, Optional

from aws_lambda_powertools import Logger
import boto3
import botocore

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

from app import constants, exceptions

__all__ = ["S3", "S3Object"]

logger = Logger(child=True)
BUCKET_NAME = os.getenv(constants.ENV_BUCKET_NAME)
BUCKET_OWNER_ID = os.getenv(constants.ENV_BUCKET_OWNER_ID)
KMS_KEY_ID = os.getenv(constants.ENV_KMS_KEY_ID)


@dataclass(kw_only=True, slots=True, frozen=True)
class S3Object:
    bucket: str
    key: str
    version_id: str


class S3:
    def __init__(self, session: boto3.Session) -> None:
        self._client: "S3Client" = session.client("s3", config=constants.BOTO3_CONFIG)

    def put_object(
        self,
        key: str,
        body: str,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = "application/json",
    ) -> S3Object:
        checksum_md5 = self._checksum_algo(body, "md5")
        checksum_sha1 = self._checksum_algo(body, "sha1")

        params = {
            "ACL": "bucket-owner-full-control",
            "Body": body,
            "Bucket": BUCKET_NAME,
            "ContentMD5": checksum_md5,
            "ChecksumAlgorithm": "SHA1",
            "ChecksumSHA1": checksum_sha1,
            "Key": key,
            "ServerSideEncryption": "aws:kms",
            "SSEKMSKeyId": KMS_KEY_ID,
            "StorageClass": "STANDARD_IA",
        }
        if content_type:
            params["ContentType"] = content_type
        if metadata:
            params["Metadata"] = metadata
        if BUCKET_OWNER_ID:
            params["ExpectedBucketOwner"] = BUCKET_OWNER_ID

        logger.debug("put_object", params=params)
        try:
            response = self._client.put_object(**params)
        except botocore.exceptions.ClientError as error:
            logger.exception("Failed to write object to S3", error)
            raise exceptions.S3PutError()

        return S3Object(bucket=BUCKET_NAME, key=key, version_id=response["VersionId"])

    def delete_object(self, key: str, version_id: Optional[str] = None) -> None:
        params = {
            "Bucket": BUCKET_NAME,
            "Key": key,
        }
        if version_id:
            params["VersionId"] = version_id
        if BUCKET_OWNER_ID:
            params["ExpectedBucketOwner"] = BUCKET_OWNER_ID

        logger.debug("delete_object", params=params)
        try:
            self._client.delete_object(**params)
        except botocore.exceptions.ClientError as error:
            logger.exception("Failed to delete object from S3", error)
            raise exceptions.S3DeleteError()

    @classmethod
    def _checksum_algo(cls, data: str, algo: str = "md5") -> str:
        hash = hashlib.new(algo, bytes(data, "utf-8")).digest()
        return base64.b64encode(hash).decode()
