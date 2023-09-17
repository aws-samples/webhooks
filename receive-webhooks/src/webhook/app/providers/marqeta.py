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

from typing import Optional, Literal

from aws_lambda_powertools import Logger

from app.providers.base import BaseProvider, HTTPBasicCredentials

__all__ = ["MarqetaProvider"]

logger = Logger(child=True)


# @see https://www.marqeta.com/docs/developer-guides/signature-verification
class MarqetaProvider(BaseProvider):
    SIGNATURE_HEADER = "X-Marqeta-Signature"
    SIGNATURE_ALGO = "sha1"

    @classmethod
    def get_provider_name(cls) -> Literal["marqeta"]:
        return "marqeta"

    def get_event_id(self) -> Optional[str]:
        return self._event.get_header_value("x-marqeta-request-trace-id")

    def verify(self) -> bool:
        authorization = self._event.get_header_value("Authorization")
        if not authorization:
            logger.warning(f"Authorization header not found")
            return False

        parameter = self.get_parameter()

        expected = HTTPBasicCredentials(
            parameter["basic_auth_user"], parameter["basic_auth_password"]
        )

        actual = self.extract_authorization(authorization)

        if expected != actual:
            logger.warning("Encoded values did not match", expected=expected, actual=actual)
            return False

        # Marqeta uses both an Authorization header and a signature header. After validating
        # the Authorization header, we need to verify the signature.
        return super().verify()
