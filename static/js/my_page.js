// 달력 날짜 오늘로 고정
window.addEventListener('DOMContentLoaded', () => {
    const today = new Date();
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    const dd = String(today.getDate()).padStart(2, '0');
    const formatted = `${yyyy}-${mm}-${dd}`;
    document.getElementById('task-date').value = formatted;
});

// 프로젝트 상세보기 탭 메뉴 접기, 펼치기
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.project-tab-content');

tabButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
        // 버튼 스타일
        tabButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // 콘텐츠 전환
        const target = btn.getAttribute('data-tab');
        tabContents.forEach(c => {
            c.classList.toggle('active', c.id === target);
        });
    });
});

document.querySelectorAll('.project-name').forEach(projectName => {
    projectName.addEventListener('click', () => {
        const container = projectName.closest('.project-container');
        const body = container.querySelector('.project-body');

        // 토글 표시
        const isVisible = body.style.display === 'block';
        body.style.display = isVisible ? 'none' : 'block';

        // 스타일 토글 (선택)
        projectName.classList.toggle('active', !isVisible);
    });
});

document.querySelector('.btn-edit').addEventListener('click', () => {
    // 체크된 라디오 버튼 찾기
    const checkedRadio = document.querySelector('input[name="taskSelect"]:checked');
    if (!checkedRadio) {
        document.querySelector('.alert-box.warning').style.display = 'block';
        return;
    }

    // 라디오 버튼이 포함된 tr 찾기
    const row = checkedRadio.closest('tr');
    if (document.querySelector('.btn-edit').textContent == '편집') {
        // 내용 바꾸기
        const contentCell = row.querySelector('.todo_content');
        contentCell.innerHTML = `<input type="text" class="todo_content" value="${contentCell.textContent}" />`;
        // 상태 영역 바꾸기
        const statusCell = row.querySelector('.status');
        const currentStatus = statusCell.textContent.trim();
        statusCell.innerHTML = `
            <select class="status-select">
            <option value="Done" ${currentStatus === 'Done' ? 'selected' : ''}>Done</option>
            <option value="In Progress" ${currentStatus === 'In Progress' ? 'selected' : ''}>In Progress</option>
            <option value="To do" ${currentStatus === 'To do' ? 'selected' : ''}>To do</option>
            </select>
        `;

        // 날짜 영역 바꾸기
        const dateCell = row.querySelector('.task-date');
        const today = new Date().toISOString().split('T')[0];
        dateCell.innerHTML = `<input type="date" class="date-picker" value="${today}" />`;

        // 버튼 텍스트 변경
        document.querySelector('.btn-edit').textContent = '저장';
        document.querySelector('.btn-del').textContent = "취소";
        document.getElementById('btn-add').style.display = "none"
    } else if (document.querySelector('.btn-edit').textContent == '저장') {
        content = row.querySelector('.todo_content input').value;
        status = row.querySelector('.status-select').value;
        date = row.querySelector('.date-picker').value;

        fetch('/mypage/update_task', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                _id: row.querySelector('td[name="task_id"]').getAttribute('value'),
                content: content,
                status: status,
                date: date
            })
        })
            .then(response => {
                if (response.ok) {
                    console.log('수정 성공');
                    location.reload()
                } else {
                    console.warn('서버 응답 오류:', response.status);
                }
            })
            .catch(error => {
                console.error('에러 발생:', error);
            });
    }
});

document.querySelector('.btn-del').addEventListener('click', () => {
    if (document.querySelector('.btn-del').textContent == '삭제') {
        // 체크된 라디오 버튼 찾기
        const checkedRadio = document.querySelector('input[name="taskSelect"]:checked');
        if (!checkedRadio) {
            document.querySelector('.alert-box.warning').style.display = 'block';
            return;
        }

        console.log(checkedRadio)
        // 라디오 버튼이 포함된 tr 찾기
        const row = checkedRadio.closest('tr');
        console.log(row.querySelector('td[name="task_id"]').getAttribute('value'));


        fetch('/mypage/del_task', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                _id: row.querySelector('td[name="task_id"]').getAttribute('value')
            })
        })
            .then(response => {
                if (response.ok) {
                    console.log('삭제 성공');
                    location.reload()
                } else {
                    console.warn('서버 응답 오류:', response.status);
                }
            })
            .catch(error => {
                console.error('에러 발생:', error);
            });
    } else if (document.querySelector('.btn-del').textContent == '취소') {
        // 버튼 텍스트 변경 (선택)
        location.reload();
    }
});

// 취소/확인 버튼 누르면 alert-box 닫기
document.querySelector('.alert-box .cancel').addEventListener('click', () => {
    document.querySelector('.alert-box.warning').style.display = 'none';
});

document.querySelector('.alert-box .confirm').addEventListener('click', () => {
    document.querySelector('.alert-box.warning').style.display = 'none';
});


