from abc import ABC, abstractmethod


class Orchestrator(ABC):
    @abstractmethod
    def run(self):
        pass