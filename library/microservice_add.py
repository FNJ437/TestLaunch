#!/usr/bin/python
##=================================================================
#
# Copyright Motorola Solutions, Inc. and/or Kodiak Networks, Inc.
# All Rights Reserved
# Motorola Solutions Confidential Restricted
#
##=================================================================

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
from collections import defaultdict
from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = r'''
---
module: microservice_add

short_description: This custom module will be used to diff the MCS card already added in EMS and
                   MCS cards which is yet to be added in EMS

options:
    remote_data:
        description: This is networkmap data which contains the info of cards which are
                     already added in EMS.
        required: true
        type: list
    local_data:
        description:
            - This data contains the data from microservices.yml file.
        required: true
        type: list
    remote_config:
        description:
            - This data contains the remote mcs configuration data (required to fetch version).
        required: true
        type: list
'''

Servicetype = {'Sync-Gateway': 'SYNCGW','Sync-Gateway-Replicator': 'SYNCGWREP' , 'Couchbase-server': 'CBS',
                  'RabbitMQ': 'RMQ', 'KPNS Server': 'KPNS', 'LCMS Server': 'LCMS', 'fds': 'FDS',
                  'PlatformAuditService': 'PlatformAuditSvc', 'IDAPElasticSearch': 'IDAPElasticsrch',
                  'IDAPDashboardService': 'IDAPDshboard', 'UGWDataGWAffiliation': 'UGWGWAffiliation',
               'UGWDataGWLocation': 'UGWGWLocation', 'UGWDataGWPresence': 'UGWGWPresence',
               'NNI GW UGW Container': 'UGWWebserver'}


def create_remote_data_card_dict(remote_card_data, remote_card_config):
    remote_card_dict = defaultdict(int)
    remote_card_config_dict = {}

    # loop through service configuration data to get the version of each added card
    for card_config in remote_card_config:
        if card_config:
            remote_card_config_dict[card_config['SIGNALINGCARD_NAME']] = card_config['SERVICEVER']

    # loop through the network map data to get the count of MCS cards that are already added in EMS
    for card in remote_card_data:
        version = remote_card_config_dict.get(card['cardDetails'][0]['SIGNALINGCARD_NAME'])
        if not version:
            continue
        if card['cardDetails'] and card['cardDetails'][0]['CONTAINERNAME'] in Servicetype:
            card_dict_key = Servicetype[card['cardDetails'][0]['CONTAINERNAME']] + "-" + card[
                'cardDetails'][0]['CLUSTERID'] + "-" + card['cardDetails'][0]['CHASSISID'] + "-" + version
        else:
            card_dict_key = card['cardDetails'][0]['CONTAINERNAME'] + "-" + card['cardDetails'][0][
                'CLUSTERID'] + "-" + card['cardDetails'][0]['CHASSISID'] + "-" + version if card['cardDetails'] else ''
        if card_dict_key:
            remote_card_dict[card_dict_key] += 1

    return remote_card_dict


def create_local_data_card_dict(local_card_data):
    local_card_dict = defaultdict(int)

    # loop through the user provided card data that is required to be added in EMS
    for data in local_card_data:
        for card in data['containers']:
            card_dict_key = card['name'] + "-" + str(data['clusterid']) + "-" + str(data['chassisid']) + "-" + card['version']
            local_card_dict[card_dict_key] += 1

    return local_card_dict


def create_final_count_dict(local_card_data_dict, remote_card_data_dict):

    # get the diff of count between the card already added in EMS and card which is left to be added.
    for card_key, local_count in local_card_data_dict.items():
        remote_count = remote_card_data_dict[card_key]
        new_count = local_count - remote_count
        # below check is added if more cards are added manually than what is expected then count will
        # taken as zero
        new_count = new_count if new_count >= 0 else 0
        local_card_data_dict[card_key] = new_count

    return local_card_data_dict


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        remote_data=dict(type='list', required=True),
        local_data=dict(type='list', required=True),
        remote_config=dict(type='list', required=True)
    )

    result = dict(
        changed=False,
        local_card_count={},
        remote_card_count={}
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    remote_data = module.params['remote_data']
    remote_config = module.params['remote_config']
    remote_card_count_dict = create_remote_data_card_dict(remote_data, remote_config)

    local_data=module.params['local_data']
    local_card_count_dict = create_local_data_card_dict(local_data)

    final_local_card_count = create_final_count_dict(local_card_count_dict, remote_card_count_dict)

    result['remote_card_count'] = remote_card_count_dict
    result['local_card_count'] = final_local_card_count

    if module.params['remote_data']:
        result['changed'] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
