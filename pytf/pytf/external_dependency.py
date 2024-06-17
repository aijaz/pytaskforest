from attrs import define, asdict


@define
class ExternalDependency:
    family: str
    job_name: str
