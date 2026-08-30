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


# Use a segment-specific pagination parameter so the generated reference reflects
# the service's exact normalization behavior.
replace_once(
'''        "parameters": [
          { "$ref": "#/components/parameters/LimitOffset" },
          { "$ref": "#/components/parameters/Offset" }
        ],
        "responses": {
          "200": {
            "description": "Segments retrieved successfully.",''',
'''        "parameters": [
          { "$ref": "#/components/parameters/SegmentLimit" },
          { "$ref": "#/components/parameters/SegmentOffset" }
        ],
        "responses": {
          "200": {
            "description": "Segments retrieved successfully.",''',
)

replace_once(
'''        "parameters": [
          { "$ref": "#/components/parameters/SegmentId" },
          { "$ref": "#/components/parameters/LimitOffset" },
          { "$ref": "#/components/parameters/Offset" }
        ],
        "responses": {
          "200": {
            "description": "Segment contacts retrieved successfully.",''',
'''        "parameters": [
          { "$ref": "#/components/parameters/SegmentId" },
          { "$ref": "#/components/parameters/SegmentLimit" },
          { "$ref": "#/components/parameters/SegmentOffset" }
        ],
        "responses": {
          "200": {
            "description": "Segment contacts retrieved successfully.",''',
)

# Add audience-size route between the segment resource and contacts route.
marker = '    "/segments/{segment_id}/contacts": {'
audience_path = '''    "/segments/{segment_id}/audience-size": {
      "get": {
        "operationId": "getSegmentAudienceSize",
        "summary": "Get Segment Audience Size",
        "description": "Returns the current number of contacts assigned to the segment. This is raw segment membership and does not apply unsubscribe, topic, or suppression eligibility rules.",
        "tags": ["Segments"],
        "parameters": [{ "$ref": "#/components/parameters/SegmentId" }],
        "responses": {
          "200": {
            "description": "Segment audience size retrieved successfully.",
            "content": { "application/json": { "schema": { "$ref": "#/components/schemas/SegmentAudienceSizeEnvelope" } } }
          },
          "default": { "$ref": "#/components/responses/Error" }
        }
      }
    },
'''
replace_once(marker, audience_path + marker)

# Add exact segment pagination parameters after Offset.
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
      "SegmentLimit": {
        "name": "limit",
        "in": "query",
        "required": false,
        "description": "Maximum number of records to return. Omitted or non-positive values use 50; values above 100 are capped at 100. Malformed integers return 400.",
        "schema": { "type": "integer", "format": "int32", "default": 50 }
      },
      "SegmentOffset": {
        "name": "offset",
        "in": "query",
        "required": false,
        "description": "Number of records to skip. Omitted or negative values use 0. Malformed integers return 400.",
        "schema": { "type": "integer", "format": "int32", "default": 0 }
      },
''',
)

# Add audience-size response schema next to SegmentResource.
replace_once(
'''      "SegmentResource": {
        "type": "object",
        "properties": {
          "id": { "type": "string", "format": "uuid" },
          "team_id": { "type": "string", "format": "uuid" },
          "name": { "type": "string" },
          "created_at": { "type": "string", "format": "date-time" }
        }
      },
''',
'''      "SegmentResource": {
        "type": "object",
        "required": ["id", "team_id", "name", "created_at"],
        "properties": {
          "id": { "type": "string", "format": "uuid" },
          "team_id": { "type": "string", "format": "uuid" },
          "name": { "type": "string" },
          "created_at": { "type": "string", "format": "date-time" }
        }
      },
      "SegmentAudienceSize": {
        "type": "object",
        "required": ["segment_id", "count"],
        "properties": {
          "segment_id": { "type": "string", "format": "uuid" },
          "count": { "type": "integer", "format": "int64", "minimum": 0 }
        }
      },
      "SegmentAudienceSizeEnvelope": {
        "type": "object",
        "required": ["success", "data"],
        "properties": {
          "success": { "type": "boolean", "enum": [true] },
          "data": { "$ref": "#/components/schemas/SegmentAudienceSize" }
        }
      },
''',
)

# Tighten SegmentContact required fields to match the public struct while keeping
# optional names optional because of omitempty.
replace_once(
'''      "SegmentContact": {
        "type": "object",
        "properties": {''',
'''      "SegmentContact": {
        "type": "object",
        "required": ["id", "team_id", "email", "unsubscribed", "created_at", "updated_at"],
        "properties": {''',
)

parsed = json.loads(text)
assert "/segments/{segment_id}/audience-size" in parsed["paths"]
assert parsed["paths"]["/segments"]["get"]["parameters"][0]["$ref"].endswith("/SegmentLimit")
assert parsed["paths"]["/segments/{segment_id}/contacts"]["get"]["parameters"][1]["$ref"].endswith("/SegmentLimit")
assert parsed["components"]["schemas"]["SegmentAudienceSize"]["properties"]["count"]["format"] == "int64"
assert parsed["components"]["parameters"]["SegmentLimit"]["schema"]["default"] == 50
assert parsed["components"]["parameters"]["SegmentOffset"]["schema"]["default"] == 0

OPENAPI.write_text(json.dumps(parsed, indent=2) + "\n")
