# This library is the interface between the buildbot master and
# the buildbot influxdb database.

import time

class Line(object):

    def __init__(self, measure, tags=dict(), fields=dict(), timestamp=None):
        self.measure = measure
        self.tags = tags
        self.fields = fields
        self.timestamp = timestamp

    def write(self, client):
        """Writes data to client."""
        client.write(self.to_line(), protocol='line')

    def to_line(self, with_timestamp=False):
        """Returns a string with the line for the current data."""
        if self.timestamp is None and with_timestamp:
            self.timestamp = int(time.time() / time.get_clock_info('time').resolution)

        line = ''
        line_prefix = []
        line_prefix.append(self.to_escaped_type_str(self.measure, 'measurement'))
        line_prefix.extend(['{}={}'.format(self.to_escaped_type_str(k, 'tag-key-value'),
                                           self.to_escaped_type_str(v, 'tag-key-value'))
                            for k, v in self.tags.items()])

        line += ','.join(line_prefix)
        line += ' '

        fields = ['{}={}'.format(self.to_escaped_type_str(k, 'field-key'),
                                 self.to_escaped_type_str(v, 'field-value'))
                  for k, v in self.fields.items()]
        line += ','.join(fields)

        if self.timestamp is not None:
            line += ' {}'.format(self.timestamp)

        return line

    def to_type_str(self, val, mode) -> str:
        """Returns a string with val being of the right type."""
        t = type(val)

        if t is int:
            return '{}i'.format(val)
        elif t is float:
            return '{}'.format(val)
        elif t is bool:
            if val:
                return 'True'
            else:
                return 'False'
        else:
            assert t is str
            if mode == 'field-value':
                return '"{}"'.format(val)
            return val

    def escape_str_char(self, s: str, ch: str) -> str:
        """Escape in string s, char ch with a backslash."""
        parts = s.split(ch)
        return '\\{}'.format(ch).join(parts)

    def escape_str(self, s: str, mode: str) -> str:
        """Escape string s according to line protocol."""
        # In strings we need to escape double quotes

        if mode == 'field-value':
            return escape_str_char(str, '"')
        else:
            estr = s
            chlist = [',', ' ']
            if mode != 'measurement':
                chlist.append('=')
            for ch in chlist:
                estr = self.escape_str_char(estr, ch)
            return estr

    def to_escaped_type_str(self, val, mode: str) -> str:
        """Escape val as a type string in mode `mode'.
           Mode can be one of: 'tag-key-value', 'field-value', 'field-key', 'measurement'.
        """
        return self.escape_str(self.to_type_str(val, mode), mode)
