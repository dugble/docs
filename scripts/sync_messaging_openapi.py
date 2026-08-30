from __future__ import annotations

import json
from pathlib import Path

OPENAPI = Path("openapi.json")
text = OPENAPI.read_text()


def replace_once(old: str, new: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected exactly one match, found {count}: {old[:120]!r}")
    text = text.replace(old, new, 1)


# Email analytics route.
email_marker = '    "/emails/{message_id}": {'
email_analytics = r'''    "/emails/analytics": {
      "get": {
        "operationId": "getEmailAnalytics",
        "summary": "Get Email Analytics",
        "description": "Returns team-wide email delivery, open, click, and bounce analytics for fixed 7-day, 30-day, and 90-day windows.",
        "tags": ["Email"],
        "responses": {
          "200": {
            "description": "Email analytics retrieved successfully.",
            "content": { "application/json": { "schema": { "$ref": "#/components/schemas/EmailAnalyticsEnvelope" } } }
          },
          "default": { "$ref": "#/components/responses/Error" }
        }
      }
    },
'''
replace_once(email_marker, email_analytics + email_marker)

# SMS analytics route.
sms_marker = '    "/sms/{message_id}": {'
sms_analytics = r'''    "/sms/analytics": {
      "get": {
        "operationId": "getSmsAnalytics",
        "summary": "Get SMS Analytics",
        "description": "Returns team-wide SMS delivery analytics for fixed 7-day, 30-day, and 90-day windows plus 90-day delivery totals by destination country.",
        "tags": ["SMS"],
        "responses": {
          "200": {
            "description": "SMS analytics retrieved successfully.",
            "content": { "application/json": { "schema": { "$ref": "#/components/schemas/SmsAnalyticsEnvelope" } } }
          },
          "default": { "$ref": "#/components/responses/Error" }
        }
      }
    },
'''
replace_once(sms_marker, sms_analytics + sms_marker)

# Email event pagination supports limit + offset, with event-specific default 100.
replace_once(
'''        "parameters": [
          { "$ref": "#/components/parameters/MessageId" },
          { "$ref": "#/components/parameters/LimitOffset" }
        ],
        "responses": {
          "200": {
            "description": "Email events retrieved successfully.",''',
'''        "parameters": [
          { "$ref": "#/components/parameters/MessageId" },
          { "$ref": "#/components/parameters/EventLimit" },
          { "$ref": "#/components/parameters/Offset" }
        ],
        "responses": {
          "200": {
            "description": "Email events retrieved successfully.",''',
)

# SMS events support limit only, defaulting to 100.
replace_once(
'''        "parameters": [
          { "$ref": "#/components/parameters/MessageId" },
          { "$ref": "#/components/parameters/LimitOffset" }
        ],
        "responses": {
          "200": {
            "description": "SMS events retrieved successfully.",''',
'''        "parameters": [
          { "$ref": "#/components/parameters/MessageId" },
          { "$ref": "#/components/parameters/EventLimit" }
        ],
        "responses": {
          "200": {
            "description": "SMS events retrieved successfully.",''',
)

# SMS list filters.
replace_once(
'''        "parameters": [
          { "$ref": "#/components/parameters/LimitOffset" },
          { "$ref": "#/components/parameters/Offset" }
        ],
        "responses": {
          "200": {
            "description": "SMS messages retrieved successfully.",''',
'''        "parameters": [
          { "$ref": "#/components/parameters/LimitOffset" },
          { "$ref": "#/components/parameters/Offset" },
          {
            "name": "status",
            "in": "query",
            "required": false,
            "description": "Filter by exact normalized SMS status.",
            "schema": { "type": "string", "enum": ["queued", "processing", "submitted", "sent", "delivered", "undelivered", "rejected", "failed", "expired", "unknown", "canceled"] }
          },
          {
            "name": "sender",
            "in": "query",
            "required": false,
            "description": "Filter by exact sender identity matching the response `from` value.",
            "schema": { "type": "string" }
          },
          {
            "name": "start_date",
            "in": "query",
            "required": false,
            "description": "Include messages created at or after this RFC 3339 timestamp.",
            "schema": { "type": "string", "format": "date-time" }
          },
          {
            "name": "end_date",
            "in": "query",
            "required": false,
            "description": "Include messages created at or before this RFC 3339 timestamp. Must not precede start_date.",
            "schema": { "type": "string", "format": "date-time" }
          },
          {
            "name": "search",
            "in": "query",
            "required": false,
            "description": "Case-insensitive partial match across recipient, sender, body, or provider message ID.",
            "schema": { "type": "string" }
          }
        ],
        "responses": {
          "200": {
            "description": "SMS messages retrieved successfully.",''',
)

# Scheduling route descriptions and dedicated update schemas.
replace_once(
'        "description": "Changes the delivery time of an email that is still queued for scheduled delivery.",',
'        "description": "Reschedules a pending scheduled email. The new scheduled_at value must be a future RFC 3339 timestamp.",',
)
replace_once(
'          "content": { "application/json": { "schema": { "$ref": "#/components/schemas/ScheduleUpdateRequest" } } }\n        },\n        "responses": {\n          "200": {\n            "description": "Email schedule updated successfully.",',
'          "content": { "application/json": { "schema": { "$ref": "#/components/schemas/EmailScheduleUpdateRequest" } } }\n        },\n        "responses": {\n          "200": {\n            "description": "Email schedule updated successfully.",',
)
replace_once(
'        "description": "Changes the delivery time of an SMS that is still queued for scheduled delivery.",',
'        "description": "Reschedules a pending scheduled SMS outside the delivery cutoff. The new scheduled_at value must be a future RFC 3339 timestamp at least 30 seconds ahead.",',
)
replace_once(
'          "content": { "application/json": { "schema": { "$ref": "#/components/schemas/ScheduleUpdateRequest" } } }\n        },\n        "responses": {\n          "200": {\n            "description": "SMS schedule updated successfully.",',
'          "content": { "application/json": { "schema": { "$ref": "#/components/schemas/SmsScheduleUpdateRequest" } } }\n        },\n        "responses": {\n          "200": {\n            "description": "SMS schedule updated successfully.",',
)
replace_once(
'        "description": "Cancels an SMS that is still queued for scheduled delivery.",',
'        "description": "Cancels a pending scheduled SMS outside the final 15-second delivery cutoff.",',
)

# Batch limits and descriptions are 50, not 100.
replace_once(
'        "description": "Atomically queues up to 100 emails. Attachments are not supported in batch requests. A top-level array is preferred; an object containing a `messages` array is also accepted.",',
'        "description": "Atomically queues up to 50 emails. Attachments are not supported in batch requests. A top-level array is preferred; an object containing a `messages` array is also accepted.",',
)
replace_once(
'        "description": "Atomically validates, prices, charges, and queues up to 100 SMS messages. A top-level array is preferred; an object containing a `messages` array is also accepted.",',
'        "description": "Atomically validates, prices, charges, and queues up to 50 SMS messages. A top-level array is preferred; an object containing a `messages` array is also accepted.",',
)

# Event-specific limit parameter.
replace_once(
'''      "Offset": {
        "name": "offset",
        "in": "query",
        "required": false,
        "description": "Number of records to skip.",
        "schema": { "type": "integer", "format": "int32", "minimum": 0 }
      },
''',
'''      "Offset": {
        "name": "offset",
        "in": "query",
        "required": false,
        "description": "Number of records to skip.",
        "schema": { "type": "integer", "format": "int32", "minimum": 0 }
      },
      "EventLimit": {
        "name": "limit",
        "in": "query",
        "required": false,
        "description": "Maximum number of message events to return. Defaults to 100; values above 100 use the default.",
        "schema": { "type": "integer", "format": "int32", "minimum": 1, "maximum": 100, "default": 100 }
      },
''',
)

# Email request fixes: from is optional, single-send attachment paths are unsupported, batch max 50.
replace_once(
'        "required": ["from", "to", "subject"],',
'        "required": ["to", "subject"],',
)
replace_once(
'''          "from": {
            "$ref": "#/components/schemas/EmailAddress",
            "default": "Acme <onboarding@dugble.me>"
          },''',
'''          "from": {
            "$ref": "#/components/schemas/EmailAddress",
            "description": "Optional sender override. When omitted, Dugble resolves the configured default sender."
          },''',
)
replace_once(
'          "path": { "type": "string", "format": "uri" },\n',
'',
)
replace_once(
'''      "EmailBatchArray": {
        "type": "array",
        "minItems": 1,
        "maxItems": 100,''',
'''      "EmailBatchArray": {
        "type": "array",
        "minItems": 1,
        "maxItems": 50,''',
)

# Replace the shared scheduling schema with channel-specific mutation schemas.
replace_once(
'''      "ScheduleUpdateRequest": {
        "type": "object",
        "required": ["scheduled_at"],
        "properties": { "scheduled_at": { "type": "string" } }
      },''',
'''      "EmailScheduleUpdateRequest": {
        "type": "object",
        "required": ["scheduled_at"],
        "properties": {
          "scheduled_at": { "type": "string", "format": "date-time", "description": "Future RFC 3339 timestamp. Relative scheduling values are not accepted when rescheduling." }
        },
        "additionalProperties": false
      },
      "SmsScheduleUpdateRequest": {
        "type": "object",
        "required": ["scheduled_at"],
        "properties": {
          "scheduled_at": { "type": "string", "format": "date-time", "description": "Future RFC 3339 timestamp at least 30 seconds ahead. Relative values are not accepted." }
        },
        "additionalProperties": false
      },''',
)

# Email analytics schemas.
replace_once(
'''      "EmailListEnvelope": {
        "type": "object",
        "required": ["success", "data"],
        "properties": { "success": { "type": "boolean", "enum": [true] }, "data": { "type": "array", "items": { "$ref": "#/components/schemas/EmailSummary" } } }
      },''',
'''      "EmailListEnvelope": {
        "type": "object",
        "required": ["success", "data"],
        "properties": { "success": { "type": "boolean", "enum": [true] }, "data": { "type": "array", "items": { "$ref": "#/components/schemas/EmailSummary" } } }
      },
      "EmailAnalyticsRate": {
        "type": "object",
        "required": ["name", "value"],
        "properties": {
          "name": { "type": "string", "enum": ["delivery_rate", "open_rate", "click_rate", "bounce_rate"] },
          "value": { "type": "number", "format": "double", "minimum": 0 }
        }
      },
      "EmailAnalyticsPoint": {
        "type": "object",
        "required": ["date", "total", "delivered", "opened", "clicked", "bounced"],
        "properties": {
          "date": { "type": "string", "format": "date" },
          "total": { "type": "integer", "format": "int64", "minimum": 0 },
          "delivered": { "type": "integer", "format": "int64", "minimum": 0 },
          "opened": { "type": "integer", "format": "int64", "minimum": 0 },
          "clicked": { "type": "integer", "format": "int64", "minimum": 0 },
          "bounced": { "type": "integer", "format": "int64", "minimum": 0 }
        }
      },
      "EmailAnalyticsWindow": {
        "type": "object",
        "required": ["days", "rates", "series"],
        "properties": {
          "days": { "type": "integer", "format": "int32", "enum": [7, 30, 90] },
          "rates": { "type": "array", "items": { "$ref": "#/components/schemas/EmailAnalyticsRate" } },
          "series": { "type": "array", "items": { "$ref": "#/components/schemas/EmailAnalyticsPoint" } }
        }
      },
      "EmailAnalytics": {
        "type": "object",
        "required": ["object", "windows"],
        "properties": {
          "object": { "type": "string", "enum": ["email.analytics"] },
          "windows": { "type": "array", "items": { "$ref": "#/components/schemas/EmailAnalyticsWindow" } }
        }
      },
      "EmailAnalyticsEnvelope": {
        "type": "object",
        "required": ["success", "data"],
        "properties": {
          "success": { "type": "boolean", "enum": [true] },
          "data": { "$ref": "#/components/schemas/EmailAnalytics" }
        }
      },''',
)

# SMS request validation and batch max 50.
replace_once(
'''          "to": { "type": "string", "example": "+233201234567" },
          "from": { "type": "string", "example": "Dugble" },
          "body": { "type": "string" },
          "metadata": { "type": "object", "additionalProperties": true },
          "scheduled_at": { "type": "string" }''',
'''          "to": { "type": "string", "pattern": "^\\+[1-9]\\d{7,14}$", "example": "+233201234567", "description": "Supported E.164 destination number." },
          "from": { "type": "string", "minLength": 1, "maxLength": 11, "example": "Dugble", "description": "Approved sender ID." },
          "body": { "type": "string", "minLength": 1, "maxLength": 1600 },
          "metadata": { "type": "object", "additionalProperties": true },
          "scheduled_at": { "type": "string", "description": "Future RFC 3339 timestamp or supported relative value such as 'in 5 min'. The resolved time must be at least 30 seconds ahead." }''',
)
replace_once(
'''      "SmsBatchArray": {
        "type": "array",
        "minItems": 1,
        "maxItems": 100,''',
'''      "SmsBatchArray": {
        "type": "array",
        "minItems": 1,
        "maxItems": 50,''',
)

# SMS analytics schemas.
replace_once(
'''      "SmsListEnvelope": {
        "type": "object",
        "required": ["success", "data"],
        "properties": { "success": { "type": "boolean", "enum": [true] }, "data": { "type": "array", "items": { "$ref": "#/components/schemas/SmsResource" } } }
      },''',
'''      "SmsListEnvelope": {
        "type": "object",
        "required": ["success", "data"],
        "properties": { "success": { "type": "boolean", "enum": [true] }, "data": { "type": "array", "items": { "$ref": "#/components/schemas/SmsResource" } } }
      },
      "SmsAnalyticsRate": {
        "type": "object",
        "required": ["name", "value"],
        "properties": {
          "name": { "type": "string", "enum": ["delivery_rate", "failure_rate"] },
          "value": { "type": "number", "format": "double", "minimum": 0 }
        }
      },
      "SmsAnalyticsPoint": {
        "type": "object",
        "required": ["date", "total", "delivered", "failed"],
        "properties": {
          "date": { "type": "string", "format": "date" },
          "total": { "type": "integer", "format": "int64", "minimum": 0 },
          "delivered": { "type": "integer", "format": "int64", "minimum": 0 },
          "failed": { "type": "integer", "format": "int64", "minimum": 0 }
        }
      },
      "SmsAnalyticsWindow": {
        "type": "object",
        "required": ["days", "rates", "series"],
        "properties": {
          "days": { "type": "integer", "format": "int32", "enum": [7, 30, 90] },
          "rates": { "type": "array", "items": { "$ref": "#/components/schemas/SmsAnalyticsRate" } },
          "series": { "type": "array", "items": { "$ref": "#/components/schemas/SmsAnalyticsPoint" } }
        }
      },
      "SmsCountryAnalytics": {
        "type": "object",
        "required": ["country", "total", "delivered", "failed"],
        "properties": {
          "country": { "type": "string" },
          "total": { "type": "integer", "format": "int64", "minimum": 0 },
          "delivered": { "type": "integer", "format": "int64", "minimum": 0 },
          "failed": { "type": "integer", "format": "int64", "minimum": 0 }
        }
      },
      "SmsAnalytics": {
        "type": "object",
        "required": ["object", "windows", "delivery_by_country"],
        "properties": {
          "object": { "type": "string", "enum": ["sms.analytics"] },
          "windows": { "type": "array", "items": { "$ref": "#/components/schemas/SmsAnalyticsWindow" } },
          "delivery_by_country": { "type": "array", "maxItems": 25, "items": { "$ref": "#/components/schemas/SmsCountryAnalytics" } }
        }
      },
      "SmsAnalyticsEnvelope": {
        "type": "object",
        "required": ["success", "data"],
        "properties": {
          "success": { "type": "boolean", "enum": [true] },
          "data": { "$ref": "#/components/schemas/SmsAnalytics" }
        }
      },''',
)

# Stronger event object semantics.
replace_once(
'          "object": { "type": "string" },\n          "data": { "type": "array", "items": { "$ref": "#/components/schemas/DeliveryEvent" } }',
'          "object": { "type": "string", "enum": ["list"] },\n          "data": { "type": "array", "items": { "$ref": "#/components/schemas/DeliveryEvent" } }',
)

OPENAPI.write_text(text)
parsed = json.loads(text)

# Assertions for the migration contract.
assert "/emails/analytics" in parsed["paths"]
assert "/sms/analytics" in parsed["paths"]
assert parsed["components"]["schemas"]["EmailBatchArray"]["maxItems"] == 50
assert parsed["components"]["schemas"]["SmsBatchArray"]["maxItems"] == 50
assert "from" not in parsed["components"]["schemas"]["EmailSendRequest"]["required"]
assert len(parsed["paths"]["/emails/{message_id}/events"]["get"]["parameters"]) == 3
assert len(parsed["paths"]["/sms/{message_id}/events"]["get"]["parameters"]) == 2
assert len(parsed["paths"]["/sms"]["get"]["parameters"]) == 7
assert parsed["components"]["schemas"]["EmailAnalytics"]["properties"]["object"]["enum"] == ["email.analytics"]
assert parsed["components"]["schemas"]["SmsAnalytics"]["properties"]["object"]["enum"] == ["sms.analytics"]
print("messaging OpenAPI sync complete")
