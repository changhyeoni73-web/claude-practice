# usage: pexels_dl.sh ID name  — Pexels CDN 파일명 패턴을 추측해서 받음 (세로 우선)
id=$1; name=$2
for res in 1080_1920 1440_2560 720_1280 1920_1080 1280_720 2560_1440 3840_2160 2160_3840; do
  case $res in 3840_2160|2160_3840|1440_2560|2560_1440) q=uhd;; *) q=hd;; esac
  for fps in 25 30 24 50 60 29 23 59 48; do
    u="https://videos.pexels.com/video-files/$id/$id-${q}_${res}_${fps}fps.mp4"
    c=$(curl -s -m 15 -o /dev/null -w "%{http_code}" -I "$u")
    if [ "$c" = 200 ]; then curl -s -m 300 -o "$name.mp4" "$u" && echo "OK $name $id $res ${fps}fps" && exit 0; fi
  done
done; echo "FAIL $name $id"
