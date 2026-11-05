import json, torch, soundfile as sf, uroman as ur, numpy as np, sys
from transformers import VitsModel, AutoTokenizer
torch.manual_seed(7)
m=VitsModel.from_pretrained("facebook/mms-tts-kor"); t=AutoTokenizer.from_pretrained("facebook/mms-tts-kor"); r=ur.Uroman()
m.speaking_rate=float(sys.argv[1]) if len(sys.argv)>1 else 1.1; m.noise_scale=0.6
sr=m.config.sampling_rate; out={}
for s in json.load(open("script.json")):
    txt=s["say"].replace("AI","에이아이")
    with torch.no_grad(): w=m(**t(r.romanize_string(txt),return_tensors="pt")).waveform[0].numpy()
    sf.write(f"assets/audio/{s['id']}.wav",w,sr); out[s["id"]]=len(w)/sr
json.dump(out,open("assets/audio/durations.json","w"),indent=1); print(out, sum(out.values()))
