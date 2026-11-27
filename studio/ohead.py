import sys, os, math, subprocess, json, glob
import numpy as np, cv2, soundfile as sf
sys.path.insert(0, '/tmp/par2'); from anim import *
os.chdir('/home/claude/repo')
from kokoro_onnx import Kokoro

SPEC = json.load(open(sys.argv[1])); OUT = sys.argv[2]
VOICE = SPEC.get('voice', 'am_onyx'); SPEED = SPEC.get('speed', 0.92)
import urllib.request
os.makedirs('tts', exist_ok=True)
for _f in ('kokoro-v1.0.int8.onnx', 'voices-v1.0.bin'):
    if not os.path.exists('tts/' + _f): urllib.request.urlretrieve('https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/' + _f, 'tts/' + _f)
K = Kokoro('tts/kokoro-v1.0.int8.onnx', 'tts/voices-v1.0.bin')
SR = 24000
lines = SPEC['lines'] + ['Follow Fruit Soda for a fun fact every day.']
gaps = SPEC.get('gaps', {})
import hashlib, pickle
ck = '/tmp/par2/cache_' + hashlib.md5((json.dumps(lines) + VOICE + str(SPEED) + json.dumps(gaps)).encode()).hexdigest() + '.pkl'
if os.path.exists(ck):
    S, E, total, voice = pickle.load(open(ck, 'rb'))
else:
    S = []; E = []; t = 0.6
    chunks = [np.zeros(int(SR * 0.6), np.float32)]
    for i, l in enumerate(lines):
        s, _ = K.create(l, voice=VOICE, speed=SPEED, lang='en-gb' if VOICE.startswith('b') else 'en-us'); s = np.asarray(s, np.float32)
        idx = np.where(np.abs(s) > 0.01)[0]; s = s[idx[0]:idx[-1] + 1]
        S.append(t); E.append(t + len(s) / SR); chunks.append(s)
        g = float(gaps.get(str(i), 0.42)); chunks.append(np.zeros(int(SR * g), np.float32)); t += len(s) / SR + g
    total = t + 0.4; voice = np.concatenate(chunks)
    pickle.dump((S, E, total, voice), open(ck, 'wb'))
sf.write('/tmp/par2/vo_raw.wav', voice, SR)
subprocess.run(['ffmpeg','-y','-loglevel','error','-i','/tmp/par2/vo_raw.wav','-af','equalizer=f=110:t=q:w=1.0:g=3.5,equalizer=f=250:t=q:w=1:g=1.5,equalizer=f=3200:t=q:w=1:g=1.5,acompressor=threshold=-22dB:ratio=3:attack=12:release=180:makeup=4,aecho=0.8:0.45:38:0.14','/tmp/par2/vo.wav'],check=True)
print('timings', [round(x, 1) for x in S], round(total, 1))
WORDS = [l.split() for l in lines]
WT = []
for i, ws in enumerate(WORDS):
    ln = np.array([len(w) + 2 for w in ws], float); cs = np.concatenate([[0], np.cumsum(ln)]) / ln.sum()
    WT.append([S[i] + (E[i] - S[i]) * x for x in cs[:-1]])
