"""Restore exact missing resources from archives attached to this Composer Master."""
from contextlib import ExitStack
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def confined(root, relative):
    path = root / relative
    if Path(relative).is_absolute() or '..' in Path(relative).parts:
        raise ValueError('Unsafe resource path: ' + relative)
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Resource escapes Composer: ' + relative)
    return path


def restore(root=ROOT):
    root = Path(root).resolve()
    manifest = json.loads((root / 'resource_installation.json').read_text())
    pending = []
    for entry in manifest['files']:
        path = confined(root, entry['path'])
        if path.exists():
            if not path.is_file() or path.stat().st_size != entry['size'] or digest(path) != entry['sha256']:
                raise ValueError('Existing resource differs; left unchanged: ' + entry['path'])
        else:
            pending.append(entry)
    if not pending:
        return {'status': 'VERIFIED', 'files': len(manifest['files']), 'restored': 0}
    wanted = {e['source'] for e in pending}
    with tempfile.TemporaryDirectory(prefix='composer-resources-', dir=root) as temporary, ExitStack() as stack:
        temp = Path(temporary)
        archives = {}
        # Validate complete source archives before installing any bytes.
        for source in manifest['sources']:
            if source['id'] not in wanted:
                continue
            paths = []
            for item in source['archives']:
                path = confined(root.parent, item['path'])
                if not path.is_file() or digest(path) != item['sha256']:
                    raise ValueError('Attached resource archive missing or changed: ' + item['path'])
                paths.append(path)
            if 'joined_sha256' in source:
                path = temp / (source['id'] + '.zip')
                with path.open('wb') as output:
                    for part in paths:
                        with zipfile.ZipFile(part) as archive:
                            members = [i for i in archive.infolist() if not i.is_dir()]
                            if len(members) != 1:
                                raise ValueError('Unexpected resource archive contents')
                            with archive.open(members[0]) as stream:
                                shutil.copyfileobj(stream, output)
                if digest(path) != source['joined_sha256']:
                    raise ValueError('Joined resource archive hash mismatch')
            elif 'nested_member' in source:
                path = temp / (source['id'] + '.zip')
                with zipfile.ZipFile(paths[0]) as outer, outer.open(source['nested_member']) as stream, path.open('wb') as output:
                    shutil.copyfileobj(stream, output)
                if digest(path) != source['nested_sha256']:
                    raise ValueError('Nested resource archive hash mismatch')
            else:
                path = paths[0]
            archives[source['id']] = stack.enter_context(zipfile.ZipFile(path))
        for number, entry in enumerate(pending):
            destination = confined(root, entry['path'])
            staged = temp / ('file-' + str(number))
            if entry['source'] == 'inline':
                staged.write_bytes(entry['text'].encode('utf-8'))
            else:
                with archives[entry['source']].open(entry['member']) as stream, staged.open('wb') as output:
                    shutil.copyfileobj(stream, output)
            if staged.stat().st_size != entry['size'] or digest(staged) != entry['sha256']:
                raise ValueError('Resource bytes do not match saved master: ' + entry['path'])
            destination.parent.mkdir(parents=True, exist_ok=True)
            if entry.get('executable'):
                staged.chmod(0o755)
            # Publish without overwriting a file installed by another process.
            try:
                os.link(staged, destination)
            except FileExistsError:
                if digest(destination) != entry['sha256']:
                    raise ValueError('Concurrent resource conflict: ' + entry['path'])
            staged.unlink()
    return {'status': 'VERIFIED', 'files': len(manifest['files']), 'restored': len(pending)}


if __name__ == '__main__':
    print(json.dumps(restore()))
