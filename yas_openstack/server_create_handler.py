from yas_openstack.openstack_handler import OpenStackHandler
from yas_openstack.server import NoServersFound, MultipleServersFound


class OpenStackServerCreateHandler(OpenStackHandler):

    def __init__(self, regex, bot_name, api_call, *args, log=None, **kwargs):
        super().__init__('(?:launch|start|create)\ ([-\w]+)'
                         '(?:\ on\ )?([-\w]+:?[-\w]+)?'
                         '(?:\ meta\ )?([\w=,]+)?'
                         '(?:\ from\ )?([-:/\w]+)',
                         bot_name, api_call, *args, log=log, **kwargs)
        self.log('DEBUG', f'Initializing OpenStack server create handler with defaults:\n{self.config.__dict__}')

    def __name_already_used(self, name):
        try:
            existing_server = self.server_manager.find(name=name)
        except NoServersFound:
            existing_server = None
        except MultipleServersFound:
            existing_server = True

        return existing_server

    def handle(self, data, reply):
        name, branch, meta, image = self.current_match.groups()
        reply(f"Received request for creation of {name}", thread=data['ts'])

        if self.__name_already_used(name):
            return reply(f"{name} already exists.", thread=data['ts'])

        userdata = self.template.render(name=name, branch=branch or '', data=data)
        server = self.server_manager.create(name, userdata=userdata, image=image, meta=meta)

        reply(f'Requested creation of {name} with id {server.id}', thread=data['ts'])
        self.log('DEBUG', f'Created used userdata:\n{userdata}')