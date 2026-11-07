"""Fail-closed SFZ opcode validation for Renderer 005; does not emulate missing expressive behavior."""
import re
from pathlib import Path

# The internal renderer's implemented note/velocity/sample subset.
SUPPORTED = {'sample','default_path','pitch_keycenter','key','lokey','hikey','lovel','hivel'}
# These require a compatible external engine or a properly tested implementation.
EXPRESSIVE = {'ampeg_release','lorand','hirand'}

def unsupported_expressive_opcodes(path: Path):
    source = Path(path).read_text(encoding='utf-8',errors='replace')
    source = re.sub(r'(?m)//.*$', '', source)
    return sorted(set(re.findall(r'(?<![\w])([A-Za-z_][A-Za-z0-9_]*)\s*=', source.lower())) & EXPRESSIVE)
