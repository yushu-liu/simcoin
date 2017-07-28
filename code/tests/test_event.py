from unittest import TestCase
import event
from event import Event
from unittest.mock import patch
from unittest.mock import Mock
from unittest.mock import mock_open
import config
from subprocess import CalledProcessError
from textwrap import dedent


class TestEvent(TestCase):

    @patch('time.time')
    @patch('utils.sleep')
    @patch('utils.check_for_file', lambda file: None)
    @patch('event.execute_cmd')
    def test_execute_multiple_cmds(self, m_execute_cmd, m_sleep, m_time):
        data = dedent("""
            cmd1;cmd2;cmd3
        """).strip()

        with patch('builtins.open', mock_open(read_data=data)):
            e = Event(Mock(), 1)

            m_time.return_value = 0

            e.execute()

            self.assertEqual(m_execute_cmd.call_count, 3)
            self.assertTrue(m_sleep.called)

    @patch('time.time')
    @patch('utils.sleep')
    @patch('utils.check_for_file', lambda file: None)
    @patch('event.execute_cmd')
    def test_execute_multiple_lines(self, m_execute_cmd, m_sleep, m_time):
        data = dedent("""
            cmd1
            cmd2
        """).strip()

        with patch('builtins.open', mock_open(read_data=data)):
            e = Event(Mock(), 1)

            m_time.return_value = 0

            e.execute()

            self.assertEqual(m_execute_cmd.call_count, 2)
            self.assertTrue(m_sleep.call_count, 2)

    @patch('time.time')
    @patch('utils.check_for_file', lambda file: None)
    @patch('event.execute_cmd', lambda cmd, nodes: None)
    def test_execute(self, m_time):
        data = dedent("""
            cmd1;cmd2;cmd3
        """).strip()

        with patch('builtins.open', mock_open(read_data=data)):
            e = Event(Mock(), 0)

            m_time.side_effect = [0, 1, 10]

            with self.assertRaises(Exception) as context:
                e.execute()
            self.assertTrue('Consider to raise the tick_duration' in str(context.exception))

    @patch('utils.check_for_file', lambda file: None)
    @patch('event.execute_cmd')
    def test_execute_with_exce_execute_cmd(self, m_execute_cmd):
        data = dedent("""
            cmd1
        """).strip()

        with patch('builtins.open', mock_open(read_data=data)):
            e = Event(Mock(), 0)
            m_execute_cmd.side_effect = Exception('mock')

            with self.assertRaises(Exception) as context:
                e.execute()
            self.assertTrue('mock' in str(context.exception))

    def test_execute_cmd_with_block_cmd(self):
        node_1 = Mock()
        nodes = {'node-1': node_1}
        cmd = 'block node-1'

        event.execute_cmd(cmd, nodes)

        self.assertTrue(node_1.generate_block.called)

    @patch('event.generate_tx_and_save_creator')
    def test_execute_cmd_with_tx_tmd(self, m_generate_tx_and_save_creator):
        node = Mock()
        node.spent_to_address = 'address'
        nodes = {'node-1': node}
        cmd = 'tx node-1'

        event.execute_cmd(cmd, nodes)

        self.assertTrue(m_generate_tx_and_save_creator.called)
        self.assertEqual(m_generate_tx_and_save_creator.call_args[0][0], node)
        self.assertEqual(m_generate_tx_and_save_creator.call_args[0][1], 'address')

    def test_execute_cmd_with_unknown_cmd(self):
        nodes = {'node-1': {}}
        cmd = 'unknown node-1'

        with self.assertRaises(Exception) as context:
            event.execute_cmd(cmd, nodes)

        self.assertTrue('Unknown cmd' in str(context.exception))

    @patch('builtins.open', new_callable=mock_open)
    def test_generate_tx_and_save_creator(self, m_open):
        node = Mock()
        node.name = 'node-1'
        node.generate_tx.return_value = 'tx_hash'

        event.generate_tx_and_save_creator(node, 'address')

        m_open.assert_called_with(config.tx_csv, 'a')
        handle = m_open()
        self.assertEqual(handle.write.call_args[0][0], 'node-1;tx_hash\n')

    @patch('builtins.open', new_callable=mock_open)
    def test_generate_tx_and_save_creator_with_exception(self, m_open):
        node = Mock()
        node.generate_tx.side_effect = CalledProcessError(None, None)

        event.generate_tx_and_save_creator(node, None)

        self.assertFalse(m_open.called)
