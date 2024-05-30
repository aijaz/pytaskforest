from attrs import define

from .job import Job
from .external_dependency import ExternalDependency


@define
class Forest:
    jobs: [[Job | ExternalDependency]]

    @classmethod
    def parse(cls, job_string: str):
        j = cls(
            jobs=[[]]
        )
        return j
