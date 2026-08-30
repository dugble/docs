from pathlib import Path
import json

path = Path("openapi.json")
text = path.read_text()

replacements = [
    (
'''        "parameters": [
          { "$ref": "#/components/parameters/LimitOffset" },
          { "$ref": "#/components/parameters/Offset" }
        ],
        "responses": {
          "200": {
            "description": "Templates retrieved successfully."''',
'''        "parameters": [
          { "$ref": "#/components/parameters/TemplateLimit" },
          { "$ref": "#/components/parameters/TemplateOffset" }
        ],
        "responses": {
          "200": {
            "description": "Templates retrieved successfully."'''
    ),
    (
'''        "parameters": [
          { "$ref": "#/components/parameters/TemplateIdentifier" },
          { "$ref": "#/components/parameters/LimitOffset" },
          { "$ref": "#/components/parameters/Offset" }
        ],
        "responses": {
          "200": {
            "description": "Template versions retrieved successfully."''',
'''        "parameters": [
          { "$ref": "#/components/parameters/TemplateIdentifier" },
          { "$ref": "#/components/parameters/TemplateLimit" },
          { "$ref": "#/components/parameters/TemplateOffset" }
        ],
        "responses": {
          "200": {
            "description": "Template versions retrieved successfully."'''
    ),
    (
'''        "tags": ["Domains"],
        "responses": {
          "200": {
            "description": "Sending domains retrieved successfully."''',
'''        "tags": ["Domains"],
        "parameters": [
          { "$ref": "#/components/parameters/DomainLimit" },
          { "$ref": "#/components/parameters/DomainOffset" }
        ],
        "responses": {
          "200": {
            "description": "Sending domains retrieved successfully."'''
    ),
    (
'''        "parameters": [
          { "$ref": "#/components/parameters/CursorLimit" },
          { "$ref": "#/components/parameters/After" },
          { "$ref": "#/components/parameters/Before" }
        ],
        "responses": {
          "200": {
            "description": "Topics retrieved successfully."''',
'''        "parameters": [
          { "$ref": "#/components/parameters/TopicLimit" },
          { "$ref": "#/components/parameters/TopicOffset" }
        ],
        "responses": {
          "200": {
            "description": "Topics retrieved successfully."'''
    ),
    (
'''      "SegmentLimit": {
        "name": "limit",
        "in": "query",
        "required": false,
        "description": "Maximum number of records to return. Omitted or non-positive values use 50; values above 100 are capped at 100. Malformed integers return 400.",
        "schema": { "type": "integer", "format": "int32", "default": 50 }
      },''',
'''      "TemplateLimit": {
        "name": "limit",
        "in": "query",
        "required": false,
        "description": "Maximum number of templates or template versions to return. Omitted or non-positive values use 50; values above 100 are capped at 100. Malformed integers return 400.",
        "schema": { "type": "integer", "format": "int32", "default": 50 }
      },
      "TemplateOffset": {
        "name": "offset",
        "in": "query",
        "required": false,
        "description": "Number of templates or template versions to skip. Omitted or negative values use 0. Malformed integers return 400.",
        "schema": { "type": "integer", "format": "int32", "default": 0 }
      },
      "DomainLimit": {
        "name": "limit",
        "in": "query",
        "required": false,
        "description": "Maximum number of sender domains to return. Omitted, non-positive, or values above 100 use the default 50. Malformed integers return 400.",
        "schema": { "type": "integer", "format": "int32", "default": 50 }
      },
      "DomainOffset": {
        "name": "offset",
        "in": "query",
        "required": false,
        "description": "Number of sender domains to skip. Omitted or negative values use 0. Malformed integers return 400.",
        "schema": { "type": "integer", "format": "int32", "default": 0 }
      },
      "TopicLimit": {
        "name": "limit",
        "in": "query",
        "required": false,
        "description": "Maximum number of topics to return. Omitted, non-positive, or values above 100 use the default 50. Malformed integers return 400.",
        "schema": { "type": "integer", "format": "int32", "default": 50 }
      },
      "TopicOffset": {
        "name": "offset",
        "in": "query",
        "required": false,
        "description": "Number of topics to skip. Omitted or negative values use 0. Malformed integers return 400.",
        "schema": { "type": "integer", "format": "int32", "default": 0 }
      },
      "SegmentLimit": {
        "name": "limit",
        "in": "query",
        "required": false,
        "description": "Maximum number of records to return. Omitted or non-positive values use 50; values above 100 are capped at 100. Malformed integers return 400.",
        "schema": { "type": "integer", "format": "int32", "default": 50 }
      },'''
    ),
]

for old, new in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one match, got {count}: {old[:80]!r}")
    text = text.replace(old, new, 1)

json.loads(text)
path.write_text(text)
