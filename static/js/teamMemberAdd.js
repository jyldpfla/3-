
function updateUserInfo(selectElement) {
const selectedId = selectElement.value;
const user = users.find(u => u._id === selectedId);

const infoBox = selectElement.closest('.member-field').querySelector('.member-info-box');
if (user) {
    infoBox.querySelector('.email').textContent = "이메일: " + user.email;
    infoBox.querySelector('.role').textContent = "역할: " + user.role;
    infoBox.querySelector('.department').textContent = "소속: " + (user.department || "-");
} else {
    infoBox.querySelector('.email').textContent = "이메일: 선택된 팀원이 없습니다.";
    infoBox.querySelector('.role').textContent = "역할: -";
    infoBox.querySelector('.department').textContent = "소속: -";
}
}

function addMemberField() {
const container = document.getElementById("member-fields");

const memberField = document.createElement("div");
memberField.className = "member-field";

memberField.innerHTML = `
    <label for="name">이름</label>
    <select name="_id" class="name-select" onchange="updateUserInfo(this)" required>
    <option value="" disabled selected>팀원을 선택하세요</option>
    ${users.map(user => `<option value="${user._id}">${user.name}</option>`).join('')}
    </select>

    <div class="member-info-box">
    <p class="email">이메일: 선택된 팀원이 없습니다.</p>
    <p class="role">역할: -</p>
    <p class="department">소속: -</p>
    </div>

    <label for="status">상태</label>
    <select name="status" class="status-select" required>
    <option value="참여중">참여중</option>
    <option value="대기">대기</option>
    </select>

    
`;

container.appendChild(memberField);

}
function removeLastMemberField() {
const container = document.querySelector("#member-fields");
const fields = container.querySelectorAll(".member-field");

if (fields.length <= 1) {
    alert("최소 한 명의 팀원은 필요합니다.");
    return;
}

const lastField = fields[fields.length - 1];
lastField.remove();
}
// updateUserInfo: 사용자가 이름을 선택하면 해당 사용자 정보(이메일, 역할, 소속)를 찾아 보여줍니다.

// addMemberField: 새 팀원 입력 필드를 추가합니다.

// removeLastMemberField: 마지막으로 추가된 팀원 입력 필드를 삭제하는데, 최소 1명은 남도록 제한합니다.