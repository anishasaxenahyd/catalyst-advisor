"""Provider interfaces for the Catalyst Catalog and Catalyst Workbench.

The engine depends only on `KnowledgeProvider`. `CatalogProvider`,
`ModelProvider`, and `WorkbenchProvider` are separate interfaces so any one
of them can be swapped for a REST- or MCP-backed implementation later
without touching the other two or the engine that consumes the composite.
"""

from abc import ABC, abstractmethod

from app.models.schemas import (
    AIModel,
    ArchitecturePattern,
    ComputeProfile,
    DeploymentTarget,
    EnterpriseAsset,
    SecurityProfile,
    WorkspaceTier,
)


class ModelProvider(ABC):
    @abstractmethod
    def list_models(self) -> list[AIModel]: ...


class CatalogProvider(ABC):
    @abstractmethod
    def list_skills(self) -> list[EnterpriseAsset]: ...

    @abstractmethod
    def list_mcp_servers(self) -> list[EnterpriseAsset]: ...

    @abstractmethod
    def list_agents(self) -> list[EnterpriseAsset]: ...

    @abstractmethod
    def list_apis(self) -> list[EnterpriseAsset]: ...

    @abstractmethod
    def list_architecture_templates(self) -> list[ArchitecturePattern]: ...

    def list_all_assets(self) -> list[EnterpriseAsset]:
        return [
            *self.list_skills(),
            *self.list_mcp_servers(),
            *self.list_agents(),
            *self.list_apis(),
        ]


class WorkbenchProvider(ABC):
    @abstractmethod
    def list_workspace_tiers(self) -> list[WorkspaceTier]: ...

    @abstractmethod
    def list_compute_profiles(self) -> list[ComputeProfile]: ...

    @abstractmethod
    def list_security_profiles(self) -> list[SecurityProfile]: ...

    @abstractmethod
    def list_deployment_targets(self) -> list[DeploymentTarget]: ...


class KnowledgeProvider(ABC):
    """The single interface the recommendation engine is allowed to import.

    A concrete implementation may be a flat JSON composite (Phase 0), or may
    fan the same methods out to a REST catalog service and an MCP-backed
    workbench service — the engine cannot tell the difference.
    """

    @abstractmethod
    def list_models(self) -> list[AIModel]: ...

    @abstractmethod
    def list_architecture_templates(self) -> list[ArchitecturePattern]: ...

    @abstractmethod
    def list_enterprise_assets(self) -> list[EnterpriseAsset]: ...

    @abstractmethod
    def list_workspace_tiers(self) -> list[WorkspaceTier]: ...

    @abstractmethod
    def list_compute_profiles(self) -> list[ComputeProfile]: ...

    @abstractmethod
    def list_security_profiles(self) -> list[SecurityProfile]: ...

    @abstractmethod
    def list_deployment_targets(self) -> list[DeploymentTarget]: ...
