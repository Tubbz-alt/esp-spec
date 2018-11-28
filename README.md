# Ecological State Protocol Specification

The primary building blocks of Ecological State Protocols (ESPs) are compute functionsand verification reports. Ideally these building blocks will be composed together into pipelines that allow for composition of different compute functions and protocols into larger protocols.

## Compute Functions

Compute functions are deterministic, side effect free pieces of code that can be executed in an ESP runner. That is they should produce the same output given the same input and not have any side effects like calling external web or database services. In the long run, we aim to make static type checking more of a first class concern. In the short term, we take advantage of existing informally specified technologies and take appropriate measures to ensure determinism. 

## Docker Compute Functions

Docker compute functions are the first type of compute function to be supported by runners. This is because docker has become a fairly ubiquitous method for packaging a binary to be executed in a sandbox environment rather than the technical superiority of docker over other potential methods.

### Requirements

In order to function as a well-behaved docker compute function, the docker image must adhere to the following conventions:

* The image expects the function input to be passed in as volume mounted as the file `/input.json`
* If the image can successful complete the computational task specified by the input in `/input.json`, it will return with a `0` exit code and place all output results as files in the `/out` folder.
* If the image depends on other compute functions, verification reports, or data sources and cannot complete because of missing dependencies, it will exit with the exit code `2` and specify any required dependencies in the `/compute-deps.json` file specified below. The image expects that any files already placed in `/out` will be saved by the runner and remounted in that volume when the runner calls the compute function again with resolved dependencies.
* The image expects any dependencies that are resolved by the runner to be placed in the `/input` folder.
* The image *SHOULD* allow itself to be pre-empted with the `SIGINT` signal. The running container will be given an unspecified number of seconds to complete processing, but should attempt to exit as soon as possible. If computation has completed successfully the container should exit with `0` as usual. If computation can continue later, the container should exit with `2` as above. If computation can continue later, but no new dependencies are needed, the container should exit with `3` and the runner will attempt to cache any files in `/out` for the next invocation.
* If computation cannot complete successfully for any reason and a retry will not be useful, the container should exit with code `1` and place error metadata in the file `/error.json`.
* Any relevant logging messages should be placed on `stdout` and `stderr` but these will be used for debugging purposes only.

### `compute-deps.json` specification

