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

import binascii
import base64
from dataclasses import dataclass
import hmac
import os
from typing import Optional, Dict, Any

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.data_classes.common import BaseProxyEvent
import boto3

from app import resources, constants, exceptions

__all__ = ["BaseProvider", "HTTPBasicCredentials"]

logger = Logger(child=True)

SSM_PARAMETER = os.getenv(constants.ENV_SSM_PARAMETER)


@dataclass(slots=True, frozen=True)
class HTTPBasicCredentials:
    username: str
    password: str


class BaseProvider:
    SIGNATURE_HEADER: Optional[str] = None
    SIGNATURE_ALGO: Optional[str] = None
    SIGNATURE_ENCODING: Optional[str] = None
    PARAMETER_KEY: Optional[str] = "webhook_secret"

    def __init__(self, event: BaseProxyEvent, session: Optional[boto3.Session] = None) -> None:
        self._event = event
        if not session:
            session = boto3._get_default_session()
        self._client = resources.DynamoDB(session)

    @classmethod
    def get_provider_name(cls) -> str:
        raise NotImplementedError

    def verify(self) -> bool:
        if not self.SIGNATURE_HEADER or not self.SIGNATURE_ALGO:
            raise NotImplementedError

        signature = self._event.get_header_value(self.SIGNATURE_HEADER)
        if not signature:
            logger.warning(f"Signature header {self.SIGNATURE_HEADER} not found")
            return False

        payload = self._event.decoded_body
        if not payload:
            logger.warning("Missing payload body")
            return False

        parameter = self.get_parameter()
        key = bytes(parameter[self.PARAMETER_KEY], "utf-8")

        if self.SIGNATURE_ENCODING == "base64":
            computed_signature = hmac.new(key, payload, self.SIGNATURE_ALGO).digest()
            computed_signature = base64.encodebytes(computed_signature).decode().rstrip()
        else:
            computed_signature = hmac.new(key, payload, self.SIGNATURE_ALGO).hexdigest()

        if not hmac.compare_digest(signature, computed_signature):
            logger.warning(
                "Computed signature did not match provided signature",
                signature=signature,
                computed_signature=computed_signature,
            )
            return False

        return True

    def get_event_id(self) -> Optional[str]:
        """
        Return the unique ID for this event
        """
        raise NotImplementedError

    def get_parameter(self) -> Dict[str, Any]:
        if not SSM_PARAMETER:
            return {}

        logger.debug(f"Fetching parameter: {SSM_PARAMETER}")
        return parameters.get_parameter(SSM_PARAMETER, transform="json")

    def is_duplicate(self, event_id: Optional[str]) -> bool:
        if not event_id:
            # if we don't have a unique event ID, treat the event as not a duplicate
            return False

        key = {
            constants.PARTITION_KEY: self.get_provider_name().upper(),
            constants.SORT_KEY: event_id,
        }
        try:
            self._client.get_item(key, attributes=[constants.PARTITION_KEY])
        except exceptions.NotFoundError:
            return False

        return True

    def extract_authorization(self, authorization: str) -> Optional[HTTPBasicCredentials]:
        scheme, _, param = authorization.partition(" ")
        if not authorization or scheme.lower() != "basic":
            return None

        try:
            data = base64.b64decode(param).decode("ascii")
        except (ValueError, UnicodeDecodeError, binascii.Error):
            logger.warning("Unable to base64 decode header", param=param)
            return None

        username, separator, password = data.partition(":")
        if not separator:
            logger.warning("No separator found", separator=separator)
            return None

        return HTTPBasicCredentials(username, password)
