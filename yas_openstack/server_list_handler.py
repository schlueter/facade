from pprint import pformat

from jinja2 import Template

from yas_openstack.openstack_handler import OpenStackHandler
from yas_openstack.server import ServersFoundException


class OpenStackServerListHandler(OpenStackHandler):

    search_error_message = (
        'Invalid search opts, list query must look like: '
        '```list[ search_opts <sort query>=<argument>[,<query>=<argument>[,...]]'
        '[ meta[data] <key>=<value>[,<key>=<value>]]```\n'
        'For example:\n&gt; list search_opts state=Running metadata owner=tswift\n'
        'Available sort queries and fields may be found in the '
        # pylint: disable=line-too-long
        '<https://developer.openstack.org/api-ref/compute/?expanded=list-servers-detailed-detail#list-servers-detailed|docs>.')

    def __init__(self, *args, **kwargs):
        super().__init__(r'(?:list)'
                         r'(?:(?:\ search_opts )([a-z\.=,:\ ]+))?'
                         r'(?:(?:\ meta(?:data)?\ )(!?[\-a-zA-Z0-9\,_=]+))?',
                         *args, **kwargs)

    def get_default_search_options(self, data):
        raw_default_search_options = Template(self.config.default_search_options).render(**data)
        raw_default_search_metadata = Template(self.config.default_search_metadata).render(**data)
        default_search_options = dict(opt.split('=') for opt in raw_default_search_options.split(',') if not opt == '')
        default_search_options['metadata'] = dict(opt.split('=') for opt in raw_default_search_metadata.split(',') if not opt == '')
        return default_search_options

    def handle(self, data, reply):
        raw_search_opts, raw_metadata = self.current_match.groups()
        self.log('DEBUG', f"{data['yas_hash']} raw_search_opts:\n{raw_search_opts}\nand raw_metadata:\n{raw_metadata}")

        if raw_search_opts or raw_metadata:
            try:
                search_opts = dict(opt.split('=') for opt in (raw_search_opts or '').split(',') if not opt == '')
            except ValueError:
                return reply(self.search_error_message)

            try:
                metadata = dict(opt.split('=') for opt in (raw_metadata or '').split(',') if not opt == '')
            except ValueError:
                return reply(self.search_error_message)

            search_opts['metadata'] = metadata
        else:
            search_opts = self.get_default_search_options(data)
        try:
            servers = self.server_manager.findall(**search_opts)
        except ServersFoundException as err:
            reply(f'There was an issue finding {search_opts}: {err}')

        options = {**search_opts, **search_opts['metadata']}
        option_string = ", ".join([opt + "=" + options[opt] for opt in options if isinstance(options[opt], str)])

        attachments = [self.parse_server_to_attachment(server.to_dict(), metadata) for server in servers]

        self.api_call('chat.postMessage',
                      text=f"Found {len(servers)} servers with search options {option_string}:",
                      channel=data['channel'],
                      thread_ts=data['ts'],
                      reply_broadcast=True,
                      attachments=attachments)

    def parse_server_to_attachment(self, server, metadata):

        self.log('DEBUG', f"Parsing server:\n{pformat(server)}")
        addresses = [interface['addr']
                     for network in server['addresses']
                     for interface in server['addresses'][network]]

        init = server['metadata'].get('init')
        test = server['metadata'].get('test')

        if init == 'done':
            if test == 'pass':
                attachment_color = '#7D7'
            elif test == 'full':
                attachment_color = '#AEC6CF'
            elif test == 'quick':
                attachment_color = '#AEC6CF'
            elif test == 'started':
                attachment_color = '#AEC6CF'
            elif test == 'fail':
                attachment_color = '#FF3'
            else:
                attachment_color = '#AAA'
        elif init == 'started':
            attachment_color = '#AEC6CF'
        elif init == 'fail':
            attachment_color = '#C23B22'
        else:
            attachment_color = '#AAA'

        for key in ['owner_id']:
            server['metadata'].pop(key, None)

        if 'owner_id' in metadata:
            # Add empty owner to remove from output
            metadata['owner'] = None

        fields = [dict(title=key, value=server['metadata'][key], short=True)
                  for key in server['metadata'] if not key in metadata and server['metadata'][key]]
        fields.append(dict(title='addresses', value=', '.join(addresses), short=len(addresses) == 1))
        fields.append(dict(title='id', value=server['id'], short=False))

        return dict(
            title=f"{server['name']}.{self.config.domain}",
            title_link=f"http://www.{server['name']}.{self.config.domain}",
            fields=fields,
            color=attachment_color)
