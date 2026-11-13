"""Small checks for launcher failure handling and result preservation; no Docker required."""
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import run_baseline as launcher


class LauncherTests(unittest.TestCase):
    def test_failed_command_stops_execution(self):
        error = subprocess.CalledProcessError(7, ['python', 'scripts/replay_fetruth_artifact.py'])
        with patch.object(launcher.subprocess, 'run', side_effect=error) as process:
            with self.assertRaises(subprocess.CalledProcessError):
                launcher.execute('fetruth', io.StringIO())
            self.assertEqual(process.call_count, 1)

    def test_backup_preserves_both_fetruth_results(self):
        with tempfile.TemporaryDirectory(prefix='baseline tests ') as directory:
            root = Path(directory)
            for name in ('fetruth', 'fetruth-paper', 'sonarqube'):
                path = root / 'results' / name
                path.mkdir(parents=True)
                (path / 'result.txt').write_text(name, encoding='utf-8')
            with patch.object(launcher, 'ROOT', root):
                launcher.backup_results('fetruth', 'test')
            backup = root / '.runtime/backups/fetruth-test'
            for name in ('fetruth', 'fetruth-paper'):
                self.assertEqual((backup / name / 'result.txt').read_text(), name)
                self.assertEqual((root / 'results' / name / 'result.txt').read_text(), name)
            self.assertFalse((backup / 'sonarqube').exists())

    def test_paper_mismatch_is_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'results/fetruth-paper'
            output.mkdir(parents=True)
            (output / 'comparison.json').write_text(json.dumps({'exact_match': False, 'observed_recommendations': 16}))
            with patch.object(launcher, 'ROOT', root), self.assertRaises(RuntimeError):
                launcher.require_paper_match()

    def test_unready_service_times_out(self):
        with patch.object(launcher.time, 'monotonic', side_effect=[0, 301]):
            with patch.object(launcher.time, 'sleep') as sleep, self.assertRaises(RuntimeError):
                launcher.wait_ready(lambda: False, 'test service')
            sleep.assert_not_called()


if __name__ == '__main__':
    unittest.main()
