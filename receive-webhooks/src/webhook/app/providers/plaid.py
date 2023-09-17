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
import hashlib
import time
from typing import Optional, Dict, Any, Literal

from aws_lambda_powertools import Logger
import requests
from jose import jwt

from app.providers.base import BaseProvider

logger = Logger(child=True)

__all__ = ["PlaidProvider"]

KEY_CACHE = {}


# @see https://plaid.com/docs/api/webhooks/webhook-verification/
class PlaidProvider(BaseProvider):
    SIGNATURE_HEADER = "plaid-verification"
    # Endpoint for getting public verification keys.
    ENDPOINT = "https://production.plaid.com/webhook_verification_key/get"

    @classmethod
    def get_provider_name(cls) -> Literal["plaid"]:
        return "plaid"

    def get_event_id(self) -> Optional[str]:
        data: Dict[str, Any] = self._event.json_body
        return data.get("item_id")

    def verify(self) -> bool:
        signed_jwt = self._event.get_header_value(self.SIGNATURE_HEADER)
        if not signed_jwt:
            logger.warning(f"Signature header {self.SIGNATURE_HEADER} not found")
            return False
        current_key_id = jwt.get_unverified_header(signed_jwt)["kid"]

        parameter = self.get_parameter()

        # If the key is not in the cache, update all non-expired keys.
        if current_key_id not in KEY_CACHE:
            keys_ids_to_update = [
                key_id for key_id, key in KEY_CACHE.items() if key["expired_at"] is None
            ]

            keys_ids_to_update.append(current_key_id)

            for key_id in keys_ids_to_update:
                r = requests.post(
                    self.ENDPOINT,
                    json={
                        "client_id": parameter["client_id"],
                        "secret": parameter["client_secret"],
                        "key_id": key_id,
                    },
                )

                # If this is the case, the key ID may be invalid.
                if r.status_code != 200:
                    continue

                response = r.json()
                key = response["key"]
                KEY_CACHE[key_id] = key

        # If the key ID is not in the cache, the key ID may be invalid.
        if current_key_id not in KEY_CACHE:
            return False

        # Fetch the current key from the cache.
        key = KEY_CACHE[current_key_id]

        # Reject expired keys.
        if key["expired_at"] is not None:
            return False

        # Validate the signature and extract the claims.
        try:
            claims = jwt.decode(signed_jwt, key, algorithms=["ES256"])
        except jwt.JWTError:
            return False

        # Ensure that the token is not expired.
        if claims["iat"] < time.time() - 5 * 60:
            return False

        body = self._event.decoded_body

        # Compute the hash of the body.
        m = hashlib.sha256()
        m.update(body.encode())
        body_hash = m.hexdigest()

        # Ensure that the hash of the body matches the claim.
        # Use constant time comparison to prevent timing attacks.
        return hmac.compare_digest(body_hash, claims["request_body_sha256"])
