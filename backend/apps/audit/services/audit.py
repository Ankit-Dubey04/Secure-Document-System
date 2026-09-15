import hashlib, json
from django.db import IntegrityError, transaction
from django.utils import timezone
from ..models import AuditChainState, AuditLog

GENESIS_HASH = "GENESIS"
SECRET_KEYS = {"password", "token", "authorization", "cookie", "key", "secret", "refresh"}

def sanitize_metadata(value):
    if isinstance(value, dict): return {str(k): sanitize_metadata(v) for k, v in value.items() if not any(term in str(k).lower() for term in SECRET_KEYS)}
    if isinstance(value, (list, tuple)): return [sanitize_metadata(v) for v in value]
    return value if isinstance(value, (str, int, float, bool, type(None))) else str(value)

def canonical_event_data(event):
    return json.dumps({"id": str(event.id), "timestamp": event.timestamp.isoformat(), "user_id": str(event.user_id or ""), "event_type": event.event_type, "outcome": event.outcome, "resource_type": event.resource_type, "resource_id": event.resource_id, "source_ip": event.source_ip or "", "user_agent": event.user_agent, "metadata": event.metadata, "previous_hash": event.previous_hash}, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

def event_hash(event): return hashlib.sha256(canonical_event_data(event).encode("utf-8")).hexdigest()

def request_context(request):
    if not request: return {}
    return {"source_ip": request.META.get("REMOTE_ADDR"), "user_agent": request.META.get("HTTP_USER_AGENT", "")[:512]}

def record_event(event_type, outcome, user=None, resource_type="", resource_id="", metadata=None, request=None):
    context = request_context(request)
    with transaction.atomic():
        # The inner savepoint keeps the outer transaction usable if another
        # request wins the first-row creation race.
        try:
            state = AuditChainState.objects.select_for_update().get(pk=1)
        except AuditChainState.DoesNotExist:
            try:
                with transaction.atomic():
                    AuditChainState.objects.create(pk=1)
            except IntegrityError:
                pass
            state = AuditChainState.objects.select_for_update().get(pk=1)
        event = AuditLog(id=__import__("uuid").uuid4(), timestamp=timezone.now(), user=user if getattr(user, "is_authenticated", False) else None, event_type=event_type, outcome=outcome, resource_type=resource_type, resource_id=str(resource_id or ""), source_ip=context.get("source_ip"), user_agent=context.get("user_agent", ""), metadata=sanitize_metadata(metadata or {}), previous_hash=state.last_hash)
        event.current_hash = event_hash(event); event.save(force_insert=True)
        state.last_hash = event.current_hash; state.save(update_fields=("last_hash",))
        return event

def verify_chain():
    previous = GENESIS_HASH; checked = 0
    for event in AuditLog.objects.order_by("timestamp", "id"):
        checked += 1
        if event.previous_hash != previous: return {"valid": False, "checked_events": checked, "first_invalid_event": str(event.id), "reason": "previous_hash_mismatch"}
        if event.current_hash != event_hash(event): return {"valid": False, "checked_events": checked, "first_invalid_event": str(event.id), "reason": "current_hash_mismatch"}
        previous = event.current_hash
    state = AuditChainState.objects.filter(pk=1).first()
    if state and state.last_hash != previous: return {"valid": False, "checked_events": checked, "first_invalid_event": None, "reason": "chain_state_mismatch"}
    return {"valid": True, "checked_events": checked, "first_invalid_event": None, "reason": None}
