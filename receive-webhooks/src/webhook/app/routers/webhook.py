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

from datetime import datetime, timezone, timedelta
import math

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler.api_gateway import Router, Response
from aws_lambda_powertools.event_handler.exceptions import InternalServerError, BadRequestError
import boto3

from app import providers, exceptions, constants, resources

__all__ = ["router"]

logger = Logger(child=True)
tracer = Tracer()
router = Router()

session = boto3._get_default_session()
s3 = resources.S3(session)
dynamodb = resources.DynamoDB(session)


@tracer.capture_method(capture_response=False)
@router.post("/<provider>")
def post_webhook(provider: str) -> Response:
    event = router.current_event
    if not event.body:
        logger.warning("No payload found in request")
        raise BadRequestError("No payload found in request")

    provider_class = providers.PROVIDER_MAP.get(provider)
    if not provider_class:
        logger.warning(f"Unknown provider: {provider}")
        raise BadRequestError(
            f"Unknown provider: {provider} (only {providers.PROVIDER_MAP.keys()} are supported)"
        )

    prov: providers.BaseProvider = provider_class(event)
    logger.debug(f"Using provider: {prov.get_provider_name()}")

    event_id = prov.get_event_id()
    if prov.is_duplicate(event_id):
        logger.warning("Duplicate webhook request, replying with 200", event_id=event_id)
        return Response(200)

    now = datetime.now(tz=timezone.utc).replace(microsecond=0)
    expires_at = now + timedelta(days=constants.EXPIRES_IN_DAYS)
    arrived_at = now.isoformat().replace("+00:00", "Z")
    if not event_id:
        # if there is no unique event ID, use the arrival time
        event_id = arrived_at

    key = f"raw/{provider}/evt_{event_id}.json"
    metadata = {
        "event_id": str(event_id),
        "arrived_at": str(arrived_at),
        "provider": provider,
        "expires_at": str(math.floor(expires_at.timestamp())),
    }
    try:
        obj = s3.put_object(key, event.decoded_body, metadata)
    except exceptions.S3PutError:
        raise InternalServerError("Failed to store request payload")

    item = {
        constants.PARTITION_KEY: provider.upper(),
        constants.SORT_KEY: event_id,
        "arrived_at": arrived_at,
        "provider": provider,
        "s3": {
            "bucket": obj.bucket,
            "key": obj.key,
            "version_id": obj.version_id,
        },
        "gsi1pk": "PENDING",
        "gsi1sk": arrived_at,
        "expires_at": math.floor(expires_at.timestamp()),
    }
    try:
        dynamodb.put_item(item)
    except exceptions.DynamoDBWriteError:
        # Remove previously uploaded S3 object
        try:
            s3.delete_object(obj.key, obj.version_id)
        except exceptions.S3DeleteError:
            pass
        raise InternalServerError("Failed to store request metadata")

    return Response(200)
