"""Persistent font-metric worker; no character-count fallback disguised as measurement."""
import json
from pathlib import Path
import subprocess
from deck import node_binary


class TextMetrics:
    def __init__(self):
        node = node_binary()
        if not node:
            raise ValueError('Node is required for actual font measurement')
        self.process = subprocess.Popen([node, str(Path(__file__).with_name('measure_text.mjs'))],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True, encoding='utf-8')
        self.cache = {}
        self.substitutions = {}

    def query(self, payload):
        key = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        if key in self.cache: return self.cache[key]
        try:
            self.process.stdin.write(key+'\n'); self.process.stdin.flush()
            line = self.process.stdout.readline()
            if not line:
                raise ValueError('Font measurement worker unavailable: '+self.process.stderr.read()[-1500:])
            result = json.loads(line)
            if not result.get('ok'): raise ValueError(result.get('error'))
        except (BrokenPipeError, json.JSONDecodeError) as error:
            raise ValueError('Font measurement failed; install runtime dependencies') from error
        self.cache[key] = result
        if result.get('substituted'): self.substitutions[payload.get('font')] = result['font']
        return result

    def wrap(self, text, font, size, width, bold=False, leading=1.28):
        return self.query({'text':text,'font':font,'size':size,'width':width*72,
                           'bold':bold,'leading':leading})

    def width(self, text, font, size, bold=False):
        return self.query({'op':'width','text':text,'font':font,'size':size,'bold':bold})['width']/72

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.close()
            self.process.wait(timeout=10)
        self.process.stdout.close(); self.process.stderr.close()

    def __enter__(self): return self
    def __exit__(self, *_): self.close()
