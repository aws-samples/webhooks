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

import hmac
from typing import Optional, Literal

from aws_lambda_powertools import Logger

from app.providers.base import BaseProvider

__all__ = ["TrolleyProvider"]

logger = Logger(child=True)


# @see https://docs.trolley.com/api/#webhooks-verify
class TrolleyProvider(BaseProvider):
    SIGNATURE_HEADER = "X-PaymentRails-Signature"
    SIGNATURE_ALGO = "sha256"

    @classmethod
    def get_provider_name(cls) -> Literal["trolley"]:
        return "trolley"

    def get_event_id(self) -> Optional[str]:
        return self._event.get_header_value("X-PaymentRails-Delivery")

    def verify(self) -> bool:
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

        sig_values = signature.split(",")
        timestamp = sig_values[0].split("=")[1]
        v1 = sig_values[1].split("=")[1]

        computed_signature = hmac.new(key, timestamp + payload, self.SIGNATURE_ALGO).hexdigest()

        if not hmac.compare_digest(v1, computed_signature):
            logger.warning(
                "Computed signature did not match provided signature",
                signature=v1,
                computed_signature=computed_signature,
            )
            return False

        return True
