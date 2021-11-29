from unittest import TestCase

from pyshrimp.utils.table_parser import parse_table

table_data = '''
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root           1  0.0  0.0 171008 10724 ?        Ss   lis21   3:28 /sbin/init
root           2  0.0  0.0      0     0 ?        S    lis21   0:00 some "command"
root           3  0.0  0.0      0     0 ?        I<   lis21   0:00 command with spaces at the end:      
root           4  0.0  0.0      0     0 ?        I<   lis21   0:00 
'''.strip()


class Test(TestCase):

    def test_parse_table_should_parse_ps_table(self):
        res = parse_table(table_data.split('\n'))
        self.assertEqual(
            ['USER', 'PID', '%CPU', '%MEM', 'VSZ', 'RSS', 'TTY', 'STAT', 'START', 'TIME', 'COMMAND'],
            res.header
        )
        self.assertEqual(
            [
                ['root', '1', '0.0', '0.0', '171008', '10724', '?', 'Ss', 'lis21', '3:28', '/sbin/init'],
                ['root', '2', '0.0', '0.0', '0', '0', '?', 'S', 'lis21', '0:00', 'some "command"'],
                ['root', '3', '0.0', '0.0', '0', '0', '?', 'I<', 'lis21', '0:00', 'command with spaces at the end:'],
                ['root', '4', '0.0', '0.0', '0', '0', '?', 'I<', 'lis21', '0:00']
            ],
            res.rows
        )
        self.assertEqual(
            [
                {'USER': 'root', 'PID': '1', '%CPU': '0.0', '%MEM': '0.0', 'VSZ': '171008', 'RSS': '10724', 'TTY': '?', 'STAT': 'Ss', 'START': 'lis21', 'TIME': '3:28', 'COMMAND': '/sbin/init'},
                {'USER': 'root', 'PID': '2', '%CPU': '0.0', '%MEM': '0.0', 'VSZ': '0', 'RSS': '0', 'TTY': '?', 'STAT': 'S', 'START': 'lis21', 'TIME': '0:00', 'COMMAND': 'some "command"'},
                {'USER': 'root', 'PID': '3', '%CPU': '0.0', '%MEM': '0.0', 'VSZ': '0', 'RSS': '0', 'TTY': '?', 'STAT': 'I<', 'START': 'lis21', 'TIME': '0:00', 'COMMAND': 'command with spaces at the end:'},
                {'USER': 'root', 'PID': '4', '%CPU': '0.0', '%MEM': '0.0', 'VSZ': '0', 'RSS': '0', 'TTY': '?', 'STAT': 'I<', 'START': 'lis21', 'TIME': '0:00'}
            ],
            list(res.dict_rows(use_dot_dict=False))
        )
