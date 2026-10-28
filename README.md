<div align="center">

<img src="assets/cover.png" alt="KEHRD Autoplay — 한국이러닝인재개발원 아이콘과 영상 자동 진행·100% 완료를 표현한 대문 이미지" width="100%">

# KEHRD Autoplay

**교육 영상은 순서대로, 중간 문제는 에이전트와 함께.**

한국이러닝인재개발원(kehrd.com)의 열린 교육 플레이어를 감시하고,<br>
영상이 끝나면 다음 페이지로 이동하고, **기본으로 남은 차시·과정 전체**를 순서대로 이어가는 에이전트 스킬입니다.

![Codex](https://img.shields.io/badge/Codex-Skill-111827?style=flat-square)
![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-D97757?style=flat-square)
![Browser](https://img.shields.io/badge/Browser-ego--browser-2563EB?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-macOS_%C2%B7_Linux-64748B?style=flat-square)

[설치](#설치) · [바로 사용하기](#바로-사용하기) · [동작 방식](#동작-방식) · [직접 실행](#직접-실행)

</div>

---

## 할 수 있는 일

| 기능 | 동작 |
| --- | --- |
| 영상 자동 진행 | 재생 시간과 페이지 번호를 확인하고 영상이 끝났을 때 다음 페이지로 이동 |
| 진도율 확인 | 기본은 100% 이후 다음 미완료 교육으로 이동, 현재 차시만 지정하면 종료 |
| 전체 과정 진행 | 차시 100% → 필요한 평가 처리 → 다음 차시 → 다음 미수료 과정 |
| 중간 문제 처리 | 문제를 감지하면 실행 중인 에이전트가 지문·보기를 읽고, 요청받은 문제 풀이 진행 |
| 정지 화면 확인 | 재생 정지·대화상자·알 수 없는 화면에서 에이전트가 상태 확인 |
| macOS 알림 | 완료 또는 화면 확인이 필요할 때 시스템 알림 요청 |
| 중복 실행 방지 | 같은 상태 폴더를 사용하는 감시기의 중복 실행 차단 |

> **문제·평가 풀이는 에이전트가 담당합니다.** 감시기는 문제·평가가 나와도 종료하지 않습니다. 별도 에이전트 자동 실행을 허용하고 `--auto-agent`를 사용하면, 대화 종료 후에도 **GPT-6.1 Terra**를 필요할 때 호출해 제출 확인창·결과 알림·다음 영상 재생까지 처리합니다.

## 설치

먼저 `ego-browser` CLI와 해당 에이전트용 ego-browser 스킬, Python 3를 준비하세요. 로그인이나 플레이어 준비는 아래 첫 실행 과정에서 진행합니다.

**Codex**

```bash
mkdir -p "$HOME/.codex/skills"
git clone https://github.com/nathankim0/kehrd-autoplay-skill.git \
  "$HOME/.codex/skills/kehrd-autoplay"
```

**Claude Code**

```bash
mkdir -p "$HOME/.claude/skills"
git clone https://github.com/nathankim0/kehrd-autoplay-skill.git \
  "$HOME/.claude/skills/kehrd-autoplay"
```

설치 후 새 에이전트 세션에서 사용하세요. 이미 설치했다면 해당 폴더에서 `git pull --ff-only`로 업데이트할 수 있습니다.

## 바로 사용하기

처음 설치한 사람도 로그인된 탭이나 TaskSpace 번호를 미리 준비할 필요 없이 시작할 수 있습니다. Codex에서는 다음처럼 요청하세요.

```text
$kehrd-autoplay로 교육 진행해줘.
```

### 처음 쓰는 사람의 로그인

1. 에이전트가 KEHRD 사이트를 열고 로그인 상태를 확인합니다.
2. **아이디·비밀번호나 학습 로그인 링크를 이미 제공했다면 에이전트가 입력·제출까지 진행합니다.** 다시 직접 입력하라고 요청하지 않습니다.
3. 인증정보를 제공하지 않았다면 브라우저 제어를 넘깁니다. 열린 로그인 화면에 직접 입력한 뒤 **“로그인 완료”**라고 알려주세요. 채팅이나 저장소에 비밀번호를 적을 필요는 없습니다.
4. 에이전트가 같은 브라우저에서 내강의실 → 미완료 과정 → 첫 미완료 차시를 찾아 재생과 감시를 시작합니다.

이미 로그인되어 있다면 입력 단계를 건너뜁니다. 사용자가 직접 제공한 인증정보는 로그인에만 사용하며, 답변에 다시 표시하거나 별도 파일·로그·저장소에 저장하지 않습니다. 이후에는 브라우저에 남은 로그인 세션을 사용합니다. 본인인증이나 CAPTCHA가 뜨면 직접 처리하고, 세션이 만료되면 다시 로그인하면 됩니다.

Claude Code에서는 `/kehrd-autoplay`를 호출하거나 같은 내용을 자연어로 요청합니다. 이미 열어둔 공간과 페이지를 알고 있다면 함께 알려주세요.

```text
TaskSpace 1의 p1은 과정 상세, p2는 플레이어야. 교육 진행해줘.
```

“전부”라고 덧붙이지 않아도 남은 차시·과정과 필요한 문제·평가를 이어가며 전체 수료 후 알려줍니다. 현재 차시만 진행하려면 그 범위를 명시하세요.

## 동작 방식

```mermaid
flowchart LR
    A[열린 교육 플레이어] --> B{상태 확인}
    B -->|영상 종료| C[다음 페이지]
    C --> B
    B -->|문제 · 정지 화면| D[에이전트가 확인 · 처리]
    D --> B
    B -->|차시 100% · 마지막 영상 완료| G[필요한 평가 · 다음 미완료 교육]
    G -->|남은 교육 있음| B
    G -->|전체 수료 확인| F[완료 알림 · 종료]
```

감시기는 약 10초마다 화면을 확인합니다. 짧은 감시 라운드를 이어서 실행하며, 문제나 확인이 필요한 화면에서는 `ACTION_REQUIRED`를 출력하고 에이전트가 처리하는 동안 대기합니다. 처리 완료 신호를 받으면 같은 프로세스가 자동 재개합니다. 중간 확인 알림으로 작업을 끝내지 않으며, 시스템 알림은 전체 완료 시에만 요청합니다.

기본으로 다음 차시와 과정으로 이어갑니다. 현재 차시만 명시적으로 요청한 경우에만 100%에서 멈춥니다. 일반 법정교육은 100% 자동 수료 여부를 확인하고, 산업안전보건교육은 차시별 평가 합격 등 화면에 표시된 수료 조건까지 확인합니다. 사이트가 요구하는 순서와 학습시간을 지키며, 잠금을 우회하거나 진도 데이터를 직접 수정하지 않습니다.

## 직접 실행

아래는 로그인과 플레이어 준비를 마친 뒤 감시기만 직접 실행하는 방법입니다. 처음 사용한다면 위 스킬 호출 방식으로 시작하세요. 저장소 폴더에서 `--space`와 `--page`를 실제 열린 플레이어 값으로 바꾸고, 상태 폴더는 교육 세션마다 새로 지정합니다.

```bash
# macOS: 감시가 실행되는 동안 절전 방지
caffeinate -dimsu python3 scripts/watch.py \
  --space 1 --page p2 --state-dir /private/tmp/kehrd-session
```

Linux에서는 `caffeinate -dimsu`를 빼고, 상태 폴더를 `/tmp/kehrd-session` 등으로 지정합니다. Windows는 지원하지 않습니다.

**전체 진행이 기본값**입니다. 상세 페이지는 기본 `p1`이며, 다른 탭이라면 `--playlist-page p3`처럼 지정합니다. 특정 과정만 요청했다면 에이전트가 그 범위 안에서 전환을 관리합니다.

**현재 차시만 진행**하려면 다음 옵션을 명시합니다.

```bash
caffeinate -dimsu python3 scripts/watch.py \
  --space 1 --page p2 --current-lesson-only \
  --state-dir /private/tmp/kehrd-one-lesson
```

기본 실행에서는 차시가 100%가 되고 마지막 영상까지 끝나면 플레이어를 종료하고 다음 미완료 차시를 엽니다. 모든 차시를 마치면 내강의실 목록에서 다음 미수료 과정을 찾습니다. 평가나 잠금 해제가 필요하면 에이전트가 처리한 뒤 이어가며, 목록 전체의 수료를 확인하면 종료합니다. 알 수 없는 수료 상태에서는 완료로 판단하지 않습니다.

### 대화가 끝난 뒤에도 자동 처리

별도 에이전트 실행을 허용한 경우 다음처럼 실행합니다. 로그인된 Codex CLI가 필요하며, CLI의 사용량이 적용됩니다.

```bash
caffeinate -dimsu python3 scripts/watch.py \
  --space 1 --page p2 --state-dir /private/tmp/kehrd-all-session --auto-agent
```

영상 재생 중에는 모델을 호출하지 않습니다. 문제·평가·정지 화면이 감지될 때만 `gpt-6.1-terra`를 reasoning `low`로 호출하고, 복구를 마치면 감시기가 이어받습니다. 같은 문제를 해결하지 못하거나 실행 오류·10분 제한에 걸리면 사유를 기록하고 반복 호출하지 않습니다. `--auto-agent`를 쓰지 않으면 주 에이전트가 계속 실행되어 있어야 문제 풀이가 진행됩니다.

| 상태 파일 | 의미 |
| --- | --- |
| `progress.log` | 페이지·재생 시간·진도율 기록 |
| `latest.snapshot` | 가장 최근에 관찰한 화면 |
| `runner.log` | 브라우저 실행 출력과 알림 오류 |
| `agent.log` | 자동 호출한 Terra 에이전트의 실행 기록 |
| `agent-last-message.txt` | 가장 최근 자동 에이전트의 처리 결과 |
| `QUESTION` | 문제·정지·대화상자·오류 등 화면 확인 필요 |
| `STOP` | 사용자 제어 전환 등으로 감시 중지 |
| `DONE` | 단일 차시 100% 또는 전체 과정 수료 확인 화면 |
| `player.json` | 전체 모드에서 현재 플레이어의 페이지 라벨 |
| `playlist.json` | 전체 모드에서 확인한 과정별 수료 상태 |
| `lesson-completed.snapshot` | 가장 최근에 100%를 달성한 차시 화면 |
| `watch.lock` | 같은 상태 폴더의 중복 실행을 막는 잠금 |

종료 코드 **0**은 완료, **2**는 중지, 그 외는 실행 오류입니다. `QUESTION`에서는 프로세스가 종료되지 않습니다. 에이전트가 제출 확인창·결과 알림과 다음 영상 재생까지 확인한 뒤 해당 파일을 삭제하면 자동 재개합니다. 평가 후 새 플레이어를 열었다면 삭제 전에 `player.json`도 새 페이지 라벨로 갱신합니다. 감시기가 실행 중이면 새 감시기를 띄우지 않습니다. `DONE` 또는 `STOP`이 있는 폴더에서는 새 교육을 시작하지 않습니다.

상태 파일에는 학습 화면의 개인정보가 포함될 수 있으므로 저장소 밖의 로컬 폴더에 보관하세요. 시스템 알림 표시는 macOS 알림 설정에 따라 달라질 수 있습니다.

## 검증과 구성

```bash
node scripts/test-watch.mjs
node scripts/test-playlist.mjs
node scripts/test-dialogs.mjs
python3 scripts/test-watch.py
python3 -m py_compile scripts/watch.py
```

동작 검증은 100%·문제 감지, 영상 종료 전 이동 방지와 페이지 이동, 차시·과정 전환, 평가 대기, 잠긴 과정·알 수 없는 상태의 중지를 확인합니다. 실제 사이트의 전체 교육 과정을 대신 검증하지는 않습니다.

| 파일 | 역할 |
| --- | --- |
| [SKILL.md](SKILL.md) | 에이전트의 실행·문제 풀이·복구 절차 |
| [scripts/watch.py](scripts/watch.py) | 감시 라운드 실행·잠금·종료 알림 |
| [scripts/watch.mjs](scripts/watch.mjs) | ego-browser로 플레이어 상태 확인·페이지 이동 |
| [scripts/playlist.mjs](scripts/playlist.mjs) | 다음 차시·과정 전환과 전체 수료 확인 |
| [scripts/dialogs.mjs](scripts/dialogs.mjs) | 알려진 제출 확인창·결과 알림 연속 처리 |
| [scripts/agent-task.md](scripts/agent-task.md) | 자동 에이전트가 한 번에 수행할 문제·평가 복구 범위 |
| [scripts/test-watch.mjs](scripts/test-watch.mjs) | 모의 화면으로 감시 동작 검증 |
| [scripts/test-playlist.mjs](scripts/test-playlist.mjs) | 모의 내강의실로 전체 진행 동작 검증 |
| [scripts/test-dialogs.mjs](scripts/test-dialogs.mjs) | 제출 확인·정답 알림 연속 처리 검증 |
| [scripts/test-watch.py](scripts/test-watch.py) | 문제 처리 중 감시 유지·자동 재개 검증 |

플레이어의 화면 구조가 바뀌면 파싱과 문제 감지를 조정해야 합니다. 영상·캔버스 내부의 문제는 재생 정지 시 에이전트가 스크린샷으로 확인합니다.

대문 이미지는 [KEHRD 공식 아이콘](https://kehrd.com/img/favicon.ico)을 참고해 ImageGen으로 제작했습니다. [생성 프롬프트](assets/cover-prompt.txt)
