from attrs import define


@define
class Token:
    name: str
    num_instances: int
