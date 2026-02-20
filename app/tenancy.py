import os
from dataclasses import dataclass
from typing import Literal
from .config import STORAGE_ROOT, TENANCY_MODE

Scope = Literal["dept", "user"]

@dataclass(frozen=True)
class Tenancy:
    tenant_id: str
    dept_id: str
    user_id: str
    collection: str = "knowledgebase"

    @property
    def scope(self) -> Scope:
        return "user" if TENANCY_MODE == "user" else "dept"

    @property
    def namespace(self) -> str:
        # cost-effective default: per-dept shared KB
        if self.scope == "dept":
            return f"{self.tenant_id}__{self.dept_id}__{self.collection}"
        # strict isolation: per-user KB
        return f"{self.tenant_id}__{self.dept_id}__user-{self.user_id}__{self.collection}"

    @property
    def index_dir_current(self) -> str:
        return os.path.join(STORAGE_ROOT, "indexes", self.namespace, "current")

    @property
    def manifest_path(self) -> str:
        return os.path.join(STORAGE_ROOT, "manifests", f"{self.namespace}.json")