#!/usr/bin/env python
import sys
import os
import yaml

_RET = 0

for root, dirs, files in os.walk('./Yaml-Data'):
    for filename in files:
        if filename.endswith('.yml'):
            yamlfile = os.path.join(root, filename)

            try:
                yaml.safe_load(open(yamlfile))
                print("===> {} Successfully Loaded".format(yamlfile))
            except Exception as err:
                _RET += 1
                print("===> {} fail to Load")
                print(err)

if _RET:
    sys.exit(_RET)
