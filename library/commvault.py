# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# --------------------------------------------------------------------------


ANSIBLE_METADATA = {"metadata_version": "11.16.0"}

DOCUMENTATION = """

module: commvault

short_description: To perform commvault operations

description:

    - Ansible Commvault module can be used in playbooks to perform commvault operations

    - Commvault module uses CVPySDK to perform operations

    - CVPySDK, in turn, uses Commvault REST API to perform operations on a Commcell via WebConsole.

author: "Commvault Systems, Inc."

options:

    operation:
        description:
            - operation to be performed
            - corresponds to method name in CVPySDK modules
            - example "restore_in_place" method is in subclient module

        required: true

        choices:
            - Login
            - CVPySDK methods like backup, restore_in_place

        type: str

    entity:
        description:
            -  contain basic CVPySDK inputs

        required: false

        default: {}

        choices:
            - client
            - clientgroup
            - agent
            - instance
            - backupset
            - subclient
            - job_id

        type: dict

    commcell:
        description:
            -   mandatory to perform any tasks, when performing login operation commcell is registered

        required: true

    entity_type:
        description:
            -   corresponds to baisc CVPySDK class

        required: false

        default: ''

        choices:
            - Commcell
            - Clients
            - Client
            - Clientgroups
            - Clientgroup
            - Agents
            - Agent
            - Instances
            - Instance
            - Backupsets
            - Backupset
            - Subclients
            - Subclient
            - Job

        type: str

    args:
        description:
            -   arguments to be passed to the CVPySDK methods

        required: false

        default: {}

        type: dict

requirements:

    - Ansible

    - Python 2.7 or above

    - CVPySDK

    - Commvault Software v11 SP16 or later release with WebConsole installed

"""

EXAMPLES = """
**Login to Commcell:**

      - name: Login
        commvault:
            operation: login
            entity: {
            webconsole_hostname: "{{ webconsole_hostname }}",
            commcell_username: "{{ commcell_username }}",
            commcell_password: "{{ commcell_password }}"
            }
        register: commcell

**Run backup for a subclient:**

      - name: Backup
        commvault:
                operation: "backup"
                entity_type: subclient
                commcell: "{{ commcell }}"
                entity: {
                    client: "client name",
                    agent: "file system",
                    backupset: "defaultbackupset",
                    subclient: "default"
                }
        register: backup_job

**Run restore in place job for a subclient:**

     - name: Restore
       commvault:
            operation: "restore_in_place"
            entity_type: subclient
            commcell: "{{ commcell }}"
            entity: {
                client: "client name",
                agent: "file system",
                backupset: "defaultbackupset",
                subclient: "default"
            }
            args: {
                paths: ['path']
            }
       register: restore_job
          
**Wait for the restore job to complete:**

      - name: wait for restore job to complete
        commvault:
            operation: "wait_for_completion"
            entity_type: "job"
            commcell: "{{ commcell }}"
            entity: {
                job_id: "{{ restore_job.output }}"
            }
        register: restore_status

"""

RETURN = """

return name: output

returned: always

sample: {
            output: "output of operation"
        }

"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text
from cvpysdk.commcell import Commcell
from cvpysdk.exception import SDKException
from cvpysdk.job import Job
import typing  # noqa F401
from typing import Optional


commcell = (
    client
) = (
    clients
) = (
    agent
) = (
    agents
) = instance = instances = backupset = backupsets = subclient = subclients = None

clientgroups = clientgroup = job = jobs = None


def login_token(webconsole_hostname: str, authtoken: str):
    """
    sign in the user to the commcell with token provided

    Args:
        webconsole_hostname (str)   -- the hostname of webconsole
        authtoken (str)   -- the authtoken

    """
    params = {"webconsole_hostname": webconsole_hostname, "authtoken": authtoken}

    return Commcell(**params)


def login_username_password(
    webconsole_hostname: str, commcell_username: str, commcell_password: str
):
    """
    sign in the user to the commcell with the credentials provided

    Args:
        webconsole_hostname (str)   -- the hostname of webconsole
        commcell_username (str)   -- the username to login with
        commcell_password (str)   -- the password to login with
    """
    params = {
        "webconsole_hostname": webconsole_hostname,
        "commcell_username": commcell_username,
        "commcell_password": commcell_password,
    }

    return Commcell(**params)


def create_object(entity: dict, commcell_object: Commcell):
    """
    To create the basic commvault objects

    entity  (dict)  -- basic commvault object names

        Example:
            {
                client: "",
                agent: "",
                instance: ""
                backupset: "",
                subclient: ""
            }

    """
    global commcell, client, clients, agent, agents, instance, instances, backupset, backupsets, subclient, subclients, clientgroup, clientgroups
    global job, jobs

    commcell = commcell_object
    clients = commcell_object.clients
    clientgroups = commcell_object.client_groups
    jobs = commcell_object.job_controller

    if "client" in entity:

        client = clients.get(entity["client"])
        agents = client.agents

        if "agent" in entity:
            agent = agents.get(entity["agent"])
            instances = agent.instances
            backupsets = agent.backupsets

            if "instance" in entity:
                instance = instances.get(entity["instance"])
                subclients = instance.subclients

            if "backupset" in entity:
                backupset = backupsets.get(entity["backupset"])
                subclients = backupset.subclients

            if subclients and "subclient" in entity:
                subclient = subclients.get(entity["subclient"])

    if "job_id" in entity:
        job = jobs.get(entity["job_id"])
    if "clientgroup" in entity:
        clientgroup = clientgroups.get(entity["clientgroup"])


def main():
    """Main method for this module"""
    module_args = dict(
        operation=dict(type="str", required=True),
        entity=dict(type="dict", default={}),
        entity_type=dict(type="str", default=""),
        commcell=dict(type="dict", default={}, no_log=True),
        args=dict(type="dict", default={}),
    )
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    result = dict()

    entity = module.params.get("entity")
    entity_type = module.params.get("entity_type")
    commcell_args = module.params.get("commcell")

    if module.params["operation"].lower() == "login":
        try:
            commcell_auth = login_username_password(**entity)
            result["changed"] = True
            result["webconsole_hostname"] = commcell_auth.webconsole_hostname
            result["authtoken"] = commcell_auth.auth_token
        except SDKException as sdk_exception:
            result["failed"] = True
            module.fail_json(msg=to_text(sdk_exception), **result)
    else:
        try:
            if (
                "webconsole_hostname" not in commcell_args
                and "authtoken" not in commcell_args
            ):
                module.fail_json(
                    msg="You either need to login with operation 'login' or provide 'webconsole_hostname' and 'authtoken' in commcell"
                )

            commcell_auth = login_token(
                commcell_args.get("webconsole_hostname"), commcell_args.get("authtoken")
            )
            _ = create_object(entity, commcell_auth)
        except SDKException as sdk_exception:
            result["failed"] = True
            module.fail_json(msg=to_text(sdk_exception), **result)

        obj_name = entity_type
        obj = eval(obj_name)
        method = module.params["operation"]

        if not hasattr(obj, method):
            obj_name = "{0}s".format(entity_type)
            obj = eval(obj_name)

        statement = "{0}.{1}".format(obj_name, method)
        attr = getattr(obj, method)

        if callable(attr):
            if module.params.get("args"):
                args = module.params["args"]
                statement = "{0}(**{1})".format(statement, args)
            else:
                statement = "{0}()".format(statement)
        else:
            if module.params.get("args"):
                statement = '{0} = list(module.params["args"].values())[0]'.format(
                    statement
                )
                try:
                    _ = exec(statement)
                    result["output"] = "Property set successfully"
                    module.exit_json(**result)
                except SDKException as sdk_exception:
                    result["failed"] = True
                    module.fail_json(msg=to_text(sdk_exception), **result)

        try:
            output = eval(statement)
        except SDKException as sdk_exception:
            result["failed"] = True
            module.fail_json(msg=to_text(sdk_exception), **result)            

        if type(output).__module__ in ["builtins", "__builtin__"]:
            result["output"] = output
        elif isinstance(output, Job):
            result["output"] = output.job_id
        else:
            result["output"] = str(output)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
