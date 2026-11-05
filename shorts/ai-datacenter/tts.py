"""Edge TTS로 문장별 내레이션 + 단어 타이밍 생성
출력: assets/audio/{id}.wav, assets/audio/timing.json ({id: {dur, words:[[start,end,text],...]}})
사용: python tts.py [voice] [rate]   예) python tts.py ko-KR-InJoonNeural +5%
"""
import asyncio, json, os, subprocess, sys, edge_tts
VOICE = sys.argv[1] if len(sys.argv) > 1 else "ko-KR-InJoonNeural"
RATE = sys.argv[2] if len(sys.argv) > 2 else "+5%"
PROXY = os.environ.get("HTTPS_PROXY")  # 클라우드 환경에선 프록시 필요

async def synth(text, mp3):
    com = edge_tts.Communicate(text, VOICE, rate=RATE, proxy=PROXY, boundary="WordBoundary")
    words = []
    with open(mp3, "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio": f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                s = ch["offset"] / 1e7; words.append([round(s, 3), round(s + ch["duration"] / 1e7, 3), ch["text"]])
    return words

async def main():
    out = {}
    for s in json.load(open("script.json"))["lines"]:
        mp3, wav = f"assets/audio/{s['id']}.mp3", f"assets/audio/{s['id']}.wav"
        words = await synth(s["say"], mp3)
        lead = max(0.0, words[0][0] - 0.05)          # 앞쪽 무음은 첫 단어 0.05초 전까지 잘라냄
        end = words[-1][1] + 0.12                      # 뒤쪽 무음도 정리
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{lead:.3f}", "-to", f"{end:.3f}", "-i", mp3,
                        "-ar", "48000", wav], check=True)
        os.remove(mp3)
        words = [[round(a - lead, 3), round(b - lead, 3), t] for a, b, t in words]
        out[s["id"]] = {"dur": round(end - lead, 3), "words": words}
        print(s["id"], out[s["id"]]["dur"], len(words), "words")
    json.dump(out, open("assets/audio/timing.json", "w"), indent=1, ensure_ascii=False)
    print("total", round(sum(v["dur"] for v in out.values()), 2))

asyncio.run(main())
