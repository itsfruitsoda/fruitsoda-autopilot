"""Studio builder: python studio/build.py <spec.json> <out.mp4> [t1,t2,...]
Spec needs "scene": otter | axo. Runs from the repo root."""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
TMP = os.environ.get('STUDIO_TMP', '/tmp/studio'); os.makedirs(TMP, exist_ok=True)
spec = json.load(open(sys.argv[1])); scene = spec['scene']
tail = {'otter': 'otail.py', 'axo': 'atail.py'}[scene]
code = open(os.path.join(HERE, 'ohead.py')).read() + '\n' + open(os.path.join(HERE, tail)).read() + '\n' + open(os.path.join(HERE, 'common.py')).read()
code = code.replace('/tmp/par2', TMP).replace('/home/claude/repo', ROOT)
sys.path.insert(0, HERE); sys.argv = [sys.argv[0]] + sys.argv[1:]
exec(compile(code, 'studio_' + scene, 'exec'), {'__name__': '__main__'})
