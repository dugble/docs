#!/usr/bin/env python3
"""Check the documented public API route surface against dugble/dugble.

The backend has several HTTP contract classes. This checker treats routes from
PUBLIC_API_PACKAGES as the team-token API Reference surface, requires every
`middleware.tenantAccess` registration to be explicitly classified, and then
compares the exact HTTP method/path set with openapi.json.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}

PUBLIC_API_PACKAGES = {
    "server/internal/modules/broadcast",
    "server/internal/modules/contact",
    "server/internal/modules/contactproperty",
    "server/internal/modules/domain",
    "server/internal/modules/email",
    "server/internal/modules/messagetemplate",
    "server/internal/modules/segment",
    "server/internal/modules/senderid",
    "server/internal/modules/sms",
    "server/internal/modules/suppression",
    "server/internal/modules/topic",
}

# tenantAccess accepts both team tokens and browser sessions. These route sets
# are intentionally outside the current public API Reference. Keeping them here
# means any newly registered tenantAccess module fails CI until it is explicitly
# classified as public or excluded.
TENANT_ACCESS_EXCLUSIONS = {
    "server/internal/billing/plan": "dashboard billing plan surface",
    "server/internal/billing/subscription": "dashboard billing subscription surface",
    "server/internal/billing/wallet": "dashboard billing wallet surface",
    "server/internal/modules/campaign": "SMS campaign/opt-out surface is not in the public API Reference",
    "server/internal/modules/domainclaim": "domain-claim onboarding surface is not in the public API Reference",
}

IMPORT_RE = re.compile(
    r'(?m)^\s*(?:(?P<alias>[A-Za-z_][A-Za-z0-9_]*)\s+)?'
    r'"github\.com/dugble/dugble/(?P<path>server/[^"]+)"'
)
REGISTER_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\.RegisterRoutes\s*\(")
GROUP_RE = re.compile(
    r'\b([A-Za-z_][A-Za-z0-9_]*)\s*:?=\s*'
    r'([A-Za-z_][A-Za-z0-9_]*)\.Group\(\s*"([^"]*)"\s*\)'
)
ROUTE_RE = re.compile(
    r'\b([A-Za-z_][A-Za-z0-9_]*)\.(GET|POST|PUT|PATCH|DELETE)'
    r'\(\s*"([^"]*)"'
)
ANY_ROUTE_CALL_RE = re.compile(
    r'\b([A-Za-z_][A-Za-z0-9_]*)\.(GET|POST|PUT|PATCH|DELETE)\s*\('
)
PATH_PARAM_RE = re.compile(r":([A-Za-z_][A-Za-z0-9_]*)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", type=Path, required=True, help="Path to dugble/dugble checkout")
    parser.add_argument("--openapi", type=Path, required=True, help="Path to docs openapi.json")
    return parser.parse_args()


def strip_go_comments(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
    return re.sub(r"//[^\n]*", "", source)


def find_matching_paren(source: str, open_index: int) -> int:
    depth = 0
    in_string = False
    escaped = False
    for index in range(open_index, len(source)):
        char = source[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("unterminated RegisterRoutes call in backend registry")


def import_aliases(source: str) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for match in IMPORT_RE.finditer(source):
        package_path = match.group("path")
        alias = match.group("alias") or package_path.rsplit("/", 1)[-1]
        aliases[alias] = package_path
    return aliases


def tenant_access_packages(source: str) -> set[str]:
    aliases = import_aliases(source)
    packages: set[str] = set()
    for match in REGISTER_RE.finditer(source):
        alias = match.group(1)
        open_index = source.find("(", match.start())
        close_index = find_matching_paren(source, open_index)
        call = source[match.start() : close_index + 1]
        if "middleware.tenantAccess" not in call:
            continue
        package_path = aliases.get(alias)
        if package_path is None:
            raise ValueError(f"cannot resolve import for RegisterRoutes alias {alias!r}")
        packages.add(package_path)
    return packages


def join_route(prefix: str, suffix: str) -> str:
    parts = [part.strip("/") for part in (prefix, suffix) if part.strip("/")]
    path = "/" + "/".join(parts) if parts else "/"
    return PATH_PARAM_RE.sub(r"{\1}", path)


def route_operations(route_file: Path) -> set[tuple[str, str]]:
    source = strip_go_comments(route_file.read_text(encoding="utf-8"))
    prefixes: dict[str, str] = {"router": ""}

    unresolved = list(GROUP_RE.finditer(source))
    while unresolved:
        progressed = False
        remaining = []
        for match in unresolved:
            variable, parent, suffix = match.groups()
            if parent not in prefixes:
                remaining.append(match)
                continue
            prefixes[variable] = join_route(prefixes[parent], suffix)
            progressed = True
        if not progressed:
            names = ", ".join(sorted({match.group(1) for match in remaining}))
            raise ValueError(f"{route_file}: could not resolve route group(s): {names}")
        unresolved = remaining

    operations: set[tuple[str, str]] = set()
    parsed_starts: set[int] = set()
    for match in ROUTE_RE.finditer(source):
        receiver, method, suffix = match.groups()
        if receiver not in prefixes:
            continue
        parsed_starts.add(match.start())
        operation = (method.lower(), join_route(prefixes[receiver], suffix))
        if operation in operations:
            raise ValueError(f"{route_file}: duplicate route {method} {operation[1]}")
        operations.add(operation)

    # Public route paths must stay literal so comparison remains deterministic.
    for match in ANY_ROUTE_CALL_RE.finditer(source):
        receiver, method = match.groups()
        if receiver in prefixes and match.start() not in parsed_starts:
            raise ValueError(f"{route_file}: {receiver}.{method} must use a literal path")

    if not operations:
        raise ValueError(f"{route_file}: no HTTP routes found")
    return operations


def openapi_operations(openapi_file: Path) -> set[tuple[str, str]]:
    spec = json.loads(openapi_file.read_text(encoding="utf-8"))
    paths = spec.get("paths")
    if not isinstance(paths, dict):
        raise ValueError("openapi.json must contain an object-valued paths field")

    operations: set[tuple[str, str]] = set()
    operation_ids: dict[str, tuple[str, str]] = {}
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            method = method.lower()
            if method not in HTTP_METHODS:
                continue
            key = (method, path)
            operations.add(key)
            if not isinstance(operation, dict):
                raise ValueError(f"OpenAPI operation {method.upper()} {path} must be an object")
            operation_id = operation.get("operationId")
            if not operation_id:
                raise ValueError(f"OpenAPI operation {method.upper()} {path} has no operationId")
            if operation_id in operation_ids:
                previous = operation_ids[operation_id]
                raise ValueError(
                    f"duplicate operationId {operation_id!r}: "
                    f"{previous[0].upper()} {previous[1]} and {method.upper()} {path}"
                )
            operation_ids[operation_id] = key
    return operations


def render(operations: set[tuple[str, str]]) -> list[str]:
    return [
        f"{method.upper():6} {path}"
        for method, path in sorted(operations, key=lambda value: (value[1], value[0]))
    ]


def main() -> int:
    args = parse_args()
    backend = args.backend.resolve()
    registry_file = backend / "server/internal/registry/server/modules.go"

    try:
        registry_source = strip_go_comments(registry_file.read_text(encoding="utf-8"))
        tenant_packages = tenant_access_packages(registry_source)
        classified = PUBLIC_API_PACKAGES | set(TENANT_ACCESS_EXCLUSIONS)

        errors = []
        unclassified = tenant_packages - classified
        stale_public = PUBLIC_API_PACKAGES - tenant_packages
        stale_exclusions = set(TENANT_ACCESS_EXCLUSIONS) - tenant_packages
        if unclassified:
            errors.append("Unclassified tenantAccess package(s):\n  - " + "\n  - ".join(sorted(unclassified)))
        if stale_public:
            errors.append(
                "Public API package(s) are no longer registered with tenantAccess:\n  - "
                + "\n  - ".join(sorted(stale_public))
            )
        if stale_exclusions:
            errors.append("Stale tenantAccess exclusion(s):\n  - " + "\n  - ".join(sorted(stale_exclusions)))
        if errors:
            raise ValueError("\n\n".join(errors))

        backend_operations: set[tuple[str, str]] = set()
        for package_path in sorted(PUBLIC_API_PACKAGES):
            route_file = backend / package_path / "routes.go"
            if not route_file.is_file():
                raise ValueError(f"missing public route file: {route_file}")
            package_operations = route_operations(route_file)
            overlap = backend_operations & package_operations
            if overlap:
                raise ValueError("duplicate public routes across packages:\n  " + "\n  ".join(render(overlap)))
            backend_operations |= package_operations

        documented_operations = openapi_operations(args.openapi.resolve())
        missing_from_openapi = backend_operations - documented_operations
        missing_from_backend = documented_operations - backend_operations

        print(f"Classified tenantAccess packages: {len(tenant_packages)}")
        print(f"Backend public operations:       {len(backend_operations)}")
        print(f"OpenAPI documented operations:  {len(documented_operations)}")

        if missing_from_openapi or missing_from_backend:
            if missing_from_openapi:
                print("\nBackend routes missing from openapi.json:", file=sys.stderr)
                for line in render(missing_from_openapi):
                    print(f"  {line}", file=sys.stderr)
            if missing_from_backend:
                print("\nOpenAPI operations missing from backend public routes:", file=sys.stderr)
                for line in render(missing_from_backend):
                    print(f"  {line}", file=sys.stderr)
            print(
                "\nAPI contract drift detected. Update openapi.json or intentionally "
                "reclassify the backend route package in this checker.",
                file=sys.stderr,
            )
            return 1

        print("API route surface is in sync.")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"API drift check failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
