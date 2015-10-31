#!/usr/bin/env python

import argparse
import logging

import opentuner
from opentuner.measurement import MeasurementInterface, MeasurementDriver
from opentuner.search.manipulator import ConfigurationManipulator
from opentuner.search.manipulator import FloatParameter
from GCEInterface.interface import GCEInterface

log = logging.getLogger(__name__)

parser = argparse.ArgumentParser(parents=opentuner.argparsers())
parser.add_argument('--dimensions', type=int, default=2,
                    help='dimensions for the Rosenbrock function')
parser.add_argument('--domain', type=float, default=1000,
                    help='bound for variables in each dimension')
parser.add_argument('--function', default='rosenbrock',
                    choices=('rosenbrock', 'sphere', 'beale'),
                    help='function to use')
parser.add_argument('--zone',
                    type     = str,
                    default  = "us-central1-f",
                    help     = "The GCE zone.")
parser.add_argument('--project',
                    type     = str,
                    required = True,
                    help     = "The GCE project.")
parser.add_argument('--repo',
                    type     = str,
                    required = True,
                    help     = "The git repository with the tuner.")
parser.add_argument('--interface-path',
                    type     = str,
                    required = True,
                    help     = "The path of your tuner in the repository.")
parser.add_argument('--interface-name',
                    type     = str,
                    required = True,
                    help     = "The name of your measurement interface.")

class MeasurementClient(MeasurementDriver):
  def __init__(self,
               measurement_interface,
               input_manager,
               **kwargs):
    super(MeasurementClient, self).__init__(measurement_interface,
                                            input_manager,
                                            **kwargs)

    print self.args
    self.gce_interface = GCEInterface(zone            = self.args.zone,
                                      project         = self.args.project,
                                      repo            = self.args.repo,
                                      interface_path  = self.args.interface_path,
                                      interface_name  = self.args.interface_name,
                                      instance_number = self.args.parallelism)

    self.gce_interface.create_and_connect_all()

  def process_all(self):
    self.lap_timer()
    q = self.query_pending_desired_results()
    desired_results = []

    for dr in q.all():
      if self.claim_desired_result(dr):
        desired_results.append(dr)

    self.run_desired_results(desired_results)

  def run_desired_results(self, desired_results):
    requests = []

    for desired_result in desired_results:
      desired_result.limit = self.run_time_limit(desired_result)

      input = self.input_manager.select_input(desired_result)
      self.session.add(input)
      self.session.flush()

      log.debug('running desired result %s on input %s', desired_result.id,
                input.id)

      self.input_manager.before_run(desired_result, input)

      requests.append((desired_result.configuration,
                       input,
                       desired_result.limit))

    results = self.gce_interface.compute_results(requests)

    for result, d_result, request in zip(results, desired_results, requests):
      input = request[1]
      self.report_result(d_result, result, input)

class Rosenbrock(MeasurementInterface):
    def run(self, desired_result, input, limit):
        cfg = desired_result.configuration.data
        val = 0.0
        x0 = cfg[0]
        x1 = cfg[1]
        val += 100.0 * (x1 - x0 ** 2) ** 2 + (x0 - 1) ** 2
        return opentuner.resultsdb.models.Result(time=val)

    def manipulator(self):
        manipulator = ConfigurationManipulator()
        for d in xrange(self.args.dimensions):
            manipulator.add_parameter(FloatParameter(d,
                                                     -self.args.domain,
                                                     self.args.domain))
        return manipulator

    def program_name(self):
        return self.args.function

    def program_version(self):
        return "%dx%d" % (self.args.dimensions, self.args.domain)

    def save_final_config(self, configuration):
        """
        called at the end of autotuning with the best resultsdb.models.Configuration
        """
        print "Final configuration", configuration.data

    @classmethod
    def main(cls, args, *pargs, **kwargs):
        from opentuner.tuningrunmain import TuningRunMain
        return TuningRunMain(cls(args, *pargs, **kwargs), args,
                             measurement_driver = MeasurementClient).main()


if __name__ == '__main__':
    args = parser.parse_args()
    if args.function == 'beale':
        # fixed for this function
        args.domain = 4.5
        args.dimensions = 2
    Rosenbrock.main(args)

