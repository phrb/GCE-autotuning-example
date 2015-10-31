#! /usr/env/python

from subprocess import call

repo = "--repo=https://github.com/phrb/GCE-autotuning-example.git"
project = "--project=just-clover-107416"
interface_path = "--interface-path=rosenbrock.py"
interface_name = "--interface-name=Rosenbrock"
parallelism = "--parallelism=4"

cmd = "python rosenbrock.py {0} {1} {2} {3} {4}".format(repo,
                                                        project,
                                                        interface_path,
                                                        interface_name,
                                                        parallelism)

print cmd

retcode = call(cmd, shell=True)
