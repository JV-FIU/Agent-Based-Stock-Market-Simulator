import argparse
import importlib
import sys
'''
if __name__ == '__main__':

  # Print system banner.
  system_name = "ABIDES: Agent-Based Interactive Discrete Event Simulation"

  print ("=" * len(system_name))
  print (system_name)
  print ("=" * len(system_name))
  print ()

  # Test command line parameters.  Only peel off the config file.
  # Anything else should be left FOR the config file to consume as agent
  # or experiment parameterization.
  parser = argparse.ArgumentParser(description='Simulation configuration.')
  parser.add_argument('-c', '--config', required=True,
                      help='Name of config file to execute')
  parser.add_argument('--config-help', action='store_true',
                    help='Print argument options for the specific config file.')

  args, config_args = parser.parse_known_args()

  # First parameter supplied is config file.
  config_file = args.config

  config = importlib.import_module('config.{}'.format(config_file),
                                   package=None)
'''



if __name__ == '__main__':

  # Print system banner.
  system_name = "ABIDES: Agent-Based Interactive Discrete Event Simulation"

  print ("=" * len(system_name))
  print (system_name)
  print ("=" * len(system_name))
  print ()

  # Test command line parameters.  Only peel off the config file.
  # Anything else should be left FOR the config file to consume as agent
  # or experiment parameterization.
  parser = argparse.ArgumentParser(description='Simulation configuration.')
  parser.add_argument('-c', '--config', required=True,
                      help='Name of config file to execute')
  parser.add_argument('--config-help', action='store_true',
                    help='Print argument options for the specific config file.')
  
  print("Length of sys.argv is ", len(sys.argv))
  sys.argv.append("-c")
  sys.argv.append("UwU")
  sys.argv.append("-t")
  sys.argv.append("IBM")
  sys.argv.append("20200603")
  sys.argv.append("-s")
  sys.argv.append("12")
  sys.argv.append("-l")
  sys.argv.append("rmsc03_X")
  print("New length of sys.argv is ", len(sys.argv))
  args, config_args = parser.parse_known_args()

  # First parameter supplied is config file.
  
  print("Argument 0", sys.argv[0])
  print("Argument 1", sys.argv[1])
  print("Argument 2", sys.argv[2])
  sys.argv[2] = "rmsc03"
  print("New Argument 2", sys.argv[2])
  config_file = args.config
  print("Config file: ", config_file)
  config_file = "rmsc03"
  print("New config_file: ", config_file)

  config = importlib.import_module('config.{}'.format(config_file),
                                   package=None)
