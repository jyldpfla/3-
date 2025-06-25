function confirmStatusChange(btn) {
    var select = btn.closest('form').querySelector('.status-select');
    var current = select.getAttribute('data-current');
    var next = select.value;
    if (current === next) {
        alert('상태가 변경되지 않았습니다.');
        return false;
    }
    return confirm('정말로 이 팀원의 상태를 "' + current + '"에서 "' + next + '"(으)로 변경하시겠습니까?');
}