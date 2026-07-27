"""JSON and YAML file loaders — the "initially" in "JSON/YAML initially".
Both share `FileKnowledgeLoader`; adding a third format (e.g. CSV, or a
paginated REST source) means one new small subclass implementing
`_parse_raw`, not touching the JSON/YAML implementations or anything that
consumes `KnowledgeSourceLoader`.
"""

import json
from pathlib import Path
from typing import Generic, TypeVar

import yaml
from pydantic import BaseModel, TypeAdapter

from app.enterprise_knowledge.ingestion.base import KnowledgeSourceLoader

T = TypeVar("T", bound=BaseModel)


class FileKnowledgeLoader(KnowledgeSourceLoader[T], Generic[T]):
    def __init__(self, path: Path, model: type[T]):
        self.path = path
        self.model = model

    def _parse_raw(self) -> list[dict]:
        raise NotImplementedError

    def load(self) -> list[T]:
        raw = self._parse_raw()
        adapter = TypeAdapter(list[self.model])
        return adapter.validate_python(raw)


class JsonKnowledgeLoader(FileKnowledgeLoader[T]):
    def _parse_raw(self) -> list[dict]:
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)


class YamlKnowledgeLoader(FileKnowledgeLoader[T]):
    def _parse_raw(self) -> list[dict]:
        with self.path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data or []
