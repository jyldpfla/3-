function addFaq() {
    const title = document.getElementById('new-question').value;
    const content = document.getElementById('new-answer').value;
    const category = prompt('카테고리를 입력하세요');
    const user_id = document.getElementById('user_id').value; // 여기서 읽어옴

    fetch('/faq/insert_action', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: `title=${encodeURIComponent(title)}&category=${encodeURIComponent(category)}&content=${encodeURIComponent(content)}&user_id=${user_id}`
    }).then(res => {
        if (res.redirected) {
            window.location.href = res.url;
        }
    });
}

function showEditForm(id, title, category, content) {
    document.querySelectorAll('.edit-form').forEach(f => f.style.display = 'none');
    const form = document.getElementById('edit-form-' + id);
    if (form) {
        form.style.display = 'block';
        form.title.value = title;
        form.category.value = category;
        form.content.value = content;
    }
}
function hideEditForm(id) {
    const form = document.getElementById('edit-form-' + id);
    if (form) form.style.display = 'none';
}