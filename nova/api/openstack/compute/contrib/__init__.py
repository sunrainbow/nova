# Copyright 2011 Justin Santa Barbara
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Contrib contains extensions that are shipped with nova.

It can't be called 'extensions' because that causes namespacing problems.

"""

from oslo.config import cfg

from nova.api.openstack import extensions
from nova.openstack.common import log as logging

ext_opts = [
    cfg.ListOpt('osapi_compute_ext_list',
                default=[],
                help='Specify list of extensions to load when using osapi_'
                     'compute_extension option with nova.api.openstack.'
                     'compute.contrib.select_extensions'),
]

consolekeeper_opts = [
    cfg.StrOpt('consolekeeper_host',
                default='',
                help='consolekeeper_host'),
    cfg.StrOpt('consolekeeper_port',
                default='',
                help='consolekeeper_port'),
    cfg.IntOpt('consolekeeper_expiry_sec',
                default=0,
                help='consolekeeper_expiry_sec'),
    cfg.IntOpt('consolekeeper_interval_sec',
                default=0,
                help='consolekeeper_interval_sec'),
    cfg.IntOpt('suicide_sec',
                default=0,
                help='suicide_sec'),
]

CONF = cfg.CONF
CONF.register_opts(ext_opts)
CONF.register_opts(consolekeeper_opts, group='consolekeeper')

LOG = logging.getLogger(__name__)


def standard_extensions(ext_mgr):
    extensions.load_standard_extensions(ext_mgr, LOG, __path__, __package__)


def select_extensions(ext_mgr):
    extensions.load_standard_extensions(ext_mgr, LOG, __path__, __package__,
                                        CONF.osapi_compute_ext_list)
