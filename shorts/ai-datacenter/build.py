"""AI 데이터센터 숏폼 v3 조립 스크립트 (1080x1920, 30fps).

레이아웃(참고 영상 스타일):
  - 상단: 영상 내내 고정되는 연두색 질문형 제목 2줄
  - 가운데: 영상 띠 (위아래 검은 여백)
  - 하단: 말과 함께 바뀌는 작은 흰색 자막 (TTS 단어 타이밍 기반)

사용: python3 build.py  →  build/final.mp4
입력: script.json, assets/audio/{id}.wav + timing.json (tts.py), assets/clips/*.mp4, assets/music/*.mp3
"""
import json, subprocess, pathlib

ROOT = pathlib.Path(__file__).parent
B = ROOT / "build"; B.mkdir(exist_ok=True)
CLIPS = ROOT / "assets/clips"; AUD = ROOT / "assets/audio"
FONT_TITLE = ROOT / "assets/fonts/Pretendard-Black.otf"
FONT_SUB = ROOT / "assets/fonts/Pretendard-SemiBold.otf"
W, H, FPS = 1080, 1920, 30
BAND_Y, BAND_H = 430, 1100          # 영상 띠 위치/높이
TITLE_COLOR = "0xD4FF3A"            # 형광 연두
SUB_Y = 1590                        # 하단 자막 위치 (Shorts UI에 안 가리도록)
GAP = 0.12                          # 문장 사이 기본 쉼 (호흡을 빠르게)
GAP_AFTER = {"s1": 0.25, "s3": 0.3, "s4": 0.35, "s9": 0.3}
SUB_MAX = 16                        # 자막 한 덩어리 최대 글자 수(공백 포함)

# 배경음악: "Investigations" Kevin MacLeod (incompetech.com), CC BY 4.0 — 영상 설명란에 출처 표기 필요
MUSIC = ROOT / "assets/music/Investigations.mp3"
MUSIC_VOL = 0.50

# 장면별 클립: (파일, 원본 시작초, 비율[, 가로 크롭 위치 0~1])
SCENES = {
    "s1":  [("phone_typing", 0.5, 1.0)],
    "s2":  [("vote_people", 0.5, 0.5, 0.25), ("ballot_boxes", 1.0, 0.5)],
    "s3":  [("people_voting", 2.0, 1.0)],
    "s4":  [("server", 3.0, 1.0)],
    "s5":  [("water_drops", 2.0, 1.0)],
    "s6":  [("cpu", 2.0, 1.0)],
    "s7":  [("city_night", 0.3, 0.55), ("server", 15.0, 0.45)],
    "s8":  [("steam_plant", 4.0, 0.5), ("transmission", 6.0, 0.5)],
    "s9":  [("dry_lake", 5.0, 0.5), ("protest", 10.0, 0.5)],
    "s10": [("phone_thinking", 6.0, 1.0)],
}


def run(cmd):
    subprocess.run(cmd, check=True)


def esc(p):
    return str(p).replace(":", r"\:")


def textfile(name, text):
    p = B / f"txt_{name}.txt"; p.write_text(text, encoding="utf-8"); return esc(p)


def render_band(sid, dur):
    """장면 하나를 1080xBAND_H 영상 띠로 렌더링."""
    parts = SCENES[sid]; inputs, chains = [], []
    for k, (name, ss, frac, *opt) in enumerate(parts):
        ax = opt[0] if opt else 0.5
        d = dur * frac; ZW, ZH = int(W * 1.08), int(BAND_H * 1.08)
        inputs += ["-ss", str(ss), "-t", f"{d + 0.1:.3f}", "-i", str(CLIPS / f"{name}.mp4")]
        chains.append(
            f"[{k}:v]fps={FPS},scale={ZW}:{ZH}:force_original_aspect_ratio=increase,"
            f"crop={ZW}:{ZH}:x=(iw-ow)*{ax}:y=(ih-oh)/2,"
            f"scale=w='{W}*(1.08-0.06*t/{d:.3f})':h=-2:eval=frame,"      # 아주 느린 줌인
            f"crop={W}:{BAND_H},setsar=1,trim=duration={d:.3f},setpts=PTS-STARTPTS[c{k}]")
    cat = "".join(f"[c{k}]" for k in range(len(parts)))
    fc = ";".join(chains) + f";{cat}concat=n={len(parts)}:v=1:a=0,eq=saturation=1.08:contrast=1.03[v]"
    out = B / f"band_{sid}.mp4"
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[v]", "-t", f"{dur:.3f}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS), str(out)])
    return out


def chunk_words(words, say, manual=None):
    """단어 타이밍 → 자막 덩어리 [(start, text)].
    TTS 단어에는 문장부호가 빠져 있어서, 대본 원문 어절(문장부호 포함)로 바꿔 끼운 뒤
    문장부호에서 끊고, 너무 길어지면 그 전에 끊음."""
    tokens = say.split()
    if len(tokens) == len(words):
        words = [[a, b, tok] for (a, b, _), tok in zip(words, tokens)]
    if manual and len(manual.replace("|", " ").split()) == len(words):   # 대본의 "sub"로 직접 끊기
        out, i = [], 0
        for part in manual.split("|"):
            n = len(part.split()); out.append((words[i][0], part.strip().rstrip(",."))); i += n
        return out
    chunks, cur, start = [], [], None
    for a, b, t in words:
        n = len(" ".join(cur + [t]))
        # 넘치면 먼저 끊기 — 단, 문장부호로 끝나는 짧은 꼬리("같죠?")는 고아가 되지 않게 붙여줌
        if cur and n > SUB_MAX and not (t[-1] in ",.?!" and n <= SUB_MAX + 6):
            chunks.append((start, " ".join(cur))); cur, start = [], None
        if start is None: start = a
        cur.append(t)
        if t[-1] in ",.?!":                                   # 문장부호에서 끊기
            chunks.append((start, " ".join(cur))); cur, start = [], None
    if cur: chunks.append((start, " ".join(cur)))
    return [(s, txt.rstrip(",.")) for s, txt in chunks]


def main():
    sc = json.load(open(ROOT / "script.json")); timing = json.load(open(AUD / "timing.json"))
    lines = sc["lines"]
    bands, starts, durs, t = [], [], [], 0.0
    for s in lines:
        sid = s["id"]; dur = timing[sid]["dur"] + GAP_AFTER.get(sid, GAP)
        starts.append(t); durs.append(dur); t += dur
        bands.append(render_band(sid, dur)); print("band", sid, round(dur, 2))
    total = t

    # 자막 덩어리를 전체 타임라인 기준 시간으로 변환
    subs = []
    for s, st, dur in zip(lines, starts, durs):
        ch = chunk_words(timing[s["id"]]["words"], s["say"], s.get("sub"))
        for i, (a, text) in enumerate(ch):
            end = ch[i + 1][0] if i + 1 < len(ch) else dur - 0.02
            subs.append((st + a, st + end, text))

    # 1) 영상 띠 이어붙이기
    lst = B / "bands.txt"; lst.write_text("".join(f"file '{p}'\n" for p in bands))
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(B / "band_all.mp4")])

    # 2) 검은 화면 위에 띠 + 고정 제목 + 하단 자막 합성
    f = [f"[0:v]pad={W}:{H}:0:{BAND_Y}:black"]
    for i, line in enumerate(sc["title"].split("\n")):
        f.append(f"drawtext=expansion=none:fontfile={esc(FONT_TITLE)}:textfile={textfile(f'title{i}', line)}:"
                 f"fontsize=100:fontcolor={TITLE_COLOR}:x=(w-tw)/2:y={150 + i * 125}")
    for i, (a, b, text) in enumerate(subs):
        f.append(f"drawtext=expansion=none:fontfile={esc(FONT_SUB)}:textfile={textfile(f'sub{i}', text)}:"
                 f"fontsize=54:fontcolor=white:borderw=3:bordercolor=black@0.8:x=(w-tw)/2:y={SUB_Y}:"
                 f"enable='between(t,{a:.3f},{b:.3f})'")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(B / "band_all.mp4"), "-vf", ",".join(f),
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", str(B / "video.mp4")])

    # 3) 내레이션: 문장 + 쉼 이어붙이기, 음량 정리
    ins, fc = [], []
    for k, (s, dur) in enumerate(zip(lines, durs)):
        ins += ["-i", str(AUD / f"{s['id']}.wav")]
        fc.append(f"[{k}:a]aresample=48000,apad,atrim=duration={dur:.3f}[a{k}]")
    fc.append("".join(f"[a{k}]" for k in range(len(lines))) + f"concat=n={len(lines)}:v=0:a=1,highpass=f=80,"
              "acompressor=threshold=-20dB:ratio=2.5:attack=5:release=80,loudnorm=I=-16:TP=-2,"
              "aresample=48000,aformat=channel_layouts=stereo[voice]")
    run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(fc), "-map", "[voice]", str(B / "voice.wav")])

    # 4) 배경음악 (내레이션 나올 때 자동으로 작아짐) + 최종 음량 -14 LUFS
    fc = (f"[0:a]aresample=48000,aformat=channel_layouts=stereo,volume={MUSIC_VOL},atrim=duration={total:.3f},"
          f"afade=t=in:d=0.3,afade=t=out:st={total - 2:.3f}:d=2[bgm];"
          f"[1:a]asplit=2[vo][sc];[bgm][sc]sidechaincompress=threshold=0.05:ratio=3:attack=30:release=400[duck];"
          f"[duck][vo]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[out]")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(MUSIC), "-i", str(B / "voice.wav"),
         "-filter_complex", fc, "-map", "[out]", "-ar", "48000", str(B / "mix.wav")])

    # 5) 합치기
    run(["ffmpeg", "-v", "error", "-y", "-i", str(B / "video.mp4"), "-i", str(B / "mix.wav"),
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(B / "final.mp4")])
    print("done", round(total, 2), "sec,", len(subs), "subtitle chunks ->", B / "final.mp4")


if __name__ == "__main__":
    main()
