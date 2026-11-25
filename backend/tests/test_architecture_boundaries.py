"""
Architecture Boundary Tests for CampusConnect.
Governing Baseline: architecture.md v1.1, AGENTS.md Section 5.1 & Section 11.

PHASE 3 INTEGRATION GATE:
Enforces strict separation of concerns across architectural layers:
    API Routes -> Services -> Repositories + DSAManager
Routes must NEVER directly import from Repositories or DSAManager.
Currently in Phase 2, the routes directory contains health.py.
This automated AST test serves as a permanent integration gate for Phase 3 routes.
"""

import ast
import os
import pytest


PROHIBITED_MODULES = {
    "app.repositories",
    "repositories",
    "app.dsa",
    "dsa",
}


def check_ast_imports_for_prohibited_modules(source_code: str, file_path: str = "<string>") -> list[str]:
    """
    Parse Python source code via AST and return a list of prohibited import violations.
    Checks both absolute and relative import statements.
    """
    violations = []
    tree = ast.parse(source_code, filename=file_path)

    for node in ast.walk(tree):
        # 1. Absolute import: import foo, import foo.bar
        if isinstance(node, ast.Import):
            for alias in node.names:
                for prohibited in PROHIBITED_MODULES:
                    if alias.name == prohibited or alias.name.startswith(f"{prohibited}."):
                        violations.append(
                            f"Line {node.lineno}: Prohibited absolute import '{alias.name}'"
                        )
                        break

        # 2. From import: from foo import bar, from ..foo import bar
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            # Resolve module relative to app package:
            if node.level == 2:
                resolved_mod = f"app.{module}" if module else "app"
            elif node.level == 1:
                resolved_mod = f"app.routes.{module}" if module else "app.routes"
            else:
                resolved_mod = module

            violation_found = False
            for prohibited in PROHIBITED_MODULES:
                if (
                    resolved_mod == prohibited
                    or resolved_mod.startswith(f"{prohibited}.")
                    or module == prohibited
                    or module.startswith(f"{prohibited}.")
                ):
                    violations.append(
                        f"Line {node.lineno}: Prohibited from-import '{resolved_mod}' (level={node.level})"
                    )
                    violation_found = True
                    break

            if not violation_found and resolved_mod == "app" and node.level == 2:
                for alias in node.names:
                    if alias.name in ("repositories", "dsa"):
                        violations.append(
                            f"Line {node.lineno}: Prohibited import of '{alias.name}' from parent module"
                        )
                        break

    return violations


def test_routes_do_not_import_repositories_or_dsa():
    """
    Phase 3 Integration Gate:
    Verify that all route handlers in backend/app/routes/ do not directly import
    from repositories or dsa modules.
    Fails if the expected route directory is missing or contains no route files.
    """
    routes_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "app", "routes")
    )

    if not os.path.isdir(routes_dir):
        pytest.fail(f"Expected routes directory does not exist: {routes_dir}")

    route_files = [
        f for f in os.listdir(routes_dir)
        if f.endswith(".py") and f != "__init__.py"
    ]

    if not route_files:
        pytest.fail(f"Expected route directory contains no Python route files: {routes_dir}")

    total_violations = {}
    for filename in route_files:
        filepath = os.path.join(routes_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        file_violations = check_ast_imports_for_prohibited_modules(content, filepath)
        if file_violations:
            total_violations[filename] = file_violations

    if total_violations:
        msg_lines = ["Architectural boundary violation: Routes must not directly import Repositories or DSA."]
        for fname, viols in total_violations.items():
            msg_lines.append(f"\nIn {fname}:")
            for v in viols:
                msg_lines.append(f"  - {v}")
        pytest.fail("\n".join(msg_lines))


def test_ast_boundary_scanner_detects_prohibited_imports():
    """
    Verify that the AST scanner correctly catches both absolute and relative
    prohibited imports and permits clean service-layer imports.
    """
    # Prohibited imports
    bad_code_1 = "import app.repositories.user_repo"
    assert len(check_ast_imports_for_prohibited_modules(bad_code_1)) == 1

    bad_code_2 = "from app.dsa.manager import get_dsa_manager"
    assert len(check_ast_imports_for_prohibited_modules(bad_code_2)) == 1

    bad_code_3 = "from ..repositories import UserRepository"
    assert len(check_ast_imports_for_prohibited_modules(bad_code_3)) == 1

    bad_code_4 = "from ..dsa.manager import DSAManager"
    assert len(check_ast_imports_for_prohibited_modules(bad_code_4)) == 1

    bad_code_5 = "from .. import repositories"
    assert len(check_ast_imports_for_prohibited_modules(bad_code_5)) == 1

    # Permitted clean imports
    clean_code = """
from flask import Blueprint, jsonify, request
from app.services.auth_service import AuthService
from app.services.connection_service import ConnectionService
import logging
"""
    assert len(check_ast_imports_for_prohibited_modules(clean_code)) == 0
