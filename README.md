# Ecological State Protocol Specification

The primary building blocks of Ecological State Protocols (ESPs) are compute functionsand verification reports. Ideally 
these building blocks will be composed together into pipelines that allow for composition of different compute functions 
and protocols into larger protocols.

## Compute Functions

Compute functions are deterministic, side effect free pieces of code that can be executed in an ESP runner. That is 
they should produce the same output given the same input and not have any side effects like calling external web or 
database services. In the long run, we aim to make static type checking more of a first class concern. In the short 
term, we take advantage of existing informally specified technologies and take appropriate measures to ensure determinism. 

## Docker Compute Functions

Docker compute functions are the first type of compute function to be supported by runners. This is because docker has
become a fairly ubiquitous method for packaging a binary to be executed in a sandbox environment rather than th
technical superiority of docker over other potential methods.

### Requirements

In order to function as a well-behaved docker compute function, the docker image must adhere to the following conventions:

* The image expects the function input to be passed in as volume mounted as the file `/input.json`
* If the image can successful complete the computational task specified by the input in `/input.json`, it will return
  with a `0` exit code and place all output results as files in the `/out` folder.
* If the image depends on other compute functions, verification reports, or data sources and cannot complete because of
  missing dependencies, it will exit with the exit code `2` and specify any required dependencies in the
 `/compute-deps.json` file specified below. The image expects that any files already placed in `/out` will be saved by
  the runner and remounted in that volume when the runner calls the compute function again with resolved dependencies.
* The image expects any dependencies that are resolved by the runner to be placed in the `/input` folder.
* The image *SHOULD* allow itself to be pre-empted by the `SIGINT` signal. If the container is able to shutdown
  after receiving `SIGINT`, without `SIGKILL` needing to be called on the process, the contents of the `/out`
  folder will be saved by the runner (if possible) and the process will be restarted at some later point
  with the contents of `/out` restored for the process to complete. Only work items which the process can use to recover
  where it was working should be placed in the `/out` folder. Processes which involve multiple steps should check
  the `/out` folder and attempt to restart where they last left off. In order to accomplish this behavior successfully
  programs should install shutdown handlers with their runtime. If `SIGKILL` needs to be called on a process, it is
  assumed that the program didn't have time to complete its shutdown handlers and is thus in a dirty state. The process
  will then be restarted with whatever was the previously saved state and this unclean state will be ignored.
* If computation cannot complete successfully for any reason and a retry will not be useful, the container should exit
  with code `1` and place error metadata in the file `/error.json`.
* Processes can indicate progress to completion by placing message lines that conform to the format `[PROGRESS XX%]`
  (where `XX` are numbers representing percent completion) or `[PROGRESS X/N]` (where `X` is the current step number
  and `N` is the total number of steps) on `stdout`. Runners may or may not use this information.
* Any other arelevant logging messages should be placed on `stdout` and `stderr` but these will be used for debugging purposes only.

### `compute-deps.json` specification

The JSON schema for `compute-deps.json` is described in [./compute-deps.schema.json](./compute-deps.schema.json)

A few example `compute-deps.json` files:

Sample sentinel-2 satellite imagery dependency:

```json
{
  "dependencies":{
    "image1":{
      "type":"data:sentinel-2",
      "UTM_ZONE":33,
      "LATITUDE_BAND":"U",
      "GRID_SQUARE":"UP",
      "GRANULE_ID":"S2A_MSIL1C_20150704T101337_N0202_R022_T33UUP_20160606T205155.SAFE"
    }
  }
}
```

Sample compute task dependency:

```json
{
  "dependencies":{
    "processedImage":{
      "type":"compute:docker",
      "image":"example.com/preprocess-sentinel:0.1@sha256:45b23dee08af5e43a7fea6c4cf9c25ccf269ee113168c19722f87876677c5cb2"
      "input":{
        "polygon":{
        "type": "Polygon",
        "coordinates": [
          [[-71.47705078125, 38.59970036588819], [-68.09326171875, 38.59970036588819], [-68.09326171875, 40.54720023441049], [-71.47705078125, 40.54720023441049], [-71.47705078125, 38.59970036588819]]]
        }
      }
    }
  }
}
```

`compute-deps.json` should contain a JSON object with the properties described below.


#### `dependencies`

A map of keys to dependency objects. The keys in this map should point to the disk file locations where the compute 
function can expect these dependencies to be mounted in the `/input` directory upon the next invocation. For example, 
the two examples above would expect dependencies to be mounted in `/input/image1` and `/input/processedImage` respectively.

The type tag of the dependency object describes the type of dependency. The following dependency types are available.

##### `compute:docker`

A compute function described by a docker image as specified in [Docker Compute Functions](#docker-compute-functions). 
The compute function dependency must contain the following properties:

* `type`: The string literal `"compute:docker"`
* `image`: The docker image URL for the compute function.
  This URL **MUST** contain an [SHA256 digest](https://docs.docker.com/engine/reference/commandline/pull/#pull-an-image-by-digest-immutable-identifier)
  (can be disabled in development mode).
* `input`: The input object the compute function is to be passed as `/input.json`


##### `data:sentinel-2`

Specifies a Sentinel 2 satellite image resource. The following properties are required:

* `type`: The string literal `"data:sentinel-2"`
* `UTM_ZONE`
* `LATITUDE_BAND`
* `GRID_SQUARE`
* `GRANULE_ID`
