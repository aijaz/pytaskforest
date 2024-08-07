import re

from attrs import define

from .job import Job
from .external_dependency import ExternalDependency


@define
class Forest:
    jobs: [[Job | ExternalDependency]]

    @classmethod
    def split_jobs(cls, line: str, family_name: str) -> [Job]:
        pattern = re.compile('#.*')
        line = re.sub(pattern, '', line)

        pattern = re.compile(r'([^(]+\([^)]*\))')
        job_strs = [i.strip() for i in re.findall(pattern, line)]
        return [ExternalDependency.parse(job_str) if '::' in job_str else Job.parse(job_str, family_name) for job_str in job_strs]

    def _get_all_internal_jobs(self) -> [Job]:
        result = []
        for job_list in self.jobs:
            result.extend(item for item in job_list if isinstance(item, Job))
        return result

