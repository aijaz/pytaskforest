from attrs import define


@define
class PyTfToken:
    name: str
    num_instances: int
