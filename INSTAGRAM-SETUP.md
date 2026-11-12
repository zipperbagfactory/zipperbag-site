# 인스타그램 샘플 사진 자동 연동 설정

이 홈페이지는 **Instagram API with Instagram Login**을 사용합니다.
Meta의 공식 API를 통해 본인의 비즈니스 계정에 올라온 일반 사진 및
사진 캐러셀 게시물의 최신 이미지를 홈페이지 메인 사진칸에 표시합니다.

- 홈페이지 사진은 최대 5개를 순환합니다.
- GitHub Actions가 약 4시간마다 새 게시물을 확인합니다.
- 인스타그램 토큰이 준비되지 않은 동안 기존 PRODUCT PHOTOS 안내 화면이 유지됩니다.
- 방문자에게 API 토큰이 전달되거나 노출되지 않습니다.
- 일반 비디오 및 릴스는 사진 슬라이드에서 제외됩니다.

## 1. Meta에서 연결 승인

1. https://developers.facebook.com/apps/ 에서 본인 Meta 계정으로 로그인합니다.
2. 앱을 만들고 Instagram API의 **API setup with Instagram login**을 선택합니다.
   (Meta 화면에 따라 'Instagram → API setup with Instagram login'으로 보일 수 있습니다.)
3. 본인 Instagram **비즈니스 계정**을 추가하고 본인 계정으로 로그인하여 접근을 승인합니다.
4. 필요한 최소 권한은 **instagram_business_basic**입니다.
5. **Generate access token**을 이용해 본인 계정의 장기 액세스 토큰을 발급받습니다.
   화면에 표시된 토큰을 공개 저장소, 카카오톡, ChatGPT 대화, 코드 파일 등에 붙여넣지 마세요.

이 방식은 보통 별도의 Facebook 페이지 연결이 필요하지 않습니다.
Meta 대시보드의 메뉴 표기는 변경될 수 있습니다.

## 2. GitHub에 안전하게 등록

1. https://github.com/zipperbagfactory/zipperbag-site/settings/secrets/actions
2. **New repository secret**을 클릭합니다.
3. Name에 `INSTAGRAM_ACCESS_TOKEN` 입력
4. Secret 칸에 Meta에서 발급한 토큰 입력 후 저장

**주의:** `instagram-posts.json`, `index.html` 또는 다른 공개 파일에 토큰을
입력하지 마세요. 액세스 토큰은 GitHub Actions의 Secret으로만 관리합니다.

## 3. 최초 실행

1. https://github.com/zipperbagfactory/zipperbag-site/actions/workflows/sync-instagram.yml
2. **Run workflow** → **Run workflow** 실행
3. 성공 시 `instagram-posts.json`의 `posts` 목록에 실제 샘플 사진 데이터가 들어옵니다.
4. GitHub Pages 배포가 끝나면 홈페이지 메인에 사진이 표시됩니다.

## 4. 유지관리

인스타그램 장기 액세스 토큰은 일반적으로 약 **60일** 동안 유효합니다.
토큰이 만료되거나 권한이 철회되면 사진 자동 갱신이 중단됩니다.
이 설정은 토큰을 GitHub 저장소에 노출시키지 않기 위해 토큰 **자동 갱신/저장 기능은 포함하지 않습니다**.
만료 전에 Meta에서 토큰을 다시 발급하거나 갱신하여
GitHub Actions Secret `INSTAGRAM_ACCESS_TOKEN` 값을 교체해 주세요.

새 게시물은 동기화 실행 및 GitHub Pages 배포가 끝난 후 표시되므로 즉시 반영되지는 않습니다.
API가 오류를 반환하면 기존에 저장된 사진 목록은 유지됩니다.
