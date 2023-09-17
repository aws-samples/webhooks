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

import os
from typing import TYPE_CHECKING, Dict, Any, Optional, List

from aws_lambda_powertools import Logger
import boto3
import botocore
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBClient

from app import constants, exceptions

__all__ = ["DynamoDB"]

logger = Logger(child=True)
TABLE_NAME = os.getenv(constants.ENV_TABLE_NAME)


class DynamoDB:
    _deserializer = TypeDeserializer()
    _serializer = TypeSerializer()

    def __init__(self, session: boto3.Session) -> None:
        self._client: "DynamoDBClient" = session.client("dynamodb", config=constants.BOTO3_CONFIG)

    def put_item(self, item: Dict[str, Any]) -> None:
        params = {
            "TableName": TABLE_NAME,
            "Item": self.serialize(item),
        }

        logger.debug("put_item", params=params)
        try:
            self._client.put_item(**params)
        except botocore.exceptions.ClientError as error:
            logger.exception("Unable to put item", error)
            raise exceptions.DynamoDBWriteError("Unable to put item")

    def get_item(
        self, key: Dict[str, Any], attributes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        params = {
            "TableName": TABLE_NAME,
            "Key": self.serialize(key),
        }
        if attributes:
            params["ExpressionAttributeNames"] = {}
            placeholders: List[str] = []
            for idx, attribute in enumerate(attributes):
                placeholder = f"#a{idx}"
                params["ExpressionAttributeNames"][placeholder] = attribute
                placeholders.append(placeholder)
            params["ProjectionExpression"] = ",".join(placeholders)

        logger.debug("get_item", params=params)

        try:
            response = self._client.get_item(**params)
        except botocore.exceptions.ClientError as error:
            logger.exception("Unable to get item", error)
            raise exceptions.DynamoDBReadError("Unable to get item")

        item: Dict[str, Any] = response.get("Item", {})
        if not item:
            raise exceptions.NotFoundError("Item not found")

        return self.deserialize(item)

    @classmethod
    def deserialize(cls, item: Any) -> Any:
        if not item:
            return item

        if isinstance(item, dict) and "M" not in item:
            item = {"M": item}

        return cls._deserializer.deserialize(item)

    @classmethod
    def serialize(cls, obj: Any) -> Dict[str, Any]:
        result = cls._serializer.serialize(obj)
        if "M" in result:
            result: Dict[str, Any] = result["M"]
        return result
