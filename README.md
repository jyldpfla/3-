### 프로젝트 구조
- 이름이 붙어있는 파일은 예시 파일로, 각자 이름을 붙인 파일을 생성해 사용하면 됩니다.
- example.html도 예시 파일로, 해당 코드 복사 후 html 파일을 생성 후 사용하면 됩니다.
---
```
3팀_프로젝트
├── datas
│   ├── example.py              # 예시데이터 파일, 수정 X
├── assets
│   ├── css
│   │   └── style.css           # 기본 스타일 시트, 각 페이지별 css 파일 만들어서 폴더에 삽입
│   │   └── yerim_style.css     # 스타일 시트, 각자 만들어서 사용
│   ├── images
│   │   └── logo.png            # 프로젝트에 사용하는 이미지 파일들, 다른 파일과 이름 겹치지 않게만 해주세요
│   └── js
│       └── main.js             # 동적 html 생성에 필요한 js 코드
│       └── yerim_mypage.js     # js 코드, 각자 만들어서 사용
├── logic
│   └── example_logic.py        # 예시 데이터 추가를 위한 로직 페이지, 수정 X
│   └── yerim_data_handler.py   # 페이지 내 로직 개별 파일 생성해 삽입
├── template
│   └── index.html              # 메인페이지에 사용될 파일, 수정 X
│   └── example.html            # HTML 템플릿 파일, 해당 내용은 기본 골격이므로 내용 복사해 개별 파일 생성해 사용, 수정 X
├── .gitignore                  # Git에서 제외할 파일 목록, 수정 X
├── app.py                      # 메인 Flask 애플리케이션 - 추후 사용 예정, 수정 X
├── yerim_app.py                # 각자 Flask 애플리케이션 py 파일 생성해 사용
└── README.md                   # 프로젝트 설명 문서, 수정 X
```

### Github 작업 진행
---
- main branch, develop branch는 개별적으로 push하지 말아주세요. (X절대 금지X)
- 처음 시작 시에 develop branch에 있는 코드로 개인 브랜치를 구성합니다.
- 각 브랜치에 upload 시, 커밋 메세지 첫 줄은 아래와 같이 작성 해주세요
```
2025.06.18(수) - 장예림
```
- main branch : 최종 작업물이 업로드 될 브랜치, 테스트가 완료된 코드를 업로드
- develop branch : 각자 작업한 코드를 모아서 개발, 테스트 시에 사용
- membername branch : 각자 작업한 내용이 업로드 되는 브랜치
    -  팀원 각자 이름을 딴 branch를 생성해, 각자의 branch에서만 작업 진행

### icon download
- html 파일에 기본적으로 icon을 사용할 수 있게 설정해두었습니다
- 원하는 아이콘은 해당 링크에서 찾아서 사용하시면 됩니다 https://fontawesome.com/search
- 아이콘 클릭 후 뜨는 코드를 복사해서 원하는 위치에 붙이면 바로 사용 가능합니다.
```
<!-- 아이콘 코드 예시 -->
<i class="fa-solid fa-building"></i>
```