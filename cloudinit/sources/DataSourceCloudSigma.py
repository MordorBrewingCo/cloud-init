# vi: ts=4 expandtab
#
#    Copyright (C) 2013-2014 CloudSigma
#
#    Author: Kiril Vladimiroff <kiril.vladimiroff@cloudsigma.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License version 3, as
#    published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
from slugify import slugify
from cepko import Cepko

from cloudinit import log as logging
from cloudinit import sources
from cloudinit import util

LOG = logging.getLogger(__name__)


class DataSourceCloudSigma(sources.DataSource):
    """
    Uses cepko in order to gather the server context from the VM.

    For more information about CloudSigma's Server Context:
    http://cloudsigma-docs.readthedocs.org/en/latest/server_context.html
    """
    def __init__(self, sys_cfg, distro, paths):
        self.cepko = Cepko()
        sources.DataSource.__init__(self, sys_cfg, distro, paths)

    def get_data(self):
        """
        Metadata is the whole server context and /meta/cloud-config is used
        as userdata.
        """
        try:
            server_context = self.cepko.all().result
            server_meta = server_context['meta']
            self.userdata_raw = server_meta.get('cloud-config', "")
            self.metadata = server_context
            self.ssh_public_key = server_meta['ssh_public_key']
        except:
            util.logexc(LOG, "Failed reading from the serial port")
            return False
        return True

    def get_hostname(self, fqdn=False):
        """
        Cleans up and uses the server's name if the latter is set. Otherwise
        the first part from uuid is being used.
        """
        if len(self.metadata['name']) > 0:
            return slugify(self.metadata['name'])[:61]
        else:
            return self.metadata['uuid'].split('-')[0]

    def get_public_ssh_keys(self):
        return [self.ssh_public_key]

    def get_instance_id(self):
        return self.metadata['uuid']


# Used to match classes to dependencies. Since this datasource uses the serial
# port network is not really required, so it's okay to load without it, too.
datasources = [
    (DataSourceCloudSigma, (sources.DEP_FILESYSTEM)),
    (DataSourceCloudSigma, (sources.DEP_FILESYSTEM, sources.DEP_NETWORK)),
]


def get_datasource_list(depends):
    """
    Return a list of data sources that match this set of dependencies
    """
    return sources.list_from_depends(depends, datasources)
