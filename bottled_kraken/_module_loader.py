from __future__ import annotations

import linecache
from pathlib import Path
from typing import MutableMapping, Any


def load_split_module(module_file: str, module_globals: MutableMapping[str, Any], parts_dir_name: str) -> None:
    """Load split Python source parts and execute them as one module."""
    module_path = Path(module_file)
    parts_dir = module_path.with_name(parts_dir_name)
    part_paths = [
        path
        for path in sorted(parts_dir.glob('*.py'))
        if path.is_file() and not path.name.startswith('__')
    ]
    if not part_paths:
        raise FileNotFoundError(f'No split module parts found in {parts_dir}')
    source = '\n'.join(
        path.read_text(encoding='utf-8').rstrip('\n')
        for path in part_paths
    ) + '\n'
    virtual_path = str(parts_dir / '__assembled__.py')
    linecache.cache[virtual_path] = (
        len(source),
        None,
        source.splitlines(keepends=True),
        virtual_path,
    )
    exec(compile(source, virtual_path, 'exec'), module_globals, module_globals)
