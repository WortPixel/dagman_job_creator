# DAGman Job Creator
This script can be used to create [DAGman](https://research.cs.wisc.edu/htcondor/dagman/dagman.html) jobs from a config file. The templates for all files created during the process can be found in the `resources` folder.

## Usage
Provide a `init` file like the example config in `resources/config.ini`.

Run `python create_jobs.py /path/to/config.ini`.

This will create a folder named after the provided job name, with a copy of the `init` file for reproducability. Inside this folder folders for each dataset are created. A dataset number is the combination of the `particle_type` and the `systematics` value.

Within the `job` section number of jobs to submit per interval and max jobs to submit in total are given, as well as the overall DAGman job name. The DAGman job limitations are stored in a `dagman.config` file.

`data` provides information about the given input filename syntax for all files in `settings.inputfile`. As well as a desired output syntax using elements from the input syntax. Elements not found in the input syntax are used literaly.

All values provided in the `settings` section are passed as options to the `process.executable`, thus creating a list of all options for DAGman in a `options.dag` file.

The `process` section is used to define the used software environment, keep track of the used code and its commit version, as well as the actual program to execute. This results in a `OneJob.submit` file.

A job created with this script can be started via
```python
condor_submit_dag -config dagman.config -notification Complete options.dag
```
