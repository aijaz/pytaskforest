import re

from attrs import define

from .job import Job
from .external_dependency import ExternalDependency


@define
class Forest:
    jobs: [[Job | ExternalDependency]]

    @classmethod
    def parse(cls, job_string: str):
        return cls(jobs=[])

    @classmethod
    def split_jobs(cls, line: str, family_name: str) -> [Job]:
        pattern = re.compile('#.*')
        line = re.sub(pattern, '', line)

        pattern = re.compile(r'([^(]+\([^)]*\))')
        job_strs = [i.strip() for i in re.findall(pattern, line)]
        the_list = [ExternalDependency.parse(job_str) if '::' in job_str else Job.parse(job_str) for job_str in job_strs]
        return list(map(lambda j: cls._assign_family_name_to_internal_job(j, family_name), the_list))

    @classmethod
    def _assign_family_name_to_internal_job(cls, job: Job, family_name: str) -> Job:
        job.family_name = job.family_name or family_name  # don't change family name for external dependencies
        return job

    def get_all_internal_jobs(self) -> [Job]:
        result = []
        for job_list in self.jobs:
            result.extend(item for item in job_list if isinstance(item, Job))
        return result

