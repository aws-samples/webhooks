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

from typing import Literal

from aws_lambda_powertools import Logger
from lithic import Lithic

from app.providers.base import BaseProvider

logger = Logger(child=True)

__all__ = ["LithicProvider"]


# @see https://docs.lithic.com/docs/events-api#example-code
class LithicProvider(BaseProvider):
    @classmethod
    def get_provider_name(cls) -> Literal["lithic"]:
        return "lithic"

    def get_event_id(self) -> str | None:
        return self._event.get_header_value("webhook-id")

    def verify(self) -> bool:
        payload = self._event.decoded_body

        parameter = self.get_parameter()
        secret: str = parameter["webhook_secret"]

        client = Lithic()
        try:
            client.webhooks.unwrap(payload, self._event.headers, secret)
        except Exception as error:
            logger.warning("Error verifying webhook signature", error)
            return False

        raise True
