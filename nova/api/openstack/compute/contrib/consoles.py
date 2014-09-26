# Copyright 2012 OpenStack Foundation
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

import webob

from nova.api.openstack import common
from nova.api.openstack import extensions
from nova.api.openstack import wsgi
from nova import compute
from nova import exception
from nova.i18n import _, _LW

from urlparse import urlparse
from oslo.config import cfg
from nova.openstack.common import memorycache
from nova.openstack.common import jsonutils
from nova.openstack.common import log as logging

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

authorize = extensions.extension_authorizer('compute', 'consoles')


class ConsolesController(wsgi.Controller):
    def __init__(self, *args, **kwargs):
        self.compute_api = compute.API()
        super(ConsolesController, self).__init__(*args, **kwargs)

        self.mc = memorycache.get_client()

    @wsgi.action('os-getVNCConsole')
    def get_vnc_console(self, req, id, body):
        """Get vnc connection information to access a server."""
        context = req.environ['nova.context']
        authorize(context)

        # If type is not supplied or unknown, get_vnc_console below will cope
        console_type = body['os-getVNCConsole'].get('type')
        instance = common.get_instance(self.compute_api, context, id,
                                       want_objects=True)

        try:
            output = self.compute_api.get_vnc_console(context,
                                                      instance,
                                                      console_type)
        except exception.InstanceNotReady as e:
            raise webob.exc.HTTPConflict(
                    explanation=_('Instance not yet ready'))
        except exception.ConsoleTypeUnavailable as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())
        except NotImplementedError:
            msg = _("Unable to get vnc console, functionality not implemented")
            raise webob.exc.HTTPNotImplemented(explanation=msg)

        return {'console': {'type': console_type, 'url': output['url']}}

    @wsgi.action('os-getVNCConsole-new')
    def get_vnc_console_new(self, req, id, body):
        body_dict = body['os-getVNCConsole-new']
        body = {'os-getVNCConsole': body_dict}

        vnc_console = self.get_vnc_console(req, id, body)
        vnc_console_url = vnc_console['console'].get('url')

        # parse url to get token, host, port
        parsed = urlparse.urlparse(vnc_console_url)
        vnc_host = parsed.hostname
        vnc_port = parsed.port
        param_dict = urlparse.parse_qs(parsed.query)
        token = param_dict["token"][0]

        token_dict = { 'consid': id,
                       'consolekeeper_host': CONF.consolekeeper.consolekeeper_host,
                       'consolekeeper_port': CONF.consolekeeper.consolekeeper_port,
                       'consolekeeper_expiry_sec': CONF.consolekeeper.consolekeeper_expiry_sec,
                       'consolekeeper_interval_sec': CONF.consolekeeper.consolekeeper_interval_sec,
                       'vnc_host': vnc_host,
                       'vnc_port': vnc_port,
                       'suicide_sec': CONF.consolekeeper.suicide_sec}
        data = jsonutils.dumps(token_dict)

        if not self.mc.set(token.encode('UTF-8'),
                           data):
            LOG.warning(_LW("Token: %(token)s failed to save into memcached."),
                            {'token': token})

        return vnc_console

    @wsgi.action('os-getSPICEConsole')
    def get_spice_console(self, req, id, body):
        """Get spice connection information to access a server."""
        context = req.environ['nova.context']
        authorize(context)

        # If type is not supplied or unknown, get_spice_console below will cope
        console_type = body['os-getSPICEConsole'].get('type')
        instance = common.get_instance(self.compute_api, context, id,
                                       want_objects=True)

        try:
            output = self.compute_api.get_spice_console(context,
                                                      instance,
                                                      console_type)
        except exception.ConsoleTypeUnavailable as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())
        except exception.InstanceNotReady as e:
            raise webob.exc.HTTPConflict(explanation=e.format_message())
        except NotImplementedError:
            msg = _("Unable to get spice console, "
                    "functionality not implemented")
            raise webob.exc.HTTPNotImplemented(explanation=msg)

        return {'console': {'type': console_type, 'url': output['url']}}

    @wsgi.action('os-getRDPConsole')
    def get_rdp_console(self, req, id, body):
        """Get text console output."""
        context = req.environ['nova.context']
        authorize(context)

        # If type is not supplied or unknown, get_rdp_console below will cope
        console_type = body['os-getRDPConsole'].get('type')
        instance = common.get_instance(self.compute_api, context, id,
                                       want_objects=True)

        try:
            output = self.compute_api.get_rdp_console(context,
                                                      instance,
                                                      console_type)
        except exception.ConsoleTypeUnavailable as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())
        except exception.InstanceNotReady as e:
            raise webob.exc.HTTPConflict(explanation=e.format_message())
        except NotImplementedError:
            msg = _("Unable to get rdp console, functionality not implemented")
            raise webob.exc.HTTPNotImplemented(explanation=msg)

        return {'console': {'type': console_type, 'url': output['url']}}

    @wsgi.action('os-getSerialConsole')
    def get_serial_console(self, req, id, body):
        """Get connection to a serial console."""
        context = req.environ['nova.context']
        authorize(context)

        # If type is not supplied or unknown get_serial_console below will cope
        console_type = body['os-getSerialConsole'].get('type')
        try:
            instance = self.compute_api.get(context, id, want_objects=True)
            output = self.compute_api.get_serial_console(context,
                                                         instance,
                                                         console_type)
        except exception.InstanceNotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())
        except exception.InstanceNotReady as e:
            raise webob.exc.HTTPConflict(explanation=e.format_message())
        except NotImplementedError:
            msg = _("Unable to get serial console, "
                    "functionality not implemented")
            raise webob.exc.HTTPNotImplemented(explanation=msg)

        return {'console': {'type': console_type, 'url': output['url']}}


class Consoles(extensions.ExtensionDescriptor):
    """Interactive Console support."""
    name = "Consoles"
    alias = "os-consoles"
    namespace = "http://docs.openstack.org/compute/ext/os-consoles/api/v2"
    updated = "2011-12-23T00:00:00Z"

    def get_controller_extensions(self):
        controller = ConsolesController()
        extension = extensions.ControllerExtension(self, 'servers', controller)
        return [extension]
