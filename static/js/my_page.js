window.addEventListener('DOMContentLoaded', () => {
    const today = new Date();
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    const dd = String(today.getDate()).padStart(2, '0');
    const formatted = `${yyyy}-${mm}-${dd}`;
    document.getElementById('task-date').value = formatted;
});

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
    if(document.querySelector('.btn-edit').textContent == '편집') {
        // 체크된 라디오 버튼 찾기
        const checkedRadio = document.querySelector('input[name="taskSelect"]:checked');
        if (!checkedRadio) {
            alert('수정할 항목을 선택하세요.');
            return;
        }

        console.log(checkedRadio)
        // 라디오 버튼이 포함된 tr 찾기
        const row = checkedRadio.closest('tr');
        console.log(row)

        // 상태 영역 바꾸기
        const statusCell = row.querySelector('.status');
        const currentStatus = statusCell.textContent.trim();
        statusCell.innerHTML = `
            <select class="status-select">
            <option value="done" ${currentStatus === 'Done' ? 'selected' : ''}>Done</option>
            <option value="inprogress" ${currentStatus === 'In Progress' ? 'selected' : ''}>In Progress</option>
            <option value="todo" ${currentStatus === 'To do' ? 'selected' : ''}>To do</option>
            </select>
        `;

        // 날짜 영역 바꾸기
        const dateCell = row.querySelector('.task-date');
        const today = new Date().toISOString().split('T')[0];
        dateCell.innerHTML = `<input type="date" class="date-picker" value="${today}" />`;

        // 버튼 텍스트 변경 (선택)
        document.querySelector('.btn-edit').textContent = '저장';
        document.querySelector('.btn-del').textContent = "취소";
    } else if(document.querySelector('.btn-edit').textContent == '저장') {
        
    }
});




