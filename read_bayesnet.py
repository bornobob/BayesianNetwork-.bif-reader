"""
A .bif file reader using regular expressions
Currently only supports discrete domains
Freely usable and extensible

Author: Bob Ruiken
"""

import re
from pathlib import Path

# The regular expressions to parse the .bif file
NETWORK_RE = r' *network +((?:[^{]+ +)*[^{ ]+) *{\n+ *}'
VAR_RE = r' *variable +([^{ ]+) +{\n+ *type +(?:discrete|) +\[ +(\d+) +\] *{ *([a-zA-Z, 0-9]+)};\n+ *}'
PROB_RE = r' *probability +\( *(?P<var>[^ ]+) *(?:\| *(?P<parents>[^\)]+))?\) *{\n([^}]+)\n *}'
TABLE_RE = r' *table +([^;]+) *;'
PARENTS_RE = r' *\(([^\)]+)\) +([^;]+) *;'

FLAGS = re.RegexFlag.M  # Multi line flag

# Compiling the regular expressions with the flags
network_re = re.compile(NETWORK_RE, flags=FLAGS)
var_re = re.compile(VAR_RE, flags=FLAGS)
prob_re = re.compile(PROB_RE, flags=FLAGS)
table_re = re.compile(TABLE_RE, flags=FLAGS)
parents_re = re.compile(PARENTS_RE, flags=FLAGS)


class Variable:
    """
    A simple class to save variables into
    """
    def __init__(self, name, domain):
        self.name = name
        self.domain = domain
        self.probabilities = {}
        self.parents = []
        self.table = ()

    def get_probability(self, assignment):
        """
        Returns the probability tuple for assignment given.
        For example, if the variable has one parent with domain ['True', 'False'], the parameter assignment should
        either look like ['True', 'True'].
        :param assignment: the assignment you want to get the probabilities for
        :return: the probabilities for the assignment or KeyError if the assignment is not found
        """
        key = tuple(assignment)
        if key in self.probabilities.keys():
            return self.probabilities[key]
        else:
            raise KeyError('Key ({}) is not an assignment for this variable.'.format(key))


class BayesianNetwork:
    """
    The BayesianNetwork class stores the variables and can read a network from a .bif file
    """
    def __init__(self, file):
        self.file = file
        self.name = ''
        self.variables = []
        self.parse_file()

    def parse_file(self):
        """
        Parses the supplied file in the init function
        """
        # Read in the entire file
        contents = Path(self.file).read_text()

        # Find the name of the network
        self.parse_network(contents)

        # Find all the variables
        self.parse_variables(contents)

        # Find all the probabilities
        self.parse_probabilities(contents)

    def parse_network(self, content):
        """
        Parses the network portion of the .bif file
        :param content: the content of the .bif file
        """
        network = network_re.match(content)
        try:
            self.name = network.group(1)
        except IndexError:
            self.name = 'Unnamed network'

    def parse_variables(self, content):
        """
        Parses the variables of the .bif file
        :param content: the content of the .bif file
        """
        variables = var_re.findall(content)
        for _name, _, _values in variables:
            domain = [x.strip() for x in _values.split(',')]
            self.variables.append(Variable(_name, domain))

    def parse_probabilities(self, content):
        """
        Parses the probabilities of the .bif file
        :param content: the content of the .bif file
        """
        probabilities = prob_re.findall(content)
        for _name, _parents, _probabilities in probabilities:
            if _parents:
                values = parents_re.findall(_probabilities)
                parents = [x.strip() for x in _parents.split(',')]
                var = self.get_variable(_name)
                var.parents = parents
                for val in values:
                    key = tuple([v.strip() for v in val[0].split(',')])
                    prob = tuple([float(v.strip()) for v in val[1].split(',')])
                    var.probabilities[key] = prob
            else:
                value = table_re.match(_probabilities)
                var = self.get_variable(_name)
                var.table = tuple(float(v.strip()) for v in value.group(1).split(','))

    def get_variable(self, name):
        """
        Returns the instance of the Variable class with name: name
        :param name: the name of the sought variable
        :return: the Variable instance
        """
        for var in self.variables:
            if var.name == name:
                return var


# bn = BayesianNetwork(file='earthquake.bif')  # example usage for the supplied earthquake.bif file
# print(bn.get_variable('JohnCalls').get_probability(['True'])[0])
