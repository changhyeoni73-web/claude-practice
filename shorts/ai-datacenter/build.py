"""AI 데이터센터 숏폼 조립 스크립트 (1080x1920, 30fps).

사용: python3 build.py  →  build/final.mp4
입력: script.json(대사/자막), assets/audio/*.wav(TTS), assets/clips/*.mp4(Pexels)
"""
import json, subprocess, pathlib

ROOT = pathlib.Path(__file__).parent
B = ROOT / "build"; B.mkdir(exist_ok=True)
CLIPS = ROOT / "assets/clips"; AUD = ROOT / "assets/audio"
FONT = ROOT / "assets/fonts/Pretendard-Black.otf"
FONT_M = ROOT / "assets/fonts/Pretendard-SemiBold.otf"
W, H, FPS = 1080, 1920, 30
GAP = 0.3                     # 문장 사이 쉼
GAP_AFTER = {"s1": 0.55}      # 훅 뒤엔 조금 더 길게

# 장면별 클립: (파일, 원본 시작초, 비율) — 비율 합이 1이 되도록 장면 길이를 나눔
SCENES = {
    "s1":  [("glitch", 0.0, 0.08), ("vote_drop", 1.5, 0.92)],
    "s2":  [("ballot_boxes", 1.0, 0.45), ("server", 3.0, 0.55)],
    "s3":  [("people_voting", 2.0, 1.0)],
    "s4":  [("phone_typing", 0.5, 0.45), ("water_drops", 2.0, 0.55)],
    "s5":  [("cpu", 2.0, 1.0)],
    "s6":  [("city_night", 0.5, 1.0)],
    "s7":  [("steam_plant", 4.0, 1.0)],
    "s8":  [("transmission", 6.0, 0.5), ("cooling_towers", 3.0, 0.5)],
    "s9":  [("dry_lake", 5.0, 0.5), ("protest", 10.0, 0.5)],
    "s10": [("phone_neon", 1.0, 0.45), ("server", 15.0, 0.55)],
}
# 자막 아래 작은 출처 표기
SOURCE = {
    "s2": "출처: CNBC · Ballotpedia (2026.11)",
    "s3": "출처: CNBC · Ballotpedia (2026.11)",
    "s4": "출처: Google (2025), Gemini 텍스트 프롬프트 중앙값 0.26mL",
    "s7": "출처: 미국 로런스버클리국립연구소 (2024), 2023년 기준",
    "s8": "출처: 미국 로런스버클리국립연구소 (2024), 6.7~12% 전망",
}
HEADER = "이거 알고 계셨나요?"


def run(cmd):
    subprocess.run(cmd, check=True)


def esc(p):
    return str(p).replace(":", r"\:")


def textfile(name, text):
    p = B / f"txt_{name}.txt"; p.write_text(text, encoding="utf-8"); return esc(p)


def caption_filters(sid, cap):
    lines = cap.split("\n")
    f = []
    # 상단 헤더
    f.append(f"drawtext=expansion=none:fontfile={esc(FONT)}:textfile={textfile('header', HEADER)}:fontsize=54:"
             f"fontcolor=white:box=1:boxcolor=0xE53935@0.95:boxborderw=22:x=(w-tw)/2:y=250")
    # 메인 자막: 1줄=흰색, 2줄=노란색, 살짝 튀어나오는 페이드인
    n = len(lines); base_y = 1180 - (n - 1) * 70
    for i, line in enumerate(lines):
        color = "white" if (i == 0 and n > 1) else "0xFFD600"
        size = 84 if (i == 0 and n > 1) else 112
        y = base_y + i * 150 - (20 if i == 0 and n > 1 else 0)
        f.append(f"drawtext=expansion=none:fontfile={esc(FONT)}:textfile={textfile(f'{sid}_{i}', line)}:fontsize={size}:"
                 f"fontcolor={color}:borderw=9:bordercolor=black:shadowx=0:shadowy=6:shadowcolor=black@0.6:"
                 f"x=(w-tw)/2:y={y}+12*max(0\\,1-t/0.18):alpha='min(1,t/0.18)'")
    if sid in SOURCE:
        f.append(f"drawtext=expansion=none:fontfile={esc(FONT_M)}:textfile={textfile(sid + '_src', SOURCE[sid])}:fontsize=30:"
                 f"fontcolor=white@0.75:x=(w-tw)/2:y=1600")
    return f


def render_scene(sid, cap, dur):
    parts = SCENES[sid]
    inputs, chains = [], []
    for k, (name, ss, frac) in enumerate(parts):
        d = dur * frac
        inputs += ["-ss", str(ss), "-t", f"{d + 0.1:.3f}", "-i", str(CLIPS / f"{name}.mp4")]
        # 화면 꽉 채우기(9:16 크롭) + 천천히 줌인
        chains.append(
            f"[{k}:v]fps={FPS},scale={int(W*1.15)}:{int(H*1.15)}:force_original_aspect_ratio=increase,"
            f"crop={int(W*1.15)}:{int(H*1.15)},"
            f"scale=w='{W}*(1.12-0.08*t/{d:.3f})':h=-2:eval=frame,"   # 줌인 효과
            f"crop={W}:{H},setsar=1,trim=duration={d:.3f},setpts=PTS-STARTPTS[c{k}]")
    cat = "".join(f"[c{k}]" for k in range(len(parts)))
    look = "eq=brightness=-0.07:saturation=1.15:contrast=1.05,vignette=PI/4.5"
    fc = ";".join(chains) + f";{cat}concat=n={len(parts)}:v=1:a=0,{look}," + ",".join(caption_filters(sid, cap)) + "[v]"
    out = B / f"scene_{sid}.mp4"
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[v]", "-t", f"{dur:.3f}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), str(out)])
    return out


def main():
    script = json.load(open(ROOT / "script.json"))
    durs = json.load(open(AUD / "durations.json"))
    scenes, t, voice_parts, starts = [], 0.0, [], []
    for s in script:
        sid = s["id"]; dur = durs[sid] + GAP_AFTER.get(sid, GAP)
        starts.append(t); t += dur
        scenes.append(render_scene(sid, s["cap"], dur)); print("scene", sid, round(dur, 2))
        voice_parts.append((sid, dur))
    total = t
    # 1) 영상 이어붙이기 + 하단 진행바
    lst = B / "scenes.txt"; lst.write_text("".join(f"file '{p}'\n" for p in scenes))
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-vf", f"drawbox=x=0:y=ih-14:w=iw*t/{total:.3f}:h=14:color=0xFFD600@0.9:t=fill",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", str(B / "video.mp4")])
    # 2) 내레이션: 문장 + 쉼 이어붙이기, 48kHz, 목소리 다듬기
    ins, fc = [], []
    for k, (sid, dur) in enumerate(voice_parts):
        ins += ["-i", str(AUD / f"{sid}.wav")]
        fc.append(f"[{k}:a]aresample=48000,apad,atrim=duration={dur:.3f}[a{k}]")
    fc.append("".join(f"[a{k}]" for k in range(len(voice_parts))) +
              f"concat=n={len(voice_parts)}:v=0:a=1,highpass=f=90,"
              "acompressor=threshold=-20dB:ratio=3:attack=5:release=80,aformat=channel_layouts=stereo[voice]")
    run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(fc), "-map", "[voice]", str(B / "voice.wav")])
    # 3) 배경음: 낮은 긴장감 베이스 펄스 + 장면 전환 '휙' 효과음 (직접 합성, 저작권 걱정 없음)
    bed = (f"aevalsrc='0.35*sin(2*PI*55*t)*(0.55+0.45*sin(2*PI*1.6*t))+0.12*sin(2*PI*110*t)*(0.5+0.5*sin(2*PI*0.8*t))'"
           f":s=48000:d={total:.3f}")
    whoosh_in, whoosh_fc = [], []
    for k, st in enumerate(starts[1:]):
        whoosh_in += ["-f", "lavfi", "-t", "0.45", "-i", "anoisesrc=color=pink:amplitude=0.5:r=48000"]
        ms = int(max(0, st - 0.2) * 1000)
        whoosh_fc.append(f"[{k+2}:a]bandpass=f=1800:width_type=h:w=2500,afade=t=in:d=0.25,afade=t=out:st=0.25:d=0.2,"
                         f"volume=0.35,adelay={ms}|{ms},apad[w{k}]")
    # 첫 장면 임팩트 '쿵'
    hit = "aevalsrc='0.9*sin(2*PI*(60-30*t)*t)*exp(-4*t)':s=48000:d=1.2"
    n_w = len(starts) - 1
    fc = (f"[0:a]volume=0.22,aformat=channel_layouts=stereo,afade=t=in:d=0.3,afade=t=out:st={total-1.5:.3f}:d=1.5[bed];"
          f"[1:a]aformat=channel_layouts=stereo[hit];" + ";".join(whoosh_fc) + ";"
          f"[bed][hit]{''.join(f'[w{k}]' for k in range(n_w))}amix=inputs={2+n_w}:normalize=0,"
          f"atrim=duration={total:.3f},aformat=channel_layouts=stereo[music];"
          f"[{2+n_w}:a]asplit=2[vo][sc];"
          f"[music][sc]sidechaincompress=threshold=0.05:ratio=6:attack=20:release=300[duck];"
          f"[duck][vo]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[out]")
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", bed, "-f", "lavfi", "-i", hit, *whoosh_in,
         "-i", str(B / "voice.wav"), "-filter_complex", fc, "-map", "[out]", "-ar", "48000", str(B / "mix.wav")])
    # 4) 합치기
    run(["ffmpeg", "-v", "error", "-y", "-i", str(B / "video.mp4"), "-i", str(B / "mix.wav"),
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(B / "final.mp4")])
    print("done", round(total, 2), "sec ->", B / "final.mp4")


if __name__ == "__main__":
    main()
