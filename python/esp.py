import json
import os
from enum import Enum
import abc


class DependencyType(Enum):
    COMPUTE_GIT = "compute:git"
    COMPUTE_DOCKER = "compute:docker"
    DATA_SENTINEL2 = "data:sentinel-2"


class ToDict:
    @abc.abstractmethod
    def to_dict(self, res):
        pass


class Dependency(ToDict):
    type: DependencyType

    def __init__(self, type: DependencyType):
        self.type = type

    def to_dict(self, res):
        res["type"] = self.type.value


class GitComputeDependency(Dependency):
    repo: str
    input: dict

    def __init__(self, repo: str, input: dict):
        Dependency.__init__(self, DependencyType.COMPUTE_GIT)
        self.repo = repo
        self.input = input

    def to_dict(self, res):
        Dependency.to_dict(self, res)
        res["repo"] = self.repo
        res["input"] = self.input


def git_compute(repo: str, input: dict) -> GitComputeDependency:
    return GitComputeDependency(repo, input)


class DockerComputeDependency(Dependency):
    image: str
    input: dict

    def __init__(self, image: str, input: dict):
        Dependency.__init__(self, DependencyType.COMPUTE_DOCKER)
        self.image = image
        self.input = input

    def to_dict(self, res):
        Dependency.to_dict(self, res)
        res["image"] = self.image
        res["input"] = self.input


def docker_compute(image: str, input: dict) -> DockerComputeDependency:
    return DockerComputeDependency(image, input)


class Sentinel2DataDependency(Dependency):
    utm_zone: int
    latitude_band: str
    grid_square: str
    year: int
    month: int
    day: int
    sequence: int

    def __init__(self, utm_zone: int, latitude_band: str, grid_square: str,
                 year: int, month: int, day: int, sequence: int):
        Dependency.__init__(self, DependencyType.DATA_SENTINEL2)
        self.utm_zone = utm_zone
        self.latitude_band = latitude_band
        self.grid_square = grid_square
        self.year = year
        self.month = month
        self.day = day
        self.sequence = sequence

    def to_dict(self, res):
        Dependency.to_dict(res)
        res["utm_zone"] = self.utm_zone
        res["latitude_band"] = self.latitude_band
        res["grid_square"] = self.grid_square
        res["year"] = self.year
        res["month"] = self.month
        res["day"] = self.day
        res["sequence"] = self.sequence


def sentinel2_data(
        utm_zone: int, latitude_band: str, grid_square: str,
        year: int, month: int, day: int, sequence: int) -> Sentinel2DataDependency:
    return Sentinel2DataDependency(utm_zone, latitude_band, grid_square, year, month, day, sequence)


def __get_var_or_default(var: str, default: str) -> str:
    x = os.environ.get(var)
    if x is None:
        return default
    else:
        return x


def get_input_dir() -> str:
    return __get_var_or_default("INPUT", "./input")


def get_out_dir() -> str:
    return __get_var_or_default("OUT", "./out")


def __get_err_dir() -> str:
    return __get_var_or_default("ERR", "./err")


def get_input() -> dict:
    try:
        with open(get_input_dir() + "/input.json") as f:
            return json.load(f)
    except:
        return {}


def require_dependencies(**kwargs) -> dict:
    deps = {}
    resolved = {}
    have_deps = True
    in_dir = get_input_dir()

    for key in kwargs:
        deps[key] = kwargs[key].to_dict({})
        fname = in_dir + "/" + key
        if os.path.isfile(fname):
            resolved[key] = fname
        else:
            have_deps = False

    if have_deps:
        return resolved
    else:
        with open(__get_err_dir() + "/compute-deps.json", 'w') as f:
            json.dump({"dependencies": deps}, f)
        exit(2)


def report_progress(x: int, n: int = 100):
    if (n == 100):
        print("[PROGRESS %d%%]" % (x))
    else:
        print("[PROGRESS %d/%d]" % (x, n))


def fail(err: dict):
    with open(__get_err_dir() + "/error.json", "w") as f:
        json.dump(err, f)
    exit(1)
