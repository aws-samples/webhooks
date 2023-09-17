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

from botocore.config import Config

BOTO3_CONFIG = Config(
    signature_version="v4",
    s3={
        "addressing_style": "virtual",
        "us_east_1_regional_endpoint": "regional",
    },
    retries={
        "max_attempts": 10,
        "mode": "standard",
    },
    tcp_keepalive=True,
)

# Environment variables
ENV_BUCKET_NAME = "BUCKET_NAME"
ENV_BUCKET_OWNER_ID = "BUCKET_OWNER_ID"
ENV_BUCKET_PREFIX = "BUCKET_PREFIX"
ENV_KMS_KEY_ID = "KMS_KEY_ID"
ENV_TABLE_NAME = "TABLE_NAME"
ENV_SSM_PARAMETER = "SSM_PARAMETER"

PARTITION_KEY = "pk"
SORT_KEY = "sk"

EXPIRES_IN_DAYS = 3
