# Webhooks on AWS: Innovate with event notifications

This repository is intended for developers looking to send or receive webhooks using AWS. It contains code samples for the reference architectures outlined on [Sending and receiving webhooks on AWS: Innovate with event notifications](https://aws.amazon.com/blogs/compute/sending-and-receiving-webhooks-on-aws-innovate-with-event-notifications/). This includes:

* [send-webhooks/](/send-webhooks/): An application that delivers webhooks to an external endpoint.
* [receive-webhooks/](/receive-webhooks/): An API that receives webhooks with capacity to handle large payloads.

If you have any comments, suggestions or feedback, we'd love to [hear from you](https://github.com/aws-samples/webhooks/issues/new).

## Architecture: Send Webhooks

![An architecture to send webhooks using Amazon EventBridge Pipes](/send-webhooks/images/architecture-send-webhooks.png)

## Architecture: Receive Webhooks

![An architecture to receive webhooks using the claim-check pattern](/receive-webhooks/images/architecture-receive-webhooks.png)

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

