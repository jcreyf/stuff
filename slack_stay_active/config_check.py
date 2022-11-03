#!/usr/bin/env python3
# ------------------------------------------------------
# YAML schema validation:
#   https://docs.python-cerberus.org/en/stable/
# Normalization rules:
#   https://docs.python-cerberus.org/en/stable/normalization-rules.html
#
# /> conda install -c conda-forge cerberus
#      The following packages will be downloaded:
#        package                    |            build
#        ---------------------------|-----------------
#        ca-certificates-2022.10.11 |       h06a4308_0         124 KB
#        cerberus-1.3.4             |     pyhd8ed1ab_0          51 KB  conda-forge
#        certifi-2022.9.24          |     pyhd8ed1ab_0         155 KB  conda-forge
#        openssl-1.1.1q             |       h7f8727e_0         2.5 MB
#        ------------------------------------------------------------
#        Total:         2.8 MB
# ------------------------------------------------------

import yaml
from cerberus import Validator

_configFile = './slack_active.yaml'
_schemaFile = './config.schema'

def load_doc():
    with open(_configFile, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exception:
            raise exception


## Now, validating the yaml file is straightforward:
schema = eval(open(_schemaFile, 'r').read())
v = Validator(schema, purge_unknown=True)
doc = load_doc()
print(doc)
print("---------")
print(v.validate(doc))
print(v.errors)
print("---------")
print(v.normalized(doc))