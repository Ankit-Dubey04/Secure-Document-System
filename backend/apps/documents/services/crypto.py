"""AES-256-GCM encryption and plaintext integrity helpers."""

import base64
import hashlib
import hmac
import os
from dataclasses import dataclass

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings


class EncryptionConfigurationError(Exception):
    pass


class DocumentDecryptionError(Exception):
    pass


class DocumentIntegrityError(Exception):
    pass


@dataclass(frozen=True)
class EncryptedDocument:
    ciphertext: bytes
    nonce: bytes
    plaintext_sha256: str


def get_encryption_key():
    encoded_key = settings.DOCUMENT_ENCRYPTION_KEY
    if not encoded_key:
        raise EncryptionConfigurationError("Document encryption is not configured.")
    try:
        key = base64.urlsafe_b64decode(encoded_key.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise EncryptionConfigurationError("Document encryption is not configured.") from exc
    if len(key) != 32:
        raise EncryptionConfigurationError("Document encryption is not configured.")
    return key


def encrypt_plaintext(plaintext):
    nonce = os.urandom(12)
    digest = hashlib.sha256(plaintext).hexdigest()
    ciphertext = AESGCM(get_encryption_key()).encrypt(nonce, plaintext, None)
    return EncryptedDocument(ciphertext=ciphertext, nonce=nonce, plaintext_sha256=digest)


def decrypt_and_verify(ciphertext, nonce, expected_sha256):
    try:
        plaintext = AESGCM(get_encryption_key()).decrypt(bytes(nonce), ciphertext, None)
    except InvalidTag as exc:
        raise DocumentDecryptionError("Document cannot be decrypted.") from exc
    calculated_sha256 = hashlib.sha256(plaintext).hexdigest()
    if not hmac.compare_digest(calculated_sha256, expected_sha256):
        raise DocumentIntegrityError("Document integrity verification failed.")
    return plaintext
