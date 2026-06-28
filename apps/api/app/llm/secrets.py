from __future__ import annotations

import base64
import os
import secrets
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .settings import load_project_dotenv

_AAD = b"geo-provider-config:v1"


class ProviderSecretError(ValueError):
    pass


@dataclass(frozen=True)
class ProviderSecretSettings:
    master_key: bytes

    @classmethod
    def from_env(cls) -> "ProviderSecretSettings | None":
        dotenv = load_project_dotenv()
        raw_value = os.environ.get("GEO_PROVIDER_MASTER_KEY") or dotenv.get("GEO_PROVIDER_MASTER_KEY") or ""
        if not raw_value:
            return None
        key = _decode_base64_key(raw_value)
        if len(key) != 32:
            raise ProviderSecretError("GEO_PROVIDER_MASTER_KEY must decode to exactly 32 bytes")
        return cls(master_key=key)


class AesGcmSecretCipher:
    def __init__(self, master_key: bytes) -> None:
        self._aesgcm = AESGCM(master_key)

    def encrypt(self, plaintext: str) -> str:
        nonce = secrets.token_bytes(12)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), _AAD)
        return f"v1:{_encode_b64(nonce)}:{_encode_b64(ciphertext)}"

    def decrypt(self, token: str) -> str:
        version, nonce_b64, ciphertext_b64 = _split_token(token)
        if version != "v1":
            raise ProviderSecretError("unsupported provider secret token version")
        nonce = _decode_base64_key(nonce_b64)
        ciphertext = _decode_base64_key(ciphertext_b64)
        try:
            plaintext = self._aesgcm.decrypt(nonce, ciphertext, _AAD)
        except Exception as exc:  # pragma: no cover - AESGCM raises InvalidTag
            raise ProviderSecretError("provider secret decryption failed") from exc
        return plaintext.decode("utf-8")


def _split_token(token: str) -> tuple[str, str, str]:
    parts = token.split(":", 2)
    if len(parts) != 3:
        raise ProviderSecretError("invalid provider secret token format")
    return parts[0], parts[1], parts[2]


def _encode_b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode_base64_key(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode(value + padding)
    except Exception as exc:  # pragma: no cover - binascii.Error type is implementation detail
        raise ProviderSecretError("invalid base64 value") from exc
