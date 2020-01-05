# Brightway parameters

[![Coverage Status](https://coveralls.io/repos/github/dgdekoning/bw-parameters/badge.svg?branch=master)](https://coveralls.io/github/dgdekoning/bw-parameters?branch=master) [![Build status](https://ci.appveyor.com/api/projects/status/74g4vih17u45e33y?svg=true)](https://ci.appveyor.com/project/dgdekoning/bw-parameters)
 [![Documentation Status](https://readthedocs.org/projects/brightway2-parameters/badge/?version=latest)](http://brightway2-parameters.readthedocs.io/?badge=latest)

Library for storing, validating, and calculating with parameters. Designed to work with the [Brightway2 life cycle assessment framework](https://brightwaylca.org), but is generic enough to work in other use cases.

    In [1]: from bw2parameters import ParameterSet

    In [2]: parameters = {
       ...:        'Deep_Thought': {'amount': 42},
       ...:        'East_River_Creature': {'formula': '2 * Deep_Thought + 16'},
       ...:        'Elders_of_Krikkit': {'formula': 'sqrt(East_River_Creature)'},
       ...: }

    In [3]: ParameterSet(parameters).evaluate()
    Out[3]: {'Deep_Thought': 42, 'East_River_Creature': 100, 'Elders_of_Krikkit': 10.0}

Compatible with Python 2.7, 3.5 and up. 100% test coverage. [Source code on github](https://github.com/dgdekoning/bw-parameters), documentation on [Read the Docs](https://brightway2-parameters.readthedocs.io/).

## Moving to Github and future development

This fork of the [`bw2parameters`](https://bitbucket.org/cmutel/brightway2-parameters) repository reflects the intention
to create a stand-alone (brightway) parameter creation, recalculating and storage package that can be used by the
[Brightway LCA project](https://github.com/brightway-lca) while also providing the same functionality for unrelated
projects.

As part of this the [parameter-related code](https://bitbucket.org/cmutel/brightway2-data/src/default/bw2data/parameters.py)
currently present in the `bw2data` [package](https://bitbucket.org/cmutel/brightway2-data) will be extracted and
implemented in this 'new' `bw-parameters` package.
