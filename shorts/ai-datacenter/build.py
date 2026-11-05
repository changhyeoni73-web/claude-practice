"""AI 데이터센터 숏폼 조립 스크립트 (1080x1920, 30fps).

사용: python3 build.py  →  build/final.mp4
입력: script.json(대사/자막), assets/audio/*.wav(TTS), assets/clips/*.mp4(Pexels), assets/music/*.mp3
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

# 장면별 클립: (파일, 원본 시작초, 비율[, 가로 크롭 위치]) — 비율 합이 1이 되도록 장면 길이를 나눔
SCENES = {
    "s1":  [("glitch", 0.0, 0.08), ("vote_people", 0.5, 0.92, 0.2)],
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
    "s4": "출처: Google (2025), Gemini 텍스트 질문 1회 중앙값 0.26mL",
    "s7": "출처: 미국 로런스버클리국립연구소 (2024), 2023년 기준",
    "s8": "출처: 미국 로런스버클리국립연구소 (2024), 6.7~12% 전망",
}
HEADER = "이거 알고 계셨나요?"
# 배경음악: "Investigations" Kevin MacLeod (incompetech.com), CC BY 4.0 — 영상 설명란에 출처 표기 필요
MUSIC = ROOT / "assets/music/Investigations.mp3"
MUSIC_START = 0.0
MUSIC_VOL = 0.30  # 내레이션보다 약 14dB 작게


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
        size = 84 if (i == 0 and n > 1) else (112 if len(line) <= 10 else 90)  # 긴 줄은 작게
        y = base_y + i * 150 - (20 if i == 0 and n > 1 else 0)
        f.append(f"drawtext=expansion=none:fontfile={esc(FONT)}:textfile={textfile(f'{sid}_{i}', line)}:fontsize={size}:"
                 f"fontcolor={color}:borderw=9:bordercolor=black:shadowx=0:shadowy=6:shadowcolor=black@0.6:"
                 f"x=(w-tw)/2:y={y}+12*max(0\\,1-t/0.18):alpha='min(1,t/0.18)'")
    if sid in SOURCE:
        f.append(f"drawtext=expansion=none:fontfile={esc(FONT_M)}:textfile={textfile(sid + '_src', SOURCE[sid])}:fontsize=30:"
                 f"fontcolor=white@0.75:x=(w-tw)/2:y=1470")
    return f


def render_scene(sid, cap, dur):
    parts = SCENES[sid]
    inputs, chains = [], []
    for k, (name, ss, frac, *opt) in enumerate(parts):
        ax = opt[0] if opt else 0.5   # 가로 크롭 위치 (0=왼쪽, 0.5=가운데, 1=오른쪽)
        d = dur * frac
        inputs += ["-ss", str(ss), "-t", f"{d + 0.1:.3f}", "-i", str(CLIPS / f"{name}.mp4")]
        # 화면 꽉 채우기(9:16 크롭) + 천천히 줌인
        chains.append(
            f"[{k}:v]fps={FPS},scale={int(W*1.15)}:{int(H*1.15)}:force_original_aspect_ratio=increase,"
            f"crop={int(W*1.15)}:{int(H*1.15)}:x=(iw-ow)*{ax}:y=(ih-oh)/2,"
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
              "acompressor=threshold=-20dB:ratio=3:attack=5:release=80,loudnorm=I=-16:TP=-2,aresample=48000,aformat=channel_layouts=stereo[voice]")
    run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(fc), "-map", "[voice]", str(B / "voice.wav")])
    # 3) 배경음악 + 첫 장면 '쿵' 한 번 (장면 전환 효과음은 없음)
    #    내레이션이 나올 때 음악이 자동으로 작아짐(사이드체인 더킹)
    hit = "aevalsrc='0.9*sin(2*PI*(60-30*t)*t)*exp(-4*t)':s=48000:d=1.2"
    fc = (f"[0:a]aresample=48000,aformat=channel_layouts=stereo,volume={MUSIC_VOL},"
          f"atrim=duration={total:.3f},afade=t=in:d=0.2,afade=t=out:st={total-2:.3f}:d=2[bgm];"
          f"[1:a]aformat=channel_layouts=stereo,volume=0.7[hit];"
          f"[bgm][hit]amix=inputs=2:normalize=0[music];"
          f"[2:a]asplit=2[vo][sc];"
          f"[music][sc]sidechaincompress=threshold=0.04:ratio=4:attack=30:release=400[duck];"
          f"[duck][vo]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[out]")
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(MUSIC_START), "-i", str(MUSIC), "-f", "lavfi", "-i", hit,
         "-i", str(B / "voice.wav"), "-filter_complex", fc, "-map", "[out]", "-ar", "48000", str(B / "mix.wav")])
    # 4) 합치기
    run(["ffmpeg", "-v", "error", "-y", "-i", str(B / "video.mp4"), "-i", str(B / "mix.wav"),
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(B / "final.mp4")])
    print("done", round(total, 2), "sec ->", B / "final.mp4")


if __name__ == "__main__":
    main()
