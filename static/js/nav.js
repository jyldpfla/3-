function toggleNotification() {
    const box = document.getElementById("notification-box");
    if (box) {
        box.classList.toggle("hidden");
    }
}
function toggleNotification() {
    const box = document.getElementById("notification-box");
    if (box) {
        box.classList.toggle("hidden");
    }
}

document.addEventListener('mousedown', function (event) {
    const box = document.getElementById("notification-box");
    const icon = document.querySelector('.notification-icon');
    if (!box || box.classList.contains('hidden')) return;
    if (!box.contains(event.target) && !icon.contains(event.target)) {
        box.classList.add('hidden');
    }
});
function toggleNotification() {
    const box = document.getElementById("notification-box");
    if (box) {
        box.classList.toggle("hidden");
        // 알림창이 열릴 때만 읽음 처리
        if (!box.classList.contains("hidden")) {
            fetch("/notifications/read", { method: "POST" })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        // 빨간 점(red-dot) 숨기기
                        document.querySelectorAll('.red-dot').forEach(dot => dot.style.display = 'none');
                    }
                });
        }
    }
}

document.addEventListener('mousedown', function (event) {
    const box = document.getElementById("notification-box");
    const icon = document.querySelector('.notification-icon');
    if (!box || box.classList.contains('hidden')) return;
    if (!box.contains(event.target) && !icon.contains(event.target)) {
        box.classList.add('hidden');
    }
});