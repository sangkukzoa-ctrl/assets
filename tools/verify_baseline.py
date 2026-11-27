"""Read-only offline check. ZIP comparison only when local baseline archive exists."""
from pathlib import Path
import hashlib, zipfile
root=Path(__file__).resolve().parents[1]
def h(data): return hashlib.sha256(data).hexdigest()
expected={'main.go':'d86c49b60e4a053882e3146ecb8d9bcbc969d86c684aec3c375d085070d5773a','go.mod':'8473cfb08bd8e083728fae0d5dddde7b112a751e1561dd1f57f18e89f2019aae'}
for name, sha in expected.items():
    data=(root/'project'/name).read_bytes()
    assert h(data)==sha, f'baseline source changed: {name}'
    print('PASS source',name,sha)
z=root/'baseline/FF14KakaoBridge_v1.7.13.zip'
if z.exists():
    assert h(z.read_bytes())=='82508e875934b58b663434270ea2f3808b2a9bd1c2072756a90d68b81a48599e', 'original ZIP mismatch'
    with zipfile.ZipFile(z) as f:
        assert f.testzip() is None
        assert h(f.read('FF14KakaoBridge.exe'))=='b7d732b9cea6fdc20ddeb96c78a1759e7e0fbc2cb4f7d1481a7373918517477f', 'original EXE mismatch'
        for name in expected: assert f.read('Source/'+name)==(root/'project'/name).read_bytes()
    print('PASS original ZIP, original EXE, source byte comparison')
else:
    print('Original ZIP not present (normal for remote source-only branch); source hash checked only.')
