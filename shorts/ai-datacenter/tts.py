"""Edge TTS로 문장별 내레이션 생성 → assets/audio/{id}.wav + durations.json
사용: python tts.py [voice] [rate]   예) python tts.py ko-KR-InJoonNeural +8%
"""
import asyncio, json, os, subprocess, sys, edge_tts
VOICE = sys.argv[1] if len(sys.argv) > 1 else "ko-KR-InJoonNeural"
RATE = sys.argv[2] if len(sys.argv) > 2 else "+8%"
PROXY = os.environ.get("HTTPS_PROXY")  # 클라우드 환경에선 프록시 필요

async def main():
    dur = {}
    for s in json.load(open("script.json")):
        mp3, wav = f"assets/audio/{s['id']}.mp3", f"assets/audio/{s['id']}.wav"
        await edge_tts.Communicate(s["say"], VOICE, rate=RATE, proxy=PROXY).save(mp3)
        # 앞뒤 무음 제거 후 48kHz wav로 변환
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp3, "-af",
                        "silenceremove=start_periods=1:start_threshold=-50dB,areverse,"
                        "silenceremove=start_periods=1:start_threshold=-50dB,areverse",
                        "-ar", "48000", wav], check=True)
        os.remove(mp3)
        d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav],
                                 capture_output=True, text=True).stdout)
        dur[s["id"]] = round(d, 3); print(s["id"], dur[s["id"]])
    json.dump(dur, open("assets/audio/durations.json", "w"), indent=1)
    print("total", round(sum(dur.values()), 2))

asyncio.run(main())
