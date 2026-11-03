# 대구미술 40인 거장전 · NEXORA ART MUSEUM

독립 홈페이지 소스입니다. 기존 한국미술 30인 저장소와 분리되어 있습니다.

## 구성
- `index.html`: 회전형 3D 갤러리, 4개 전시실, 작가 검색, 상세 소개
- `data/artists.json`: 40인 전시 기획 명단
- `.github/workflows/pages.yml`: GitHub Pages 배포 자동화

## 업로드 및 공개
1. GitHub에서 새 공개 저장소 `myeongdo-daegu-art-40` 생성
2. 이 패키지 파일 전체를 기본 브랜치 `main`에 업로드
3. 저장소 Settings → Pages → Build and deployment → Source: GitHub Actions 지정
4. Actions에서 `Deploy GitHub Pages`가 성공하면 공개 웹사이트 이용 가능

## 중요한 전시 검수 사항
이 파일은 **작가 명단 40인을 반영한 전시 준비본**입니다. 작가별 실제 이미지와 저작권 사용 허락, 평론 원고 및 약력의 출처 검증 이전에는 작품을 임의로 배치하지 않습니다. 기존 30인 전시의 그림을 40인에게 오배정하지 않습니다.