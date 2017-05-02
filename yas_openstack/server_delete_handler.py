from yas_openstack.openstack_handler import OpenStackHandler
from yas_openstack.server import ServersFoundException


class OpenStackServerDeleteHandler(OpenStackHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(r'(?:delete|drop|terminate|bust a cap in|pop a cap in)'
                         r'(?: search_opts (' + self.SEARCH_OPTS_REGEX + '))?'
                         r'(?: meta(?:data)? (!?' + self.SEARCH_OPTS_REGEX + '))?'
                         r'(?: ([- \w,_=]+))?',
                         *args, **kwargs)

    def handle(self, _, reply):
        raw_search_opts, raw_metadata, names = self.current_match.groups()
        if names and (raw_metadata or raw_search_opts):
            return reply(f":fearful: I don't understand. You need to specify either names *or* search parameters")

        elif names:
            for name in names.split():
                try:
                    self.server_manager.delete(name=f'^{name}$')
                except ServersFoundException as err:
                    return reply(f'There was an issue finding {name}: {err}')

                reply(f'Deleted {name}.')

        elif raw_metadata or raw_search_opts:
            search_opts = self.server_manager.parse_search_args(
                raw_metadata=raw_metadata,
                raw_search_opts=raw_search_opts)
            if not 'owner' in search_opts['metadata'] and not 'owner_id' in search_opts['metadata']:
                return reply(f":fearful: That's too dangerous. Please specify an owner using metadata.")
            servers = self.server_manager.findall(**search_opts)
            if not servers:
                reply(f'No servers found matching {search_opts}')
            else:
                for server in servers:
                    server.delete()
                    reply(f'Deleted {server.name} with id {server.id}.')
