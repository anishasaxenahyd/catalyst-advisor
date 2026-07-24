"""JSON-backed implementations of the knowledge provider interfaces.

This is the only place in the codebase that reads a catalog/workbench JSON
file from disk. Swapping to a REST or MCP-backed catalog later means adding
a new class here (or a new module implementing the same interfaces) — the
engine and API layers do not change.
"""

import json
from pathlib import Path

from app.models.schemas import (
    AIModel,
    ArchitecturePattern,
    ComputeProfile,
    DeploymentTarget,
    EnterpriseAsset,
    SecurityProfile,
    WorkspaceTier,
)
from app.providers.knowledge.base import (
    CatalogProvider,
    KnowledgeProvider,
    ModelProvider,
    WorkbenchProvider,
)


def _load(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


class JsonModelProvider(ModelProvider):
    def __init__(self, catalog_dir: Path):
        self._models = [AIModel(**row) for row in _load(catalog_dir / "models.json")]

    def list_models(self) -> list[AIModel]:
        return self._models


class JsonCatalogProvider(CatalogProvider):
    def __init__(self, catalog_dir: Path):
        self._skills = [EnterpriseAsset(**row) for row in _load(catalog_dir / "skills.json")]
        self._mcp_servers = [EnterpriseAsset(**row) for row in _load(catalog_dir / "mcp_servers.json")]
        self._agents = [EnterpriseAsset(**row) for row in _load(catalog_dir / "agents.json")]
        self._apis = [EnterpriseAsset(**row) for row in _load(catalog_dir / "apis.json")]
        self._templates = [
            ArchitecturePattern(**row) for row in _load(catalog_dir / "architecture_templates.json")
        ]

    def list_skills(self) -> list[EnterpriseAsset]:
        return self._skills

    def list_mcp_servers(self) -> list[EnterpriseAsset]:
        return self._mcp_servers

    def list_agents(self) -> list[EnterpriseAsset]:
        return self._agents

    def list_apis(self) -> list[EnterpriseAsset]:
        return self._apis

    def list_architecture_templates(self) -> list[ArchitecturePattern]:
        return self._templates


class JsonWorkbenchProvider(WorkbenchProvider):
    def __init__(self, workbench_dir: Path):
        self._workspace_tiers = [
            WorkspaceTier(**row) for row in _load(workbench_dir / "workspace_tiers.json")
        ]
        self._compute_profiles = [
            ComputeProfile(**row) for row in _load(workbench_dir / "compute_profiles.json")
        ]
        self._security_profiles = [
            SecurityProfile(**row) for row in _load(workbench_dir / "security_profiles.json")
        ]
        self._deployment_targets = [
            DeploymentTarget(**row) for row in _load(workbench_dir / "deployment_targets.json")
        ]

    def list_workspace_tiers(self) -> list[WorkspaceTier]:
        return self._workspace_tiers

    def list_compute_profiles(self) -> list[ComputeProfile]:
        return self._compute_profiles

    def list_security_profiles(self) -> list[SecurityProfile]:
        return self._security_profiles

    def list_deployment_targets(self) -> list[DeploymentTarget]:
        return self._deployment_targets


class CompositeKnowledgeProvider(KnowledgeProvider):
    """Fans the unified KnowledgeProvider interface out to three separately
    swappable providers. This is the only place that knows all three exist."""

    def __init__(
        self,
        catalog: CatalogProvider,
        models: ModelProvider,
        workbench: WorkbenchProvider,
    ):
        self._catalog = catalog
        self._models = models
        self._workbench = workbench

    def list_models(self) -> list[AIModel]:
        return self._models.list_models()

    def list_architecture_templates(self) -> list[ArchitecturePattern]:
        return self._catalog.list_architecture_templates()

    def list_enterprise_assets(self) -> list[EnterpriseAsset]:
        return self._catalog.list_all_assets()

    def list_workspace_tiers(self) -> list[WorkspaceTier]:
        return self._workbench.list_workspace_tiers()

    def list_compute_profiles(self) -> list[ComputeProfile]:
        return self._workbench.list_compute_profiles()

    def list_security_profiles(self) -> list[SecurityProfile]:
        return self._workbench.list_security_profiles()

    def list_deployment_targets(self) -> list[DeploymentTarget]:
        return self._workbench.list_deployment_targets()
