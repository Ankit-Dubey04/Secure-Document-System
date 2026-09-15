from rest_framework import serializers
from .models import AuditLog
class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ("id","timestamp","user","event_type","outcome","resource_type","resource_id","source_ip","user_agent","metadata","previous_hash","current_hash")
        read_only_fields = fields
