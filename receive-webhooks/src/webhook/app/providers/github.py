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
