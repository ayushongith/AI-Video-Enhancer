import logging
from abc import ABC, abstractmethod
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class EnhancementResult:
    def __init__(
        self,
        frame: np.ndarray,
        metadata: Optional[dict] = None,
    ) -> None:
        self.frame = frame
        self.metadata = metadata or {}


class BaseEnhancer(ABC):
    def __init__(self) -> None:
        self._name: str = self.__class__.__name__

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    def process(self, frame: np.ndarray) -> EnhancementResult:
        ...

    def __repr__(self) -> str:
        return f"<{self._name}>"
