from __future__ import annotations

import json
from pathlib import Path


OPENAPI = Path("openapi.json")


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"expected exactly one match, found {text.count(old)}: {old[:80]!r}")
    return text.replace(old, new, 1)


def replace_between(text: str, start: str, end: str, replacement: str) -> str:
    start_index = text.index(start)
    end_index = text.index(end, start_index)
    return text[:start_index] + replacement + text[end_index:]


text = OPENAPI.read_text()

# Domain PATCH route.
domain_path = text.index('    "/domains/{domain_id}": {')
domain_delete = text.index('      "delete": {', domain_path)
domain_patch = '''      "patch": {
        "operationId": "updateDomain",
        "summary": "Update Domain",
        "description": "Updates mutable configuration for a sending domain. Currently only the TLS mode can be changed.",
        "tags": ["Domains"],
        "parameters": [
          { "$ref": "#/components/parameters/DomainId" },
          { "$ref": "#/components/parameters/IdempotencyKey" }
        ],
        "requestBody": {
          "required": true,
          "content": { "application/json": { "schema": { "$ref": "#/components/schemas/DomainUpdateRequest" } } }
        },
        "responses": {
          "200": {
            "description": "Domain updated successfully.",
            "content": { "application/json": { "schema": { "$ref": "#/components/schemas/DomainEnvelope" } } }
          },
          "default": { "$ref": "#/components/responses/Error" }
        }
      },
'''
text = text[:domain_delete] + domain_patch + text[domain_delete:]

# Domain PATCH request schema. Empty objects are valid no-op updates in the current service.
domain_schema_marker = '      "SenderDomain": {'
domain_update_schema = '''      "DomainUpdateRequest": {
        "type": "object",
        "properties": {
          "tls": { "type": "string", "enum": ["opportunistic", "enforced"] }
        },
        "additionalProperties": false
      },
'''
text = text.replace(domain_schema_marker, domain_update_schema + domain_schema_marker, 1)

# Broadcast route descriptions and create example.
text = replace_once(
    text,
    '"description": "Creates a draft broadcast for a segment using a message template."',
    '"description": "Creates a broadcast with its own sender and email content. By default the broadcast is a draft; set send to true to queue immediately or combine send with a future scheduled_at to schedule it."',
)
text = replace_once(
    text,
    '''              "example": {
                "name": "August product update",
                "segment_id": "49a3999c-0ce1-4ea6-ab68-afcd6dc2e794",
                "template": "product-update"
              }''',
    '''              "example": {
                "name": "August product update",
                "segment_id": "49a3999c-0ce1-4ea6-ab68-afcd6dc2e794",
                "from_email": "hello@example.com",
                "from_name": "Dugble",
                "subject": "What's new this month",
                "preview_text": "A quick look at what shipped.",
                "html": "<p>Hello {{{FIRST_NAME}}}</p>",
                "text": "Hello {{{FIRST_NAME}}}",
                "variable_bindings": { "FIRST_NAME": "there" }
              }''',
)
text = replace_once(
    text,
    '"description": "Updates a draft broadcast. Supply the current revision for optimistic concurrency control."',
    '"description": "Updates a draft or scheduled broadcast. Supply the current revision for optimistic concurrency control; nullable content fields can be cleared with JSON null."',
)
text = replace_once(
    text,
    '"description": "Cancels a broadcast that is currently scheduled for future delivery."',
    '"description": "Cancels active scheduling or execution. Scheduled broadcasts return to draft; queued broadcasts move to canceled and remaining fanout stops."',
)
text = replace_once(
    text,
    '"description": "Creates a new draft broadcast using the configuration of an existing broadcast."',
    '"description": "Creates a new draft by copying the source broadcast audience and exact owned message content."',
)
text = replace_once(
    text,
    '"description": "Renders the broadcast template with optional preview variables without sending it."',
    '"description": "Renders the broadcast-owned subject and body with optional preview variables without sending it."',
)

# Broadcast request schemas.
create_schema = '''      "BroadcastCreateRequest": {
        "type": "object",
        "required": ["segment_id", "subject", "html"],
        "properties": {
          "name": { "type": "string" },
          "segment_id": { "type": "string", "format": "uuid" },
          "topic_id": { "type": ["string", "null"], "format": "uuid" },
          "from_email": { "type": ["string", "null"], "format": "email" },
          "from_name": { "type": ["string", "null"] },
          "reply_to_email": { "type": ["string", "null"], "format": "email" },
          "subject": { "type": "string" },
          "preview_text": { "type": ["string", "null"] },
          "html": { "type": "string" },
          "text": { "type": ["string", "null"] },
          "variable_bindings": { "type": "object", "additionalProperties": true },
          "send": { "type": "boolean", "default": false },
          "scheduled_at": { "type": ["string", "null"], "format": "date-time", "description": "When send is true, a future timestamp schedules delivery instead of queueing immediately." }
        }
      },
'''
text = replace_between(text, '      "BroadcastCreateRequest": {', '      "BroadcastUpdateRequest": {', create_schema)

update_schema = '''      "BroadcastUpdateRequest": {
        "type": "object",
        "required": ["revision"],
        "properties": {
          "revision": { "type": "integer", "format": "int64", "minimum": 1 },
          "name": { "type": "string" },
          "segment_id": { "type": "string", "format": "uuid" },
          "topic_id": { "type": ["string", "null"], "format": "uuid" },
          "from_email": { "type": ["string", "null"], "format": "email" },
          "from_name": { "type": ["string", "null"] },
          "reply_to_email": { "type": ["string", "null"], "format": "email" },
          "subject": { "type": "string" },
          "preview_text": { "type": ["string", "null"] },
          "html": { "type": "string" },
          "text": { "type": ["string", "null"] },
          "variable_bindings": { "type": ["object", "null"], "additionalProperties": true }
        }
      },
'''
text = replace_between(text, '      "BroadcastUpdateRequest": {', '      "BroadcastSendRequest": {', update_schema)
text = replace_once(
    text,
    '      "BroadcastDuplicateRequest": { "type": "object", "required": ["name"], "properties": { "name": { "type": "string", "minLength": 1 } } },',
    '      "BroadcastDuplicateRequest": { "type": "object", "properties": { "name": { "type": "string" } } },',
)

resource_schema = '''      "BroadcastResource": {
        "type": "object",
        "required": ["id", "team_id", "name", "status", "segment_id", "from_email", "subject", "html", "variable_bindings", "audience_count", "eligible_count", "suppressed_count", "queued_count", "failed_count", "revision", "created_at", "updated_at"],
        "properties": {
          "id": { "type": "string", "format": "uuid" },
          "team_id": { "type": "string", "format": "uuid" },
          "name": { "type": "string" },
          "status": { "type": "string", "enum": ["draft", "scheduled", "queued", "sent", "failed", "canceled"] },
          "segment_id": { "type": "string", "format": "uuid" },
          "topic_id": { "type": "string", "format": "uuid" },
          "from_email": { "type": "string", "format": "email" },
          "from_name": { "type": "string" },
          "reply_to_email": { "type": "string", "format": "email" },
          "subject": { "type": "string" },
          "preview_text": { "type": "string" },
          "html": { "type": "string" },
          "text": { "type": "string" },
          "variable_bindings": { "type": "object", "additionalProperties": true },
          "scheduled_at": { "type": "string", "format": "date-time" },
          "queued_at": { "type": "string", "format": "date-time" },
          "sent_at": { "type": "string", "format": "date-time" },
          "canceled_at": { "type": "string", "format": "date-time" },
          "audience_count": { "type": "integer", "format": "int64" },
          "eligible_count": { "type": "integer", "format": "int64" },
          "suppressed_count": { "type": "integer", "format": "int64" },
          "queued_count": { "type": "integer", "format": "int64" },
          "failed_count": { "type": "integer", "format": "int64" },
          "revision": { "type": "integer", "format": "int64", "minimum": 1 },
          "created_at": { "type": "string", "format": "date-time" },
          "updated_at": { "type": "string", "format": "date-time" }
        }
      },
'''
text = replace_between(text, '      "BroadcastResource": {', '      "BroadcastRecipient": {', resource_schema)

preview_schema = '''      "BroadcastPreview": {
        "type": "object",
        "required": ["from_email", "subject", "html"],
        "properties": {
          "from_email": { "type": "string", "format": "email" },
          "from_name": { "type": "string" },
          "reply_to_email": { "type": "string", "format": "email" },
          "subject": { "type": "string" },
          "preview_text": { "type": "string" },
          "html": { "type": "string" },
          "text": { "type": "string" }
        }
      },
'''
text = replace_between(text, '      "BroadcastPreview": {', '      "BroadcastEnvelope": {', preview_schema)

# Ensure the transformation leaves a valid OpenAPI JSON document and removes the obsolete broadcast template contract.
spec = json.loads(text)
assert "patch" in spec["paths"]["/domains/{domain_id}"]
assert "DomainUpdateRequest" in spec["components"]["schemas"]
broadcast = spec["components"]["schemas"]["BroadcastResource"]["properties"]
assert "template_id" not in broadcast and "template_version_id" not in broadcast
assert {"from_email", "subject", "html"}.issubset(broadcast)
assert "template" not in spec["components"]["schemas"]["BroadcastCreateRequest"]["properties"]
assert "template_id" not in spec["components"]["schemas"]["BroadcastPreview"]["properties"]

OPENAPI.write_text(text)
