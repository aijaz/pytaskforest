import re

from attrs import define


@define
class ExternalDependency:
    family_name: str
    job_name: str

    @classmethod
    def parse(cls, job_string: str):
        j = cls(
            job_name="",
            family_name="",
        )
        pattern = re.compile('([0-9A-Za-z_]+)::([0-9A-Za-z_]+)\\((.*)\\)')
        match = pattern.match(job_string)
        j.family_name = match[1]
        j.job_name = match[2]
        return j
