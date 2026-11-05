# 유튜브 숏폼 작업 — 다음 할 일 (주말)

## 지금까지 한 것
- 테크 "이거 알고 계셨나요?" 숏폼 1편 완성: `ai-datacenter/` (v3, 53.8초)
  - 주제: AI 데이터센터와 물·전기 사용 (미국 주민투표 41곳 중 1곳 빼고 반대)
  - 스타일: 참고 영상(리뷰엉이 "성게알은 사실 알이 아니다?") 형식
    - 상단 연두색 질문형 고정 제목, 가운데 영상 띠, 하단 말 맞춤 자막, 해요체 내레이션
  - 다시 만들기: `cd ai-datacenter && python tts.py && python thumbnail.py && python build.py`
  - 썸네일: 맨 앞 1초 (`thumbnail.py`, 문구는 script.json의 "thumbnail")
    (클립은 `assets/clips/pexels_dl.sh <ID> <이름>`으로 다시 받기, 음악은 incompetech에서 Investigations.mp3)
- 영상 관련 스킬 설치: `.claude/skills/` (HyperFrames, watch, graphify, ECC 영상 스킬)

## 할 일
1. **유튜브 운영 계획 짜기**
   - 업로드 주기(예: 주 3편), 목표(구독자/조회수), 제작 루틴(주제 찾기 → 대본 → 빌드 → 업로드)
2. **유튜브 카테고리 정하기**
   - 테크로 시작 → 확장할 분야 후보 정리 (과학, 생활 꿀팁, 경제 등)
   - 채널 이름·소개·썸네일 톤 정하기
3. **유튜브 영상 스타일 학습하기**
   - 참고 채널 영상 여러 개 분석 → 제목 패턴, 첫 3초 훅, 컷 길이, 말투 정리
   - 쓸 만한 스킬: `watch`(영상 보고 분석), `taste-distillation`(컷 리듬·색감 수치화)
   - 참고: 유튜브 영상 다운로드는 이 클라우드 환경에서 막혀 있음 → 영상 파일을 직접 올리거나 다른 방법 필요
4. **유튜브 자동 업로드 하기**
   - YouTube Data API v3 (OAuth 클라이언트 필요) → 제목·설명·태그·공개 예약까지 자동화
   - 설명란에 음악 출처 문구 자동 삽입

## 업로드 전 체크리스트
- 설명란 음악 출처 (필수, CC BY 4.0):
  ```
  Music: "Investigations" by Kevin MacLeod (incompetech.com)
  Licensed under Creative Commons: By Attribution 4.0
  http://creativecommons.org/licenses/by/4.0/
  ```
- TTS: Edge TTS는 상업적 사용 조건이 애매함 → 수익 창출 전에 Azure TTS / ElevenLabs 등 상업 라이선스로 교체 검토
- 영상 클립: Pexels (상업적 사용 가능, 출처 표기 불필요)
