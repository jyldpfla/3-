function showAlertBox(type, message, confirmText, cancelText, callback) {
    // 기존 alert-box 제거
    document.querySelectorAll('.alert-box.custom').forEach(e => e.remove());

    

    // alert-box 템플릿 생성
    var box = document.createElement('div');
    box.className = `alert-box ${type} custom`;
    box.innerHTML = `
        <div class="alert-message">${message}</div>
        <div class="alert-actions">
            ${cancelText ? `<button class="btn cancel">${cancelText}</button>` : ''}
            <button class="btn confirm">${confirmText || '확인'}</button>
        </div>
    `;
    document.body.appendChild(box);

    setTimeout(function() { // 이벤트 버블링 방지
        document.addEventListener('mousedown', onOutsideClick);
    }, 10);

    function onOutsideClick(e) {
        if (!box.contains(e.target)) {
            box.remove();
            document.removeEventListener('mousedown', onOutsideClick);
            if (callback) callback(false);
        }
    }

    // 버튼 이벤트
    if (cancelText) {
        box.querySelector('.btn.cancel').onclick = function() {
            box.remove();
            if (callback) callback(false);
        };
    }
    box.querySelector('.btn.confirm').onclick = function() {
        box.remove();
        if (callback) callback(true);
    };
}

// 상태 변경 확인
function confirmStatusChange(btn) {
    var select = btn.closest('form').querySelector('.status-select');
    if (!select) return true; // 삭제 폼에는 select가 없음
    var current = select.getAttribute('data-current');
    var next = select.value;
    if (current === next) {
        showAlertBox('info', '상태가 변경되지 않았습니다.', '확인');
        return false;
    }
    // confirm은 비동기 처리
    showAlertBox('warning', `정말로 이 팀원의 상태를 "${current}"에서 "${next}"(으)로 변경하시겠습니까?`, '확인', '취소', function(result) {
        if (result) {
            btn.closest('form').submit();
        }
    });
    return false; // 항상 false로 처리(비동기)
}

document.addEventListener('DOMContentLoaded', function() {
    // 저장 버튼
    document.querySelectorAll('form[action*="teamMemberUpdate"] button[type="submit"].btn-gray').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            confirmStatusChange(btn);
        });
    });
    // 삭제 버튼
    document.querySelectorAll('form[action*="teamMemberDelete"] button[type="submit"].btn-gray').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            showAlertBox('danger', '정말로 삭제하시겠습니까?', '확인', '취소', function(result) {
                if (result) {
                    btn.closest('form').submit();
                }
            });
        });
    });
        var addBtn = document.getElementById('add-member-btn');
    if (addBtn) {
        addBtn.addEventListener('click', function(e) {
            if (addBtn.dataset.notManager) {
                e.preventDefault();
                showAlertBox('danger', '팀원 추가는 프로젝트 관리자만 가능합니다.', '확인');
            } else {
                location.href = addBtn.dataset.addUrl;
            }
        });
    }
});