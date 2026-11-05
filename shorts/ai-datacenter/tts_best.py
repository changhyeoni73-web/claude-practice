# 문장마다 여러 seed로 TTS 생성 → Whisper로 받아써서 원문과 가장 가까운 버전 선택
import json, re, torch, soundfile as sf, uroman as ur, numpy as np, scipy.signal as ss, sys
from transformers import VitsModel, AutoTokenizer, pipeline
N=int(sys.argv[1]) if len(sys.argv)>1 else 6; RATE=1.2
REF={"s1":"이번 주 미국인들은 AI를 막아섰습니다","s2":"미국 10개 주 41곳의 주민투표 안건은 단 하나 AI 데이터센터",
"s3":"결과는 단 한 곳을 제외한 전부 반대였습니다","s4":"이유는 간단합니다 당신이 AI에 질문 하나를 던질 때마다 물 다섯 방울이 사라집니다",
"s5":"과열된 서버를 식히기 위해서입니다","s6":"고작 다섯 방울 하지만 그 질문은 하루 수십억 번 쏟아집니다",
"s7":"미국 전력의 4.4%는 이미 데이터센터가 삼키고 있습니다","s8":"그리고 2028년 최대 12%까지 늘어날 수 있습니다",
"s9":"치솟는 전기요금 말라가는 수자원 주민들이 먼저 움직였습니다","s10":"편리함의 대가 누가 치르게 될까요 당신의 생각을 댓글로 남겨주세요"}
norm=lambda s: re.sub(r"[^0-9A-Za-z가-힣%.]","",s.replace("마흔한","41").replace("에이아이","AI"))
def cer(a,b):
    a,b=norm(a),norm(b); d=list(range(len(b)+1))
    for i,ca in enumerate(a,1):
        p,d[0]=d[0],i
        for j,cb in enumerate(b,1): p,d[j]=d[j],min(d[j]+1,d[j-1]+1,p+(ca!=cb))
    return d[-1]/max(1,len(a))
m=VitsModel.from_pretrained("facebook/mms-tts-kor"); t=AutoTokenizer.from_pretrained("facebook/mms-tts-kor"); r=ur.Uroman()
m.speaking_rate=RATE; asr=pipeline("automatic-speech-recognition",model="openai/whisper-small"); sr=m.config.sampling_rate
dur={}; report={}
for s in json.load(open("script.json")):
    ids=t(r.romanize_string(s["say"].replace("AI","에이아이")),return_tensors="pt"); best=None
    for k in range(N):
        torch.manual_seed(k)
        with torch.no_grad(): w=m(**ids).waveform[0].numpy()
        hyp=asr({"raw":ss.resample_poly(w,16000,sr).astype(np.float32),"sampling_rate":16000},generate_kwargs={"language":"ko"})["text"]
        e=cer(REF[s["id"]],hyp)
        if best is None or e<best[0]: best=(e,w,hyp,k)
        if e==0: break
    sf.write(f"assets/audio/{s['id']}.wav",best[1],sr); dur[s["id"]]=len(best[1])/sr
    report[s["id"]]=dict(cer=round(best[0],3),heard=best[2].strip(),seed=best[3]); print(s["id"],report[s["id"]],flush=True)
json.dump(dur,open("assets/audio/durations.json","w"),indent=1); json.dump(report,open("assets/audio/asr_report.json","w"),indent=1,ensure_ascii=False)
print("total",sum(dur.values()))
