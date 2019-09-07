#!/usr/bin/env python
import sys
import os
import yaml
import re
import collections, collections.abc
from voluptuous import Any, Schema, Required, Optional, MultipleInvalid, Invalid, Match

import json
import requests
import socket

print('Static schema to test')

destination = {
    Required('DestinationEnvironment'): Any('EC', 'IR500', 'DLA'),
    Required('DestinationPOPGroup'): Any('Back Office', 'Lab', 'Border Router', 'Corporate Office', 'MCDN', 'Storage',
                                         'Streaming', 'Edge', 'Internet', 'Internet Block', 'NAT', 'Staging',
                                         'Internal Staging'),
    Required('DestinationNetworkGroup'): Any(None, str),
    Required('DestinationPOP'): [Any(None, str)],
    Required('DestinationPurpose'): Any(None, str),
    Required('DestinationSubPurpose'): Any(None, str),
    Required('DestinationVIP'): Any(None, int),
    Required('DestinationVLAN'): [Any(None, str)],
    Required('DestinationProtocol'): [Any(str)],
    Required('DestinationPort'): [Any('any', int, None, Match(r'^[0-9- ]+$'))],
    Required('DestinationHostname'): Any(None, str)
}
source = {
    Required('SourceEnvironment'):  Any('EC', 'IR500', 'DLA'),
    Required('SourcePOPGroup'): Any('Back Office', 'Lab', 'Border Router', 'Corporate Office', 'MCDN', 'Storage',
                                    'Streaming', 'Edge', 'Internet', 'Internet Block', 'NAT', 'Staging',
                                    'Internal Staging'),
    Required('SourceNetworkGroup'): Any(None, str),
    Required('SourcePOP'): [Any(None, str)],
    Required('SourcePurpose'): Any(None, str),
    Required('SourceSubPurpose'): Any(None, str),
    Required('SourceVIP'): Any(None, int),
    Required('SourceVLAN'): [Any(None, str)],
    Required('SourcePort'): [Any('any', int, None, Match(r'^[0-9- ]+$'))],
    Required('SourceHostname'): Any(None, str)
}

acl = Schema({
    Required('Comments'): Any(None, str),
    Required('Destination'): destination,
    Required('Source'): source,
    Required('Tags'): list
})

ret = 0
changed_files = os.environ['CHANGED_FILES']
print("{0} file Modified ".format(changed_files))

for root, dirs, files in os.walk('./Yaml-Data'):
    for filename in files:
        if filename.endswith('.yml') and \
                not filename.startswith('.') and \
                filename != 'mkdocs.yml':
            if filename not in changed_files:
                print("Skpping unmodified file: {0}".format(filename))
                continue
            yamlfile = os.path.join(root, filename)
            yaml_content = None

            try:
                #yaml_content = yaml.load(open(yamlfile))
                yaml_content = yaml.safe_load(open(yamlfile))
                #print(yaml_content)
            except Exception as err:
                ret += 1
                print("===> {0} fail at yaml file loading".format(yamlfile))
                print(err)
                continue

            print("===> " + filename)
            yaml_content = yaml_content.get('EBO', yaml_content.get('EBY', None))
            #print(yaml_content)
            if not isinstance(yaml_content, dict):
                ret += 1
                print("===> fail at yaml file loading")
                continue

            duplicate_check = []
            for acl_name, acl_data in yaml_content["ACL"].items():
                # checking schema
                try:
                    print("----> ACL Name is {0}".format(acl_name))
                    name_pattern = re.compile("^(\D+)(\d+)$")
                    print(name_pattern.match(acl_name))
                    #print(acl(acl_data))
                    if name_pattern.match(acl_name) != None:
                        acl(acl_data)
                    else:
                        print("----> {0} ACL Name has Error and return None".format(acl_name))
                except MultipleInvalid as err:
                    for each in err.errors:
                        invalid_value = ""
                        if len(each.path) == 2:
                            invalid_value = acl_data[each.path[0]][each.path[1]]
                        if len(each.path) == 3:
                            invalid_value = acl_data[each.path[0]][each.path[1]][each.path[2]]
                        print("===> ACL Name: {} - {} - {}".format(acl_name, each, invalid_value))
                        ret += 1

                # warn duplicate ACL
                source_count = 0
                dest_count = 0
                for n, s, d in duplicate_check:
                    if (s, d) == (acl_data['Source'], acl_data['Destination']):
                        print("===> Possible duplicate acl {} and {}".format(acl_name, n))
                        # only warning until fixed
                        # ret += 1
                    #check hostname for valid fqdn or ip

                    if acl_data['Source']['SourceHostname']:
                        source_count += 1
                        import re
                        pat = re.compile("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
                        host_digits = pat.findall(acl_data['Source']['SourceHostname'])
                        if len(host_digits) > 0:
                            if not socket.inet_aton(acl_data['Source']['SourceHostname']):
                                print("===> Invalid Source hostname ip in acl {} and {}".format(acl_name, n))
                                ret += 1
                        else:
                            host_string = str(acl_data['Source']['SourceHostname']).find('/')
                            if host_string > 0:
                                ret += 1
                                print("===> Invalid Source hostname fqdn in acl {} and {}".format(acl_name, n))
                        if source_count >= 1024:
                            print("===> To Many Source, {0} or Destination {1} Hostnames: ".format(source_count, dest_count))
                            raise Exception("To Many Source, {0},  Hostnames ".format(source_count))
                    elif acl_data['Destination']['DestinationHostname']:
                        dest_count += 1
                        import re
                        pat = re.compile("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")

                        host_digits = pat.findall(acl_data['Destination']['DestinationHostname'])
                        if len(host_digits) > 0:
                            if not socket.inet_aton(acl_data['Destination']['DestinationHostname']):
                                print("===> Invalid Destination hostname ip in acl {} and {}".format(acl_name, n))
                                ret += 1
                        else:
                            host_string = str(acl_data['Destination']['DestinationHostname']).find('/')
                            if host_string > 0:
                                ret += 1
                                print("===> Invalid Destination hostname fqdn in acl {} and {}".format(acl_name, n))
                        if dest_count >= 1024:
                            print("===> To Many Destination {0} Hostnames ".format(dest_count))
                            raise Exception("To Many Source, {0},  Hostnames ".format(dest_count))
                else:
                    duplicate_check.append((acl_name, acl_data['Source'], acl_data['Destination']))
            # uberlint
            try:
                # TODO: SSL Verification
                content = yaml_content.get("ACL", {})

                if content == {}:
                    pass
                else:
                    requests.packages.urllib3.disable_warnings()
                    r = requests.post('https://aclengine.edgecastcdn.net/uberlint', data=json.dumps(yaml_content["ACL"]),
                                      verify=False)

                    if r.status_code == 200:
                        result = json.loads(r.text)
                        for k, v in result.items():
                            print("===> {}, {}".format(k,v))
                            ret += 1
                    else:
                        raise Exception(r.status_code)
            except Exception as err:
                print("===> Warning: uberlint api call failed: {}".format(err))

if ret:
    sys.exit(ret)
