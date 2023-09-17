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

from typing import Optional, Dict, Any, Literal

from aws_lambda_powertools import Logger
import stripe

from app.providers.base import BaseProvider

logger = Logger(child=True)

__all__ = ["StripeProvider"]


# @see https://stripe.com/docs/webhooks#verify-official-libraries
class StripeProvider(BaseProvider):
    SIGNATURE_HEADER = "Stripe-Signature"
    SIGNATURE_ALGO = "sha256"

    @classmethod
    def get_provider_name(cls) -> Literal["stripe"]:
        return "stripe"

    def get_event_id(self) -> Optional[str]:
        data: Dict[str, Any] = self._event.json_body
        return data.get("id")

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
        secret = parameter["webhook_secret"]

        try:
            stripe.Webhook.construct_event(payload, signature, secret)
        except ValueError as error:
            logger.warning("Invalid payload", error)
            return False
        except stripe.error.SignatureVerificationError as error:
            logger.warning("Error verifying webhook signature", error)
            return False

        return True
