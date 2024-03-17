from abc import ABC, abstractmethod
from typing import List


class AbstractRetrieval(ABC):
    """
    Abstract class for ingesting repositories into a database.
    """

    @abstractmethod
    def retrieve(self, path: str, hybrid_factor: float) -> List[str]:
        """
        Abstract method to ingest repositories into the database.
        """
        pass