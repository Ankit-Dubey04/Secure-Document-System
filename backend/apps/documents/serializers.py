from pathlib import PurePath

from django.core.files.base import ContentFile
from rest_framework import serializers

from apps.authentication.models import User

from .models import Document
from .services.crypto import encrypt_plaintext


ALLOWED_UPLOADS = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".odt": "application/vnd.oasis.opendocument.text",
}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024
CLASSIFICATION_RANK = {"PUBLIC": 0, "INTERNAL": 1, "CONFIDENTIAL": 2, "RESTRICTED": 3}


class DocumentSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    file = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = Document
        fields = ("id", "title", "description", "document_type", "classification", "owner", "file", "original_filename", "file_size", "content_type", "created_at", "updated_at", "updated_by")
        read_only_fields = ("id", "owner", "original_filename", "file_size", "content_type", "created_at", "updated_at", "updated_by")

    def get_owner(self, obj):
        return {"id": obj.owner_id, "name": obj.owner.name, "department": obj.owner.department}

    def get_updated_by(self, obj):
        if not obj.updated_by_id:
            return None
        return {"id": obj.updated_by_id, "name": obj.updated_by.name}

    def validate_file(self, upload):
        submitted_name = upload.name or ""
        if not submitted_name or "/" in submitted_name or "\\" in submitted_name:
            raise serializers.ValidationError("Filename must not contain a path.")
        safe_name = PurePath(submitted_name).name
        if safe_name != submitted_name or safe_name in {"", ".", ".."}:
            raise serializers.ValidationError("Invalid filename.")
        extension = PurePath(safe_name).suffix.lower()
        if extension not in ALLOWED_UPLOADS:
            raise serializers.ValidationError("Unsupported file extension.")
        if upload.content_type != ALLOWED_UPLOADS[extension]:
            raise serializers.ValidationError("File content type does not match the allowed extension.")
        if upload.size == 0:
            raise serializers.ValidationError("Empty files are not allowed.")
        if upload.size > MAX_UPLOAD_SIZE:
            raise serializers.ValidationError("File exceeds the 10 MiB upload limit.")
        return upload

    def validate(self, attrs):
        if self.instance is None and "file" not in attrs:
            raise serializers.ValidationError({"file": "An uploaded file is required."})
        classification = attrs.get("classification", getattr(self.instance, "classification", None))
        user = self.context["request"].user
        if not user.is_superuser and CLASSIFICATION_RANK[classification] > CLASSIFICATION_RANK[user.clearance_level]:
            raise serializers.ValidationError({"classification": "Classification exceeds your clearance level."})
        return attrs

    def create(self, validated_data):
        upload = validated_data.pop("file")
        plaintext = upload.read()
        encrypted = encrypt_plaintext(plaintext)
        validated_data.update(original_filename=PurePath(upload.name).name, file_size=len(plaintext), content_type=upload.content_type, plaintext_sha256=encrypted.plaintext_sha256, encryption_nonce=encrypted.nonce, is_encrypted=True)
        return super().create({**validated_data, "file": ContentFile(encrypted.ciphertext, name=upload.name)})

    def update(self, instance, validated_data):
        upload = validated_data.pop("file", None)
        if upload:
            plaintext = upload.read()
            encrypted = encrypt_plaintext(plaintext)
            validated_data.update(file=ContentFile(encrypted.ciphertext, name=upload.name), original_filename=PurePath(upload.name).name, file_size=len(plaintext), content_type=upload.content_type, plaintext_sha256=encrypted.plaintext_sha256, encryption_nonce=encrypted.nonce, is_encrypted=True, integrity_verified_at=None)
        return super().update(instance, validated_data)
