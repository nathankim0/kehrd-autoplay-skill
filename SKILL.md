---
name: kehrd-autoplay
description: Use ego-browser to monitor an open kehrd.com training player, advance completed videos, solve intermediate quizzes when requested, and notify and stop at 100% lesson progress. Use for 한국이러닝인재개발원 or KEHRD 교육 자동 진행 requests.
---

# KEHRD 교육 자동 진행

먼저 설치된 ego-browser 스킬을 읽고 `ego-browser skill`을 실행한다. 사용자가 지정한 TaskSpace와 플레이어 페이지를 재사용한다. 지정하지 않았다면 `listTaskSpaces()`와 해당 공간의 `tabs()`로 찾는다. 사용자 소유 공간은 사용자가 그 공간에서 작업하도록 요청했을 때만 claim한다. 로그인과 브라우저 권한 창은 사용자에게 맡긴다.

## 실행

SKILL.md가 있는 폴더에서 다음처럼 실행한다. 공간 ID와 페이지는 실제 관찰값으로 바꾸고 상태 폴더는 교육 세션별로 새로 정한다. `python3`, `ego-browser`가 필요하며 macOS에서는 `caffeinate`가 절전을 방지한다.

```bash
caffeinate -dimsu python3 scripts/watch.py --space 1 --page p2 --state-dir /private/tmp/kehrd-session
```

macOS 이외에는 `caffeinate -dimsu`만 빼고 실행한다. 기존 감시기가 있으면 먼저 소유 프로세스를 확인해 중복 실행을 정리한다. 이 감시기는 같은 상태 폴더에서 중복 실행되지 않는다.

명령은 에이전트 턴을 유지하며 실행하고 도구의 세션 ID로 계속 관찰한다. `progress.log`에 상태가 기록된다. 정상 재생을 기다리며 사용자에게 간결한 진행 상황을 알린다. `DONE` 또는 `QUESTION` 파일이 생기면 감시 프로세스가 종료된다. 종료 코드 0은 완료, 2는 화면 확인 필요, 그 외는 실행 오류다. 오류를 무한 재시도하지 않는다.

## 중간 문제와 정지 화면

이 스크립트는 문제를 임의로 찍지 않는다. `QUESTION`이 생기면 **에이전트가 계속 작업해야 한다**. 백그라운드 감시기만 남기고 앞으로 문제도 자동으로 푼다고 말하지 않는다.

1. 같은 페이지에서 새 snapshot을 확인한다. 캔버스/영상 안에 문제가 있으면 screenshot을 보고 읽는다. `QUESTION`은 대화상자, 재생 정지, 파싱 실패, 사용자 제어 전환에도 생길 수 있으므로 실제 화면으로 원인을 판단한다.
2. 사용자가 문제 풀이를 요청했다면 지문과 보기를 읽고 정답과 근거를 판단해 관찰한 선택지와 제출 버튼으로 진행한다. 안전보건/응급처치의 정확한 지식이나 법 기준이 불확실하면 공식 자료를 확인한다. 답안 키나 비공개 API를 조회하지 않는다. 틀렸다면 표시된 해설을 읽고 재시도 허용 범위에서 고친다.
3. 재생 정지라면 관찰한 재생 버튼을 사용한다. 대화상자는 내용을 읽고 처리한다. 사용자 제어 전환이나 공간 비활성화이면 중지하고 다시 권한을 빼앗지 않는다.
4. 정상 화면으로 돌아온 것을 확인한 뒤 해당 상태 폴더의 `QUESTION` 파일만 삭제하고 같은 명령을 다시 실행한다. 문제 화면이 계속되면 재생 재개를 반복 클릭하지 않는다.

기본 범위는 현재 차시의 진도율 100%까지다. 별도 요청 없이 다른 차시나 최종 평가로 넘어가지 않는다. 마지막 페이지에서도 진도 반영을 기다린다. 현재 사이트는 페이지별 최소 60초와 차시별 총 학습시간을 안내하므로 시간을 건너뛰거나 진도 데이터를 직접 수정하지 않는다.

## 완료와 검증

100%는 타이머가 없어도 먼저 감지하며 완료 알림을 띄우고 감시를 종료한다. `DONE` 파일의 snapshot으로 완료 상태를 보고하고, 사용자가 결과를 볼 플레이어 탭은 남긴다. 알림 실패는 `runner.log`에 기록되므로 알림이 실제 표시됐다고 단정하지 않는다.

개발 검증: `node scripts/test-watch.mjs`와 `python3 -m py_compile scripts/watch.py`.
