# GitHub 업로드 안내

이 폴더는 양력 전용 MVP 출시본입니다.

GitHub에는 현재 폴더의 내용만 올립니다.

```text
release_solar_mvp/
```

원본 작업 폴더 전체를 올리면 안 됩니다.

## 방법 A. GitHub 웹 업로드

Git이 설치되어 있지 않아도 진행할 수 있는 방식입니다.

1. GitHub에 접속합니다.
2. 새 저장소를 만듭니다.
3. 저장소 이름을 정합니다.
   - 예: `saju-solar-mvp`
4. 공개 여부를 선택합니다.
   - 바로 출시할 목적이면 `Public`
   - 도메인 연결 전 비공개 검토가 필요하면 `Private`
5. `uploading an existing file`을 선택합니다.
6. `release_solar_mvp` 폴더 안의 파일과 폴더를 모두 업로드합니다.
7. 커밋 메시지는 다음처럼 적습니다.

```text
Initial solar MVP release
```

압축본을 사용할 경우에는 ZIP 파일 자체를 GitHub에 올리지 말고, 압축을 푼 뒤 그 안의 파일과 폴더를 업로드합니다.

## 방법 B. Git 설치 후 명령줄 업로드

Git이 설치되면 아래 명령을 `release_solar_mvp` 폴더에서 실행합니다.

```bash
git init
git add .
git commit -m "Initial solar MVP release"
git branch -M main
git remote add origin https://github.com/USER_OR_ORG/REPOSITORY_NAME.git
git push -u origin main
```

`USER_OR_ORG`와 `REPOSITORY_NAME`은 실제 GitHub 계정과 저장소 이름으로 바꿉니다.

## 업로드 전 확인

아래 파일과 폴더가 들어가야 합니다.

- `saju_web`
- `saju_analysis_engine`
- `saju_birth_engine`
- `web_app.py`
- `README.md`
- `requirements.txt`
- `runtime.txt`
- `Procfile`
- `render.yaml`

아래 파일은 들어가면 안 됩니다.

- PDF 원자료
- 작업 보고서
- `tmp_`로 시작하는 파일
- `.log`
- `__pycache__`
- `.pyc`
- 원본 작업 폴더의 전체 내용
