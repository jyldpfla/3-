window.addEventListener("click", function (e) {
    const wrapper = document.querySelector(".notification-wrapper");
    const box = document.getElementById("notification-box");
    if (!wrapper.contains(e.target)) {
        box.classList.add("hidden");
    }
});

function toggleNotification() {
    const box = document.getElementById("notification-box");
    box.classList.toggle("hidden");

    // 알림창이 열릴 때만 서버에 읽음 처리 요청
    if (!box.classList.contains("hidden")) {
        fetch("/notifications/read", {
            method: "POST"
        }).then(res => {
            if (res.ok) {
                const dot = document.querySelector(".red-dot");
                if (dot) dot.style.display = "none";  // 빨간 점 숨김
            }
        });
    }
}
