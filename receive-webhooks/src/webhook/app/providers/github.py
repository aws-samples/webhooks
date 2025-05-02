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

__all__ = ["GithubProvider"]

from typing import Literal, Optional

from app.providers import BaseProvider


class GithubProvider(BaseProvider):
    SIGNATURE_HEADER = "X-Hub-Signature-256"
    SIGNATURE_ALGO = "sha256"

    @classmethod
    def get_provider_name(cls) -> Literal["github"]:
        return "github"

    def get_event_id(self) -> Optional[str]:
        return self._event.headers.get("X-GitHub-Delivery")

    def parse_signature(self, signature: Optional[str]) -> Optional[str]:
        if signature and signature.startswith("sha256="):
            signature = signature[7:]
        return signature
