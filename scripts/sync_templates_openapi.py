from __future__ import annotations

import json
from pathlib import Path

OPENAPI = Path("openapi.json")
text = OPENAPI.read_text()


def replace_once(old: str, new: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected exactly one match, found {count}: {old[:80]!r}")
    text = text.replace(old, new, 1)


# Add Templates tag after Domains.
replace_once(
    '    { "name": "Domains", "description": "Manage and verify sending domains." },\n',
    '    { "name": "Domains", "description": "Manage and verify sending domains." },\n'
    '    { "name": "Templates", "description": "Create, version, publish, preview, and test reusable email templates." },\n',
)

# Add all template paths before domains.
marker = '    "/domains": {'
paths = r'''    "/templates": {
      "get": {
        "operationId": "listTemplates",
        "summary": "List Templates",
        "description": "Returns reusable email templates for the authenticated team using limit/offset pagination.",
        "tags": ["Templates"],
        "parameters": [
          { "$ref": "#/components/parameters/LimitOffset" },
          { "$ref": "#/components/parameters/Offset" }
        ],
        "responses": {
          "200": {
            "description": "Templates retrieved successfully.",
            "content": { "application/json": { "schema": { "$ref": "#/components/schemas/TemplateListEnvelope" } } }
          },
          "default": { "$ref": "#/components/responses/Error" }
        }
      },
      "post": {
        "operationId": "createTemplate",
        "summary": "Create Template",
        "description": "Creates a reusable email template and its initial draft version.",
        "tags": ["Templates"],
        "parameters": [{ "$ref": "#/components/parameters/IdempotencyKey" }],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": { "$ref": "#/components/schemas/TemplateCreateRequest" },
              "example": {
                "name": "Welcome email",
                "alias": "welcome-email",
                "category": "welcome",
                "from": "Acme <hello@example.com>",
                "subject": "Welcome, {{{FIRST_NAME}}}",
                "html": "<h1>Welcome {{{FIRST_NAME}}}</h1>",
                "variables": [
                  { "key": "FIRST_NAME_CUSTOM", "type": "string", "fallback_value": "there" }
                ]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Template created successfully.",
            "content": { "application/json": { "schema": { "$ref": "#/components/schemas/MutationEnvelope" } } }
          },
          "default": { "$ref": "#/components/responses/Error" }
        }
      }
    },
    "/templates/{template}": {
      "get": {
        "operationId": "getTemplate",
        "summary": "Retrieve Template",
        "description": "Retrieves a template by UUID or alias, including its current draft content and publish state.",
        "tags": ["Templates"],
        "parameters": [{ "$ref": "#/components/parameters/TemplateIdentifier" }],
        "responses": {
          "200": {
            "description": "Template retrieved successfully.",
            "content": { "application/json": { "schema": { "$ref": "#/components/schemas/TemplateResourceEnvelope" } } }
          },
          "default": { "$ref": "#/components/responses/Error" }
        }
      },
      "patch": {
        "operationId": "updateTemplate",
        "summary": "Update Template",
        "description": "Updates template metadata or content and creates a new current draft version.",
        "tags": ["Templates"],
        "parameters": [
          { "$ref": "#/components/parameters/TemplateIdentifier" },
          { "$ref": "#/components/parameters/IdempotencyKey" }
        ],
        "requestBody": {
          "required": true,
          "content": { "application/json": { "schema": { "$ref": "#/components/schemas/TemplateUpdateRequest" } } }
        },
        "responses": {
          "200": {
            "description": "Template updated successfully.",
            "content": { "application/json": { "schema": { "$ref": "#/components/schemas/MutationEnvelope" } } }
          },
          "default": { "$ref": "#/components/responses/Error" }
        }
      },
      "delete": {
        "operationId": "deleteTemplate",
        "summary": "Delete Template",
        "description": "Deletes a reusable email template.",
        "tags": ["Templates"],
        "parameters": [
          { "$ref": "#/components/parameters/TemplateIdentifier" },
          { "$ref": "#/components/parameters/IdempotencyKey" }
        ],
        "responses": {
          "200": {
            "description": "Template deleted successfully.",
            "content": { "application/json": { "schema": { "$ref": "#/components/schemas/DeleteEnvelope" } } }
          },
          "default": { "$ref": "#/components/responses/Error" }
        }
      }
    },
    "/templates/{template}/publish": {
      "post": {
        "operationId": "publishTemplate",
        "summary": "Publish Template",
        "description": "Publishes the template's current version. The current version must have a non-empty subject and valid content.",
        "tags": ["Templates"],
        "parameters": [
          { "$ref": "#/components/parameters/TemplateIdentifier" },
          { "$ref": "#/components/parameters/IdempotencyKey" }
        ],
        "responses": {
          "200": {
            "description": "Template published successfully.",
            "content": { "application/json": { "schema": { "$ref": "#/components/schemas/MutationEnvelope" } } }
          },
          "default": { "$ref": "#/components/responses/Error" }
        }
      }
    },
    "/templates/{template}/duplicate": {
      "post": {
        "operationId": "duplicateTemplate",
        "summary": "Duplicate Template",
        "description": "Duplicates the template's current version into a new draft template. The generated name defaults to the source name plus ' Copy'.",
        "tags": ["Templates"],
        "parameters": [
          { "$ref": "#/components/parameters/TemplateIdentifier" },
          { "$ref": "#/components/parameters/IdempotencyKey" }
        ],
        "responses": {
          "200": {
            "description": "Template duplicated successfully.",
            "content": { "application/json": { "schema": { "$ref": "#/components/schemas/MutationEnvelope" } } }
          },
          "default": { "$ref": "#/components/responses/Error" }
        }
      }
    },
    "/templates/{template}/versions": {
      "get": {
        "operationId": "listTemplateVersions",
        "summary": "List Template Versions",
        "description": "Returns template versions using limit/offset pagination.",
        "tags": ["Templates"],
        "parameters": [
          { "$ref": "#/components/parameters/TemplateIdentifier" },
          { "$ref": "#/components/parameters/LimitOffset" },
          { "$ref": "#/components/parameters/Offset" }
        ],
        "responses": {
          "200": {
            "description": "Template versions retrieved successfully.",
            "content": { "application/json": { "schema": { "$ref": "#/components/schemas/TemplateVersionListEnvelope" } } }
          },
          "default": { "$ref": "#/components/responses/Error" }
        }
      }
    },
    "/templates/{template}/versions/{version_id}": {
      "get": {
        "operationId": "getTemplateVersion",
        "summary": "Retrieve Template Version",
        "description": "Retrieves a specific immutable template version.",
        "tags": ["Templates"],
        "parameters": [
          { "$ref": "#/components/parameters/TemplateIdentifier" },
          { "$ref": "#/components/parameters/TemplateVersionId" }
        ],
        "responses": {
          "200": {
            "description": "Template version retrieved successfully.",
            "content": { "application/json": { "schema": { "$ref": "#/components/schemas/TemplateVersionEnvelope" } } }
          },
          "default": { "$ref": "#/components/responses/Error" }
        }
      }
    },
    "/templates/{template}/versions/{version_id}/revert": {
      "post": {
        "operationId": "revertTemplateVersion",
        "summary": "Revert Template Version",
        "description": "Creates a new current draft version by copying content from the selected historical version.",
        "tags": ["Templates"],
        "parameters": [
          { "$ref": "#/components/parameters/TemplateIdentifier" },
          { "$ref": "#/components/parameters/TemplateVersionId" },
          { "$ref": "#/components/parameters/IdempotencyKey" }
        ],
        "responses": {
          "200": {
            "description": "Template reverted successfully.",
            "content": { "application/json": { "schema": { "$ref": "#/components/schemas/TemplateStateEnvelope" } } }
          },
          "default": { "$ref": "#/components/responses/Error" }
        }
      }
    },
    "/templates/{template}/preview": {
      "post": {
        "operationId": "previewTemplate",
        "summary": "Preview Template",
        "description": "Renders the current or requested template version with optional variable values without sending it.",
        "tags": ["Templates"],
        "parameters": [{ "$ref": "#/components/parameters/TemplateIdentifier" }],
        "requestBody": {
          "required": false,
          "content": { "application/json": { "schema": { "$ref": "#/components/schemas/TemplatePreviewRequest" } } }
        },
        "responses": {
          "200": {
            "description": "Template preview rendered successfully.",
            "content": { "application/json": { "schema": { "$ref": "#/components/schemas/TemplatePreviewEnvelope" } } }
          },
          "default": { "$ref": "#/components/responses/Error" }
        }
      }
    },
    "/templates/{template}/test-send": {
      "post": {
        "operationId": "testSendTemplate",
        "summary": "Test Send Template",
        "description": "Renders the current or requested version and queues a test email to one recipient.",
        "tags": ["Templates"],
        "parameters": [
          { "$ref": "#/components/parameters/TemplateIdentifier" },
          { "$ref": "#/components/parameters/IdempotencyKey" }
        ],
        "requestBody": {
          "required": true,
          "content": { "application/json": { "schema": { "$ref": "#/components/schemas/TemplateTestSendRequest" } } }
        },
        "responses": {
          "202": {
            "description": "Template test email accepted for delivery.",
            "content": { "application/json": { "schema": { "$ref": "#/components/schemas/MutationEnvelope" } } }
          },
          "default": { "$ref": "#/components/responses/Error" }
        }
      }
    },
'''
replace_once(marker, paths + marker)

# Add path parameters after DomainId.
replace_once(
    '      "DomainId": { "name": "domain_id", "in": "path", "required": true, "schema": { "type": "string", "format": "uuid" } },\n',
    '      "DomainId": { "name": "domain_id", "in": "path", "required": true, "schema": { "type": "string", "format": "uuid" } },\n'
    '      "TemplateIdentifier": { "name": "template", "in": "path", "required": true, "description": "Template UUID or alias.", "schema": { "type": "string" } },\n'
    '      "TemplateVersionId": { "name": "version_id", "in": "path", "required": true, "schema": { "type": "string", "format": "uuid" } },\n',
)

# Add schemas before DomainCreateRequest.
schema_marker = '      "DomainCreateRequest": {'
schemas = r'''      "TemplateCategory": {
        "type": "string",
        "enum": ["otp", "welcome", "receipt", "alert", "notification", "custom"]
      },
      "TemplateVariableInput": {
        "type": "object",
        "required": ["key", "type"],
        "properties": {
          "key": { "type": "string", "pattern": "^[A-Za-z][A-Za-z0-9_]{0,49}$" },
          "type": { "type": "string", "enum": ["string", "number"] },
          "fallback_value": {}
        },
        "additionalProperties": false
      },
      "TemplateReplyToInput": {
        "oneOf": [
          { "type": "string" },
          { "type": "array", "items": { "type": "string" } }
        ]
      },
      "TemplateCreateRequest": {
        "type": "object",
        "required": ["name", "html", "category"],
        "properties": {
          "name": { "type": "string", "minLength": 1, "maxLength": 100 },
          "html": { "type": "string", "minLength": 1 },
          "alias": { "type": "string", "maxLength": 100, "pattern": "^[A-Za-z0-9_-]+$" },
          "category": { "$ref": "#/components/schemas/TemplateCategory" },
          "from": { "type": "string", "description": "Email address, optionally with a display name." },
          "subject": { "type": "string", "maxLength": 255 },
          "reply_to": { "$ref": "#/components/schemas/TemplateReplyToInput" },
          "text": { "type": "string" },
          "variables": { "type": "array", "maxItems": 50, "items": { "$ref": "#/components/schemas/TemplateVariableInput" } }
        },
        "additionalProperties": false
      },
      "TemplateUpdateRequest": {
        "type": "object",
        "properties": {
          "name": { "type": "string", "minLength": 1, "maxLength": 100 },
          "html": { "type": "string", "minLength": 1 },
          "alias": { "type": "string", "maxLength": 100, "pattern": "^[A-Za-z0-9_-]+$" },
          "category": { "$ref": "#/components/schemas/TemplateCategory" },
          "from": { "type": "string", "description": "Email address, optionally with a display name." },
          "subject": { "type": "string", "maxLength": 255 },
          "reply_to": { "$ref": "#/components/schemas/TemplateReplyToInput" },
          "text": { "type": "string" },
          "variables": { "type": "array", "maxItems": 50, "items": { "$ref": "#/components/schemas/TemplateVariableInput" } }
        },
        "additionalProperties": false
      },
      "TemplateVariableResource": {
        "type": "object",
        "required": ["id", "key", "type", "created_at", "updated_at"],
        "properties": {
          "id": { "type": "string", "format": "uuid" },
          "key": { "type": "string" },
          "type": { "type": "string", "enum": ["string", "number"] },
          "fallback_value": {},
          "created_at": { "type": "string", "format": "date-time" },
          "updated_at": { "type": "string", "format": "date-time" }
        }
      },
      "TemplateResource": {
        "type": "object",
        "required": ["object", "id", "current_version_id", "name", "category", "created_at", "updated_at", "status", "reply_to", "html", "variables", "has_unpublished_versions"],
        "properties": {
          "object": { "type": "string", "enum": ["template"] },
          "id": { "type": "string", "format": "uuid" },
          "current_version_id": { "type": "string", "format": "uuid" },
          "alias": { "type": ["string", "null"] },
          "name": { "type": "string" },
          "category": { "$ref": "#/components/schemas/TemplateCategory" },
          "created_at": { "type": "string", "format": "date-time" },
          "updated_at": { "type": "string", "format": "date-time" },
          "status": { "type": "string", "enum": ["draft", "published"] },
          "published_at": { "type": ["string", "null"], "format": "date-time" },
          "from": { "type": ["string", "null"] },
          "subject": { "type": ["string", "null"] },
          "reply_to": { "type": "array", "items": { "type": "string" } },
          "html": { "type": "string" },
          "text": { "type": ["string", "null"] },
          "variables": { "type": "array", "items": { "$ref": "#/components/schemas/TemplateVariableResource" } },
          "has_unpublished_versions": { "type": "boolean" }
        }
      },
      "TemplateListItem": {
        "type": "object",
        "required": ["id", "name", "category", "status", "created_at", "updated_at"],
        "properties": {
          "id": { "type": "string", "format": "uuid" },
          "name": { "type": "string" },
          "category": { "$ref": "#/components/schemas/TemplateCategory" },
          "status": { "type": "string", "enum": ["draft", "published"] },
          "published_at": { "type": ["string", "null"], "format": "date-time" },
          "created_at": { "type": "string", "format": "date-time" },
          "updated_at": { "type": "string", "format": "date-time" },
          "alias": { "type": ["string", "null"] }
        }
      },
      "TemplateList": {
        "type": "object",
        "required": ["object", "data", "has_more"],
        "properties": {
          "object": { "type": "string", "enum": ["list"] },
          "data": { "type": "array", "items": { "$ref": "#/components/schemas/TemplateListItem" } },
          "has_more": { "type": "boolean" }
        }
      },
      "TemplateVersion": {
        "type": "object",
        "required": ["id", "team_id", "template_id", "version_number", "subject", "html", "variables", "created_at"],
        "properties": {
          "id": { "type": "string", "format": "uuid" },
          "team_id": { "type": "string", "format": "uuid" },
          "template_id": { "type": "string", "format": "uuid" },
          "version_number": { "type": "integer", "format": "int32" },
          "from_email": { "type": "string", "format": "email" },
          "from_name": { "type": "string" },
          "reply_to_email": { "type": "string" },
          "subject": { "type": "string" },
          "html": { "type": "string" },
          "text": { "type": "string" },
          "variables": { "type": "array", "items": { "$ref": "#/components/schemas/TemplateVariableInput" } },
          "based_on_version_id": { "type": "string", "format": "uuid" },
          "change_note": { "type": "string" },
          "created_at": { "type": "string", "format": "date-time" }
        }
      },
      "TemplateState": {
        "type": "object",
        "required": ["id", "team_id", "name", "category", "has_unpublished_changes", "created_at", "updated_at"],
        "properties": {
          "id": { "type": "string", "format": "uuid" },
          "team_id": { "type": "string", "format": "uuid" },
          "name": { "type": "string" },
          "alias": { "type": ["string", "null"] },
          "category": { "$ref": "#/components/schemas/TemplateCategory" },
          "current_version_id": { "type": "string", "format": "uuid" },
          "published_version_id": { "type": "string", "format": "uuid" },
          "published_at": { "type": "string", "format": "date-time" },
          "has_unpublished_changes": { "type": "boolean" },
          "created_at": { "type": "string", "format": "date-time" },
          "updated_at": { "type": "string", "format": "date-time" }
        }
      },
      "TemplatePreviewRequest": {
        "type": "object",
        "properties": {
          "version_id": { "type": "string", "format": "uuid" },
          "variables": { "type": "object", "additionalProperties": true }
        },
        "additionalProperties": false
      },
      "TemplatePreview": {
        "type": "object",
        "required": ["template_id", "version_id", "subject", "html"],
        "properties": {
          "template_id": { "type": "string", "format": "uuid" },
          "version_id": { "type": "string", "format": "uuid" },
          "subject": { "type": "string" },
          "html": { "type": "string" },
          "text": { "type": "string" },
          "from_email": { "type": "string", "format": "email" },
          "from_name": { "type": "string" },
          "reply_to": { "type": "string" }
        }
      },
      "TemplateTestSendRequest": {
        "type": "object",
        "required": ["to"],
        "properties": {
          "to": { "type": "string", "format": "email" },
          "version_id": { "type": "string", "format": "uuid" },
          "variables": { "type": "object", "additionalProperties": true }
        },
        "additionalProperties": false
      },
      "TemplateResourceEnvelope": { "type": "object", "required": ["success", "data"], "properties": { "success": { "type": "boolean", "enum": [true] }, "data": { "$ref": "#/components/schemas/TemplateResource" } } },
      "TemplateListEnvelope": { "type": "object", "required": ["success", "data"], "properties": { "success": { "type": "boolean", "enum": [true] }, "data": { "$ref": "#/components/schemas/TemplateList" } } },
      "TemplateVersionEnvelope": { "type": "object", "required": ["success", "data"], "properties": { "success": { "type": "boolean", "enum": [true] }, "data": { "$ref": "#/components/schemas/TemplateVersion" } } },
      "TemplateVersionListEnvelope": { "type": "object", "required": ["success", "data"], "properties": { "success": { "type": "boolean", "enum": [true] }, "data": { "type": "array", "items": { "$ref": "#/components/schemas/TemplateVersion" } } } },
      "TemplateStateEnvelope": { "type": "object", "required": ["success", "data"], "properties": { "success": { "type": "boolean", "enum": [true] }, "data": { "$ref": "#/components/schemas/TemplateState" } } },
      "TemplatePreviewEnvelope": { "type": "object", "required": ["success", "data"], "properties": { "success": { "type": "boolean", "enum": [true] }, "data": { "$ref": "#/components/schemas/TemplatePreview" } } },
'''
replace_once(schema_marker, schemas + schema_marker)

spec = json.loads(text)
assert any(tag.get("name") == "Templates" for tag in spec["tags"])
for route in [
    "/templates", "/templates/{template}", "/templates/{template}/publish",
    "/templates/{template}/duplicate", "/templates/{template}/versions",
    "/templates/{template}/versions/{version_id}",
    "/templates/{template}/versions/{version_id}/revert",
    "/templates/{template}/preview", "/templates/{template}/test-send",
]:
    assert route in spec["paths"]
assert spec["paths"]["/templates"]["post"]["responses"].get("200")
assert spec["paths"]["/templates/{template}/test-send"]["post"]["responses"].get("202")
assert set(spec["components"]["schemas"]["TemplateCreateRequest"]["required"]) == {"name", "html", "category"}
assert spec["components"]["schemas"]["TemplateList"]["properties"]["has_more"]

OPENAPI.write_text(text)
