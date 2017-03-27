import os
import re
import sys

from jinja2 import Template
from yas import RegexHandler

from yas_openstack.server import ServerManager
from yas_openstack.yaml_file_config import YamlConfiguration


config = YamlConfiguration()

class OpenstackHandlerError(Exception):
    pass

class OpenstackHandler(RegexHandler):

    def __init__(self, regex, bot_name, api_call, *args, log=None, **kwargs):
        super().__init__(regex, bot_name, api_call, *args, log=log, **kwargs)
        self.server_manager = ServerManager()
        self.matches = {}
        self.template = self.get_userdata_template()

    def get_userdata_template(self):
        config_userdata = config.create_server_defaults.get('userdata', '')
        potential_userdata_file = os.path.join(sys.prefix, config_userdata)

        if os.path.isfile(potential_userdata_file):
            with  open(potential_userdata_file, 'r') as template_file:
                template = template_file.read()
        else:
            template = config_userdata

        return Template(template)
