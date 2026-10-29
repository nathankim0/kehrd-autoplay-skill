<div align="center">

<img src="assets/cover.png" alt="KEHRD Autoplay" width="100%">

# KEHRD Autoplay

**교육 시작부터 수료증 저장까지, 한 번의 요청으로.**

한국이러닝인재개발원(KEHRD)의 남은 교육을 진행하는 Codex · Claude Code 스킬.

[![Release](https://img.shields.io/github/v/release/nathankim0/kehrd-autoplay-skill?style=flat-square)](https://github.com/nathankim0/kehrd-autoplay-skill/releases/latest)
![Codex](https://img.shields.io/badge/Codex-Skill-111827?style=flat-square)
![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-D97757?style=flat-square)

[빠른 시작](#빠른-시작) · [기본 동작](#기본-동작) · [지원 환경](#지원-환경)

</div>

## 빠른 시작

**준비물:** [ego lite](https://lite.ego.app/)와 ego-browser 스킬, Git, Python 3, 로그인된 Codex CLI 또는 Claude Code CLI.

**1. 사용하는 에이전트에 설치하세요.**

Codex:

```bash
mkdir -p "$HOME/.codex/skills"
git clone https://github.com/nathankim0/kehrd-autoplay-skill.git "$HOME/.codex/skills/kehrd-autoplay"
```

Claude Code:

```bash
mkdir -p "$HOME/.claude/skills"
git clone https://github.com/nathankim0/kehrd-autoplay-skill.git "$HOME/.claude/skills/kehrd-autoplay"
```

**2. 새 에이전트 세션에서 요청하세요.**

```text
$kehrd-autoplay로 교육 진행해줘.
```

Claude Code에서는 `/kehrd-autoplay`로 시작하세요. 로그인된 세션이나 제공한 계정 정보·학습 링크를 사용하며, 없으면 브라우저 로그인을 안내합니다.

## 기본 동작

**로그인 → 남은 차시·과정 → 문제·평가 → 수료증 PDF → 완료 알림**

- **전체 교육 진행:** 재생 시간과 수료 조건을 확인하며 다음 차시·과정으로 이어갑니다.
- **문제와 정지 화면 처리:** 중간 문제·평가·제출 확인창을 처리하고 재생을 복구합니다.
- **한도 소진 시 계정 전환:** 다른 로그인된 Codex 계정 → Claude Sonnet으로 이어받습니다.
- **수료증까지 저장:** 모든 PDF의 저장을 확인한 뒤 개수와 저장 위치를 알립니다. 중단 후 정상 파일은 재사용합니다.

수료증: `~/Downloads/KEHRD-수료증/<세션명>/`. 비밀번호·학습 링크는 별도 저장하지 않으며 수료증은 로컬에 보관합니다.

영상은 스크립트가 감시하고, 문제·복구·정기 점검 때만 GPT-6.1 Terra(low) 또는 Claude Sonnet(low)를 호출합니다. 각 CLI의 요금·사용 한도가 적용됩니다.

## 지원 환경

| 기능 | macOS | Linux |
| --- | --- | --- |
| 교육 진행·수료증 PDF | 실제 사이트 검증 완료 | 실기 미검증 |
| 완료 안내 | 저장 위치를 담은 팝업 | `notify-send` 또는 터미널 출력 |
| 절전 방지·30분 정기 점검 | 지원 | 자동 설정 미지원 |

30분 점검은 “30분마다 확인해줘”라고 요청하면 설정됩니다. 본인인증·CAPTCHA는 직접 처리해야 하며, 재로그인이나 사이트 변경으로 복구할 수 없으면 이유를 남기고 중지합니다.

업데이트는 설치 폴더에서 `git pull --ff-only` 후 새 세션을 시작하세요.

[직접 실행·복구 가이드](SKILL.md) · [구현·테스트](scripts/) · [문제 제보](https://github.com/nathankim0/kehrd-autoplay-skill/issues)
