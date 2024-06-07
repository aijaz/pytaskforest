import tomlkit
import tomlkit.exceptions

from attrs import define, field

@define
class Config():
    toml_str: str = field(init=True)
    d = field(init=False, default={})

    def __getitem__(self, item):
        return self.d[item]

    @classmethod
    def from_str(cls, toml_str):
        try:
            d = tomlkit.loads(toml_str)
            obj = cls(toml_str=toml_str)
            obj.d = d
            return obj
        except tomlkit.exceptions.UnexpectedCharError as e:
            return cls("")
