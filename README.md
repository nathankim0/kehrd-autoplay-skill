<div align="center">

<img src="assets/cover.png" alt="KEHRD Autoplay" width="100%">

# KEHRD Autoplay

남은 KEHRD 교육을 순서대로 진행하는 Codex · Claude Code 스킬.

![Codex](https://img.shields.io/badge/Codex-Skill-111827?style=flat-square)
![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-D97757?style=flat-square)

</div>

## 설치

**필요:** ego-browser CLI와 스킬, Python 3, 로그인된 Codex CLI. macOS·Linux를 지원합니다.

**Codex**

```bash
mkdir -p "$HOME/.codex/skills"
git clone https://github.com/nathankim0/kehrd-autoplay-skill.git "$HOME/.codex/skills/kehrd-autoplay"
```

**Claude Code**

```bash
mkdir -p "$HOME/.claude/skills"
git clone https://github.com/nathankim0/kehrd-autoplay-skill.git "$HOME/.claude/skills/kehrd-autoplay"
```

설치 후 새 세션에서 사용하세요. 업데이트는 설치 폴더에서 `git pull --ff-only`.

## 사용

```text
$kehrd-autoplay로 교육 진행해줘.
```

Claude Code에서는 `/kehrd-autoplay`로 시작합니다.

- **로그인:** 제공한 아이디·비밀번호나 로그인 링크가 있으면 에이전트가 로그인합니다. 없으면 열린 브라우저에서 직접 로그인한 뒤 “로그인 완료”라고 알려주세요. 인증정보는 별도 저장하지 않습니다.
- **교육:** 기본으로 남은 차시·과정 전체를 진행합니다. 영상 종료와 진도율 100%를 확인하고, 필요한 평가를 처리한 뒤 다음 교육으로 이어갑니다.
- **문제·평가:** 필요할 때만 GPT-6.1 Terra(low)를 호출합니다. 한도가 소진되면 다른 로그인된 Codex 계정 → Claude Sonnet(low)으로 이어받습니다. 각 CLI 사용량이 적용됩니다.
- **절전 방지:** macOS에서는 활성화된 Amphetamine·caffeinate를 재사용합니다. 없을 때만 감시기용 caffeinate를 실행합니다.

본인인증·CAPTCHA는 직접 처리해야 합니다. 로그인 만료·사이트 변경 등 해결할 수 없는 오류는 기록 후 중지합니다.

<details>
<summary>감시기 직접 실행</summary>

로그인과 플레이어 준비를 마친 뒤 저장소 폴더에서 실행합니다. 페이지 값은 실제 열린 탭에 맞추고 상태 폴더는 세션마다 새로 지정하세요.

```bash
python3 scripts/watch.py --space 1 --page p2 --state-dir /tmp/kehrd-session
```

과정 상세 탭은 기본 `p1`입니다. 다르면 `--playlist-page`로 지정하세요.

| 옵션 | 동작 |
| --- | --- |
| `--current-lesson-only` | 현재 차시 100%에서 종료 |
| `--no-auto-agent` | 자동 Codex 호출 해제. 주 에이전트가 문제·평가를 처리해야 함 |

</details>

운영·복구·검증 절차는 [SKILL.md](SKILL.md), 구현과 테스트는 [scripts/](scripts/)를 참고하세요.
