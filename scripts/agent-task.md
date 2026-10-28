KEHRD 감시기의 한 번의 문제·평가·정지 화면 복구를 맡는다. 사용자는 남은 교육 전체 진행, 중간 문제와 차시 평가 답변·제출 및 별도 에이전트 자동 실행을 명시적으로 허용했다. 모델은 GPT-6.1 Terra다.

이 메시지의 복구 범위가 작업 전체다. 설치된 ego-browser 스킬을 읽고 ego-browser skill을 실행한다. 아래 Session의 기존 TaskSpace만 사용하고, 상태 폴더의 QUESTION, player.json과 실제 브라우저 화면으로 현재 위치를 파악한다. page 값보다 player.json의 라벨이 우선이다. 페이지가 닫혔다면 tabs()에서 상세·평가 팝업을 찾는다. 브라우저 제어 전환·비활성화·로그인이나 사용자 권한 창은 우회하지 말고 STOP 파일에 이유를 기록한다.

문제라면 실제 지문과 보기를 읽고 답변한다. 필요한 경우 공식 자료로 확인한다. 제출 버튼 이후의 시험 제출 확인과 정답 결과 알림도 연속 처리한다. scripts/dialogs.mjs의 settleTrainingDialogs(page, { allowSubmission: true, dialog: receipt.dialog })를 절대 경로로 import해 사용한다. receipt는 제출 클릭 결과다. 이 헬퍼는 page.events()의 대화상자 정보와 Page.handleJavaScriptDialog CDP 명령을 사용해, 알림창에 막히는 page.info()/acceptDialog() 경로를 피한다.

PageDialogOpenedError 또는 Runtime.evaluate 타임아웃이면 같은 info()/snapshot() 호출을 반복하지 않는다. 먼저 page.events()에서 Page.javascriptDialogOpening/Closed 이벤트를 확인하고 알려진 대화상자는 헬퍼로 처리한다. 이미 관찰한 정답 알림이 열린 것이 확실한데 이벤트를 다른 호출이 소비한 경우에만 page.cdp('Page.handleJavaScriptDialog', {accept:true}, {timeout:5000})로 닫는다. 이후 tabs()와 상세 페이지의 합격 상태부터 확인한다. attempt가 2이면 이전 실행의 제출이 성공했을 수 있으므로 현재 상태·agent.log를 먼저 확인하며 정답을 다시 제출하지 않는다. 예상하지 못한 메시지는 내용을 읽고 판단한다.

상세 페이지의 합격 상태를 확인하고 다음 미완료 차시의 학습하기를 눌러 실제 플레이어를 연다. 자동재생 제한 안내가 있으면 관찰한 안내 버튼을 누르고 타이머 증가까지 확인한다. 이미 정상 재생 중이면 다시 열거나 재생을 토글하지 말고 그대로 사용한다. 새 플레이어 라벨을 상태 폴더의 player.json에 {"page":"실제 라벨"} 형식으로 저장한다. 전부 끝났다면 내강의실의 전체 수료 상태를 확인하고 DONE에 화면 기록을 저장한다.

복구 또는 전체 수료를 확인한 뒤에만 QUESTION을 삭제하고 끝낸다. 감시기는 부모 프로세스가 계속 담당하므로 새 감시기·다른 에이전트를 실행하거나 다음 영상 종료를 기다리지 않는다. 다음 차시가 잠겨 있으면 실제 평가·수료 조건을 확인한다. 해결할 수 없는 장애는 STOP에 구체적으로 기록하고 QUESTION을 남긴다. 저장소 코드·설정은 수정하지 않으며 계정·토큰·개인별 답안은 공개하지 않는다. 사용자에게 추가 확인을 요구하는 대신 이미 허용된 학습 동작을 완료한다.
