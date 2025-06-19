window.addEventListener('DOMContentLoaded', () => {
    const today = new Date();
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    const dd = String(today.getDate()).padStart(2, '0');
    const formatted = `${yyyy}-${mm}-${dd}`;
    document.getElementById('task-date').value = formatted;
});

document.querySelectorAll('.tab-header .tab').forEach(tab => {
    tab.addEventListener('click', () => {
        // 탭 활성화 스타일 전환
        document.querySelectorAll('.tab-header .tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        // 콘텐츠 표시 전환
        const selectedTab = tab.getAttribute('data-tab');
        document.querySelectorAll('.tab-content').forEach(content => {
            content.style.display = content.id === selectedTab ? 'block' : 'none';
        });
    });
});

