document.addEventListener('DOMContentLoaded', function() {
    // 필요한 DOM 요소들 가져오기
    const prevMonthBtn = document.getElementById('prevMonthBtn');
    const nextMonthBtn = document.getElementById('nextMonthBtn');
    const currentMonthYear = document.getElementById('currentMonthYear');
    const calendarGrid = document.querySelector('.calendar-grid');
    const dailyScheduleList = document.getElementById('dailyScheduleList');
    const selectedDateTitle = document.getElementById('selectedDateTitle');
    const addScheduleBtn = document.getElementById('addScheduleBtn');
    const scheduleFormModal = document.getElementById('scheduleFormModal');
    const cancelScheduleBtn = document.getElementById('cancelScheduleBtn');
    const saveScheduleBtn = document.getElementById('saveScheduleBtn');
    
    const scheduleTypeSelect = document.getElementById('scheduleType');
    const projectSelectionArea = document.getElementById('projectSelectionArea');
    const scheduleProjectTitleSelect = document.getElementById('scheduleProjectTitle');
    const scheduleNameInput = document.getElementById('scheduleName');
    const schedulePersonNameSelect = document.getElementById('schedulePersonName');
    const scheduleStartDateInput = document.getElementById('scheduleStartDate');
    const scheduleStartTimeInput = document.getElementById('scheduleStartTime');
    const scheduleEndDateInput = document.getElementById('scheduleEndDate');
    const scheduleEndTimeInput = document.getElementById('scheduleEndTime');
    const scheduleContentTextarea = document.getElementById('scheduleContent');
    const scheduleStatusSelect = document.getElementById('scheduleStatus');

    const scheduleDetailCard = document.getElementById('scheduleDetailCard');
    const editScheduleBtn = document.getElementById('editScheduleBtn');
    const deleteScheduleBtn = document.getElementById('deleteScheduleBtn');
    
    const deleteConfirmModal = document.getElementById('deleteConfirmModal');
    const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');

    const selectedMembers = new Set(); // 참여자 관리를 위한 Set (id와 name 객체 저장)
    const memberList = document.getElementById('memberList'); // 참여자 목록 UI

    // 새로운 참여자 선택 UI 컨테이너
    const departmentMemberPicker = document.getElementById('departmentMemberPicker');

    // 필터링 드롭다운 요소 추가
    const scheduleTypeFilter = document.getElementById('scheduleTypeFilter');

    // 로그인된 사용자 이름 (timeline.html에서 data-logged-in-user-name으로 전달)
    const scheduleDataElement = document.getElementById('selected-schedule-data');
    const loggedInUserName = scheduleDataElement.dataset.loggedInUserName;

    const allUsersFlattened = {}; // ID로 사용자 정보를 빠르게 찾기 위한 평탄화된 객체
    if (window.grouped_users_by_department) {
        for (const dept in window.grouped_users_by_department) {
            window.grouped_users_by_department[dept].forEach(user => {
                allUsersFlattened[user.id] = {
                    id: user.id,
                    name: user.name,
                    position: user.position,
                    department: dept
                };
            });
        }
    } else {
        console.warn("WARN: window.grouped_users_by_department가 정의되지 않았습니다. 사용자 데이터 로딩에 문제가 있을 수 있습니다.");
    }

    let currentScheduleId = null; // 현재 선택되거나 수정/삭제될 일정의 ID
    let isEditMode = false; // 수정 모드 여부

    // URL 파라미터를 가져오는 함수
    function getUrlParams() {
        const params = new URLSearchParams(window.location.search);
        return {
            year: parseInt(params.get('year')) || new Date().getFullYear(),
            month: parseInt(params.get('month')) || new Date().getMonth() + 1,
            date: params.get('date') || new Date().toISOString().slice(0, 10),
            schedule_id: params.get('schedule_id') || null,
            type: params.get('type') || '전체'
        };
    }

    let urlParams = getUrlParams();
    let currentYear = urlParams.year;
    let currentMonth = urlParams.month;
    let selectedDate = urlParams.date;
    let currentTypeFilter = urlParams.type; // 현재 선택된 타입 필터 값
    currentScheduleId = urlParams.schedule_id; // 초기 일정 ID 설정

    // 선택된 날짜 제목 업데이트 함수
    function updateSelectedDateTitle() {
        const dateObj = new Date(selectedDate);
        selectedDateTitle.textContent = `${dateObj.getFullYear()}년 ${dateObj.getMonth() + 1}월 ${dateObj.getDate()}일`;
    }

    // 초기 로드 시 선택된 날짜 제목 업데이트
    updateSelectedDateTitle();

    // 모달 열기 함수
    function openModal(modal) {
        modal.style.display = 'flex'; // flex로 변경하여 중앙 정렬 유지
    }

    // 모달 닫기 함수
    function closeModal(modal) {
        modal.style.display = 'none';
    }

    // 참여자 목록 UI 업데이트 함수 (memberList)
    function updateMemberListUI() {
        memberList.innerHTML = ''; // 기존 목록 초기화
        selectedMembers.forEach(member => {
            const li = document.createElement("li");
            // 참여자 이름 옆에 직급과 부서 정보를 함께 표시
            li.textContent = `${member.name} (${member.position} - ${member.department})`; 

            const removeBtn = document.createElement("button");
            removeBtn.textContent = "❌";
            removeBtn.style.marginLeft = "10px";
            removeBtn.style.backgroundColor = "transparent";
            removeBtn.style.border = "none";
            removeBtn.style.cursor = "pointer";
            removeBtn.style.color = "#dc3545";
            removeBtn.style.fontSize = "1.1em";

            // 삭제 버튼 클릭 이벤트
            removeBtn.addEventListener("click", function () {
                selectedMembers.delete(member); // Set에서 제거
                li.remove(); // UI에서 제거
                // 새로운 UI (checkbox)에서도 해당 멤버의 체크를 해제
                const checkboxToDeselect = document.getElementById(`member-${member.id}`);
                if (checkboxToDeselect) {
                    checkboxToDeselect.checked = false;
                }
            });

            li.appendChild(removeBtn);
            memberList.appendChild(li);
        });
    }

    // 부서별 참여자 선택 UI 렌더링
    function renderDepartmentMemberPicker() {
        if (!departmentMemberPicker) {
            console.error("ERROR: 'departmentMemberPicker' element not found.");
            return;
        }
        departmentMemberPicker.innerHTML = ''; // 기존 내용 초기화

        if (!window.grouped_users_by_department) {
            console.warn("WARN: window.grouped_users_by_department is not defined for rendering member picker.");
            return;
        }

        for (const department in window.grouped_users_by_department) {
            const deptDiv = document.createElement('div');
            deptDiv.classList.add('department-group');

            const deptHeader = document.createElement('div');
            deptHeader.classList.add('department-header');
            deptHeader.innerHTML = `<h3>${department} <span class="member-count">(${window.grouped_users_by_department[department].length})</span><i class="fa-solid fa-chevron-down toggle-icon"></i></h3>`;
            deptDiv.appendChild(deptHeader);

            const memberListUl = document.createElement('ul');
            memberListUl.classList.add('department-members-list');
            memberListUl.style.display = 'none'; // 초기에는 숨김

            window.grouped_users_by_department[department].forEach(user => {
                const memberLi = document.createElement('li');
                memberLi.classList.add('member-item');
                memberLi.dataset.memberId = user.id;

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.id = `member-${user.id}`;
                checkbox.value = user.id;
                // selectedMembers Set에 해당 사용자 객체가 있는지 확인하여 체크박스 상태 설정
                checkbox.checked = Array.from(selectedMembers).some(m => m.id === user.id);

                const label = document.createElement('label');
                label.htmlFor = `member-${user.id}`;
                label.textContent = `${user.name} (${user.position})`;

                memberLi.appendChild(checkbox);
                memberLi.appendChild(label);
                memberListUl.appendChild(memberLi);

                // 체크박스 변경 이벤트 리스너
                checkbox.addEventListener('change', function() {
                    const memberId = this.value;
                    const userObj = allUsersFlattened[memberId];

                    if (this.checked) {
                        if (userObj) {
                            // Set에 동일한 ID의 객체가 없으면 추가 (중복 방지)
                            const alreadyExists = Array.from(selectedMembers).some(
                                m => m.id === userObj.id
                            );
                            if (!alreadyExists) {
                                selectedMembers.add(userObj);
                            }
                        }
                    } else {
                        // Set에서 해당 ID를 가진 멤버 제거
                        const memberToRemove = Array.from(selectedMembers).find(m => m.id === memberId);
                        if (memberToRemove) {
                            selectedMembers.delete(memberToRemove);
                        }
                    }
                    updateMemberListUI(); // 선택된 참여자 목록 UI 업데이트
                });
            });

            deptDiv.appendChild(memberListUl);
            departmentMemberPicker.appendChild(deptDiv);

            // 부서 헤더 클릭 시 멤버 목록 토글
            deptHeader.addEventListener('click', function() {
                const isHidden = memberListUl.style.display === 'none';
                memberListUl.style.display = isHidden ? 'block' : 'none';
                const icon = deptHeader.querySelector('.toggle-icon');
                if (icon) {
                    icon.classList.toggle('fa-chevron-down', !isHidden);
                    icon.classList.toggle('fa-chevron-up', isHidden);
                }
            });
        }
    }

    // 일정 타입에 따른 상태 옵션 로드 함수
    function loadStatusOptions(selectedType, currentStatus = null) {
        scheduleStatusSelect.innerHTML = '<option value="">-- 타입 선택 후 선택 --</option>'; // 기본 옵션

        if (selectedType && STATUS_OPTIONS_BY_TYPE[selectedType]) {
            STATUS_OPTIONS_BY_TYPE[selectedType].forEach(option => {
                const opt = document.createElement('option');
                opt.value = option.value;
                opt.textContent = option.text;
                scheduleStatusSelect.appendChild(opt);
            });
            scheduleStatusSelect.disabled = false; // 옵션이 있으면 활성화
        } else {
            scheduleStatusSelect.disabled = true; // 옵션이 없으면 비활성화
        }

        // 현재 상태가 있으면 해당 옵션 선택
        if (currentStatus) {
            scheduleStatusSelect.value = currentStatus;
        }
    }

    // 일정 타입 선택 변경 시 이벤트
    scheduleTypeSelect.addEventListener('change', function() {
        const selectedType = this.value;
        loadStatusOptions(selectedType); // 상태 옵션 로드

        // 프로젝트 타입일 경우 프로젝트 선택 영역 표시
        if (selectedType === '프로젝트') {
            projectSelectionArea.style.display = 'block';
            scheduleProjectTitleSelect.required = true;
        } else {
            projectSelectionArea.style.display = 'none';
            scheduleProjectTitleSelect.required = false;
            scheduleProjectTitleSelect.value = '';
        }
    });

    // 캘린더 날짜 클릭 이벤트
    calendarGrid.addEventListener('click', function(event) {
        const dayElement = event.target.closest('.calendar-day');
        if (dayElement) {
            const date = dayElement.dataset.date;
            // 선택된 날짜로 페이지 이동 (일정 ID는 유지하지 않음, 타입 필터는 유지)
            window.location.href = `/timeline?year=${currentYear}&month=${currentMonth}&date=${date}&type=${currentTypeFilter}`;
        }
    });

    // 이전 달 버튼 클릭 이벤트
    prevMonthBtn.addEventListener('click', function() {
        if (currentMonth === 1) {
            currentMonth = 12;
            currentYear--;
        } else {
            currentMonth--;
        }
        // 페이지 이동 시 타입 필터 유지
        window.location.href = `/timeline?year=${currentYear}&month=${currentMonth}&date=${selectedDate}&type=${currentTypeFilter}`;
    });

    // 다음 달 버튼 클릭 이벤트
    nextMonthBtn.addEventListener('click', function() {
        if (currentMonth === 12) {
            currentMonth = 1;
            currentYear++;
        } else {
            currentMonth++;
        }
        // 페이지 이동 시 타입 필터 유지
        window.location.href = `/timeline?year=${currentYear}&month=${currentMonth}&date=${selectedDate}&type=${currentTypeFilter}`;
    });

    // 일일 일정 목록 항목 클릭 이벤트
    dailyScheduleList.addEventListener('click', function(event) {
        const listItem = event.target.closest('.schedule-item');
        if (listItem) {
            currentScheduleId = listItem.dataset.scheduleId;
            // 선택된 일정 ID를 포함하여 페이지 이동 (타입 필터 유지)
            window.location.href = `/timeline?year=${currentYear}&month=${currentMonth}&date=${selectedDate}&schedule_id=${currentScheduleId}&type=${currentTypeFilter}`;
        }
    });

    // '일정 추가' 버튼 클릭 이벤트 (HTML의 onclick="openCreateScheduleModal()" 제거 필요)
    addScheduleBtn.addEventListener('click', function() {
        scheduleFormModal.querySelector('.modal-title').textContent = '일정 추가';
        saveScheduleBtn.textContent = '일정 추가';
        isEditMode = false;
        currentScheduleId = null;

        // 모든 입력 필드 초기화
        scheduleNameInput.value = '';
        scheduleContentTextarea.value = '';
        scheduleTypeSelect.value = '';
        scheduleProjectTitleSelect.value = '';
        projectSelectionArea.style.display = 'none';
        scheduleProjectTitleSelect.required = false;

        // 시작일/종료일은 현재 선택된 날짜로 기본 설정
        scheduleStartDateInput.value = selectedDate;
        scheduleEndDateInput.value = selectedDate;
        scheduleStartTimeInput.value = '09:00';
        scheduleEndTimeInput.value = '18:00';

        // 작성자 필드 자동 반영 및 비활성화
        if (loggedInUserName && loggedInUserName !== '-') {
            schedulePersonNameSelect.value = loggedInUserName;
        } else {
            schedulePersonNameSelect.value = '-'; // 로그인 사용자 없으면 "-"
        }
        schedulePersonNameSelect.disabled = true; // 항상 비활성화

        loadStatusOptions(''); // 상태 옵션 초기화
        selectedMembers.clear(); // 참여자 목록 초기화
        
        renderDepartmentMemberPicker(); // 새로운 참여자 선택 UI 렌더링 (체크박스 초기화 상태)
        updateMemberListUI(); // 참여자 UI 업데이트 (비어있을 것)

        openModal(scheduleFormModal); // 모달 열기
    });

    // '일정 수정' 버튼 클릭 이벤트
    if (editScheduleBtn) {
        editScheduleBtn.addEventListener('click', function() {
            const scheduleDataElement = document.getElementById('selected-schedule-data');
            const detailScheduleId = scheduleDataElement.dataset.scheduleId;

            if (detailScheduleId === 'None' || !detailScheduleId) {
                showCustomMessageBox('수정할 일정을 선택해주세요.');
                return;
            }

            currentScheduleId = detailScheduleId;
            isEditMode = true;
            
            scheduleFormModal.querySelector('.modal-title').textContent = '일정 수정';
            saveScheduleBtn.textContent = '일정 수정';

            // 선택된 일정 상세 정보로 폼 채우기
            scheduleNameInput.value = scheduleDataElement.dataset.scheduleName;
            scheduleContentTextarea.value = scheduleDataElement.dataset.content;
            scheduleStartDateInput.value = scheduleDataElement.dataset.startDate;
            scheduleStartTimeInput.value = scheduleDataElement.dataset.startTime;
            scheduleEndDateInput.value = scheduleDataElement.dataset.endDate;
            scheduleEndTimeInput.value = scheduleDataElement.dataset.endTime;

            // 작성자 필드 설정 및 비활성화
            schedulePersonNameSelect.value = scheduleDataElement.dataset.personName;
            schedulePersonNameSelect.disabled = true;

            const scheduleType = scheduleDataElement.dataset.type;
            scheduleTypeSelect.value = scheduleType;
            loadStatusOptions(scheduleType, scheduleDataElement.dataset.status);

            // 프로젝트 타입인 경우 프로젝트 선택 영역 표시 및 값 설정
            if (scheduleType === '프로젝트') {
                projectSelectionArea.style.display = 'block';
                scheduleProjectTitleSelect.value = scheduleDataElement.dataset.projectTitle;
                scheduleProjectTitleSelect.required = true;
            } else {
                projectSelectionArea.style.display = 'none';
                scheduleProjectTitleSelect.value = '';
                scheduleProjectTitleSelect.required = false;
            }

            // 참여자 목록 로드 및 UI 반영
            selectedMembers.clear(); // 기존 선택된 참여자 목록 초기화

            const memberIdsString = scheduleDataElement.dataset.memberIds; 
            if (memberIdsString) { 
                try {
                    const ids = JSON.parse(memberIdsString); 
                    console.log("DEBUG: Parsed memberIds from dataset (on edit):", ids);
                    if (Array.isArray(ids) && allUsersFlattened) {
                        ids.forEach(memberId => {
                            const userObj = allUsersFlattened[memberId]; // ID로 사용자 정보 찾기
                            if (userObj) {
                                selectedMembers.add(userObj); // Set에 사용자 객체 추가
                                console.log("DEBUG: Added member to selectedMembers (on edit):", userObj.name, userObj.id, userObj.position, userObj.department);
                            } else {
                                console.warn("WARN: User not found in allUsersFlattened for ID (on edit):", memberId);
                            }
                        });
                    } else {
                        console.warn("WARN: memberIds from dataset is not an array or allUsersFlattened is missing (on edit).");
                    }
                } catch (e) {
                    console.error("ERROR: Failed to parse memberIds as JSON (on edit):", e);
                }
            }
            renderDepartmentMemberPicker(); // 새로운 참여자 선택 UI 렌더링 (초기 선택 상태 반영)
            updateMemberListUI(); // 참여자 UI 업데이트

            openModal(scheduleFormModal); // 모달 열기
        });
    } else {
        console.warn('editScheduleBtn 요소를 찾을 수 없습니다.');
    }

    // '일정 추가/수정' 모달 저장 버튼 클릭 이벤트
    saveScheduleBtn.addEventListener('click', function() {
        const scheduleName = scheduleNameInput.value.trim();
        const scheduleStartDate = scheduleStartDateInput.value;
        const scheduleStartTime = scheduleStartTimeInput.value;
        const scheduleEndDate = scheduleEndDateInput.value;
        const scheduleEndTime = scheduleEndTimeInput.value;
        const scheduleType = scheduleTypeSelect.value;
        const scheduleStatus = scheduleStatusSelect.value;
        const scheduleProjectTitle = scheduleProjectTitleSelect.value;
        const scheduleContent = scheduleContentTextarea.value.trim();

        // 필수 입력 필드 유효성 검사 (작성자 필드는 비활성화되어 있으므로 검사에서 제외)
        if (!scheduleName || !scheduleStartDate || !scheduleStartTime || !scheduleEndDate || !scheduleEndTime || !scheduleType || !scheduleStatus) {
            showCustomMessageBox('필수 입력 필드를 모두 채워주세요.');
            return;
        }

        if (scheduleType === '프로젝트' && !scheduleProjectTitle) {
            showCustomMessageBox('프로젝트 일정을 선택한 경우 프로젝트 목록을 선택해주세요.');
            return;
        }

        // 선택된 참여자들의 ID만 추출하여 JSON 문자열로 변환
        const selectedMemberIdsArray = Array.from(selectedMembers).map(m => m.id);
        const memberIdsJsonString = JSON.stringify(selectedMemberIdsArray); // ObjectId 문자열 리스트를 JSON 문자열로
        
        console.log("DEBUG (JS): selectedMembers Set contents:", Array.from(selectedMembers));
        console.log("DEBUG (JS): Extracted selectedMemberIdsArray:", selectedMemberIdsArray);
        console.log("DEBUG (JS): Sending member_ids JSON string to backend:", memberIdsJsonString);

        const data = {
            schedule_name: scheduleName,
            member_ids: memberIdsJsonString, // 변경: 참여자 ID 배열 JSON 문자열 전송
            start_date: `${scheduleStartDate}T${scheduleStartTime}:00`,
            end_date: `${scheduleEndDate}T${scheduleEndTime}:00`,
            content: scheduleContent,
            type: scheduleType,
            status: scheduleStatus,
            project_title: scheduleType === '프로젝트' ? scheduleProjectTitle : null,
        };

        let url = '';
        let method = '';

        if (isEditMode) {
            url = '/timeline/update_schedule';
            method = 'POST';
            data.original_schedule_id_param = currentScheduleId; // 수정 시 필요
        } else {
            url = '/timeline/create_schedule';
            method = 'POST';
        }

        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                // 서버 에러 메시지 파싱
                return response.text().then(text => {
                    throw new Error('서버 오류: ' + text);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showCustomMessageBox(data.message);
                closeModal(scheduleFormModal);
                // 성공 시 페이지 새로고침 (선택된 날짜와 일정 ID 유지, 타입 필터 유지)
                const refreshUrl = `/timeline?year=${currentYear}&month=${currentMonth}&date=${selectedDate}` + 
                                     (currentScheduleId ? `&schedule_id=${currentScheduleId}` : '') +
                                     `&type=${currentTypeFilter}`;
                window.location.href = refreshUrl;
            } else {
                showCustomMessageBox('오류: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error (fetch):', error);
            showCustomMessageBox('서버 통신 중 오류가 발생했습니다. 서버 상태를 확인해주세요.');
        });
    });

    // '일정 추가/수정' 모달 취소 버튼 클릭 이벤트
    if (cancelScheduleBtn) {
        cancelScheduleBtn.addEventListener('click', function() {
            closeModal(scheduleFormModal);
        });
    } else {
        console.warn('cancelScheduleBtn 요소를 찾을 수 없습니다.');
    }

    // '일정 삭제' 버튼 클릭 이벤트
    if (deleteScheduleBtn) {
        deleteScheduleBtn.addEventListener('click', function() {
            const scheduleDataElement = document.getElementById('selected-schedule-data');
            const detailScheduleId = scheduleDataElement.dataset.scheduleId;

            if (detailScheduleId === 'None' || !detailScheduleId) {
                showCustomMessageBox('삭제할 일정을 선택해주세요.');
                return;
            }

            currentScheduleId = detailScheduleId;
            openModal(deleteConfirmModal); // 삭제 확인 모달 열기
        });
    } else {
        console.warn('deleteScheduleBtn 요소를 찾을 수 없습니다.');
    }

    // '삭제 확인' 모달 취소 버튼 클릭 이벤트
    cancelDeleteBtn.addEventListener('click', function() {
        closeModal(deleteConfirmModal);
        currentScheduleId = null; // 일정 ID 초기화
    });

    // '삭제 확인' 모달 삭제 버튼 클릭 이벤트
    confirmDeleteBtn.addEventListener('click', function() {
        if (!currentScheduleId) {
            showCustomMessageBox('삭제할 일정 정보가 없습니다.');
            closeModal(deleteConfirmModal);
            return;
        }

        fetch('/timeline/delete_schedule', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ schedule_id_param: currentScheduleId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showCustomMessageBox(data.message);
                closeModal(deleteConfirmModal);
                currentScheduleId = null; // 일정 ID 초기화
                // 성공 시 페이지 새로고침 (선택된 날짜 유지, 타입 필터 유지)
                window.location.href = `/timeline?year=${currentYear}&month=${currentMonth}&date=${selectedDate}&type=${currentTypeFilter}`;
            } else {
                showCustomMessageBox('오류: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error (delete):', error);
            showCustomMessageBox('서버 통신 중 오류가 발생했습니다.');
        });
    });

    // 모달 외부 클릭 시 닫기 이벤트
    window.addEventListener('click', function(event) {
        if (event.target === scheduleFormModal) {
            closeModal(scheduleFormModal);
        }
        if (event.target === deleteConfirmModal) {
            closeModal(deleteConfirmModal);
        }
    });

    // Alert 대신 사용할 커스텀 메시지 박스 함수
    function showCustomMessageBox(message) {
        alert(message);
    }

    // 일정 타입 필터 변경 이벤트 리스너 추가 [새로운 로직]
    if (scheduleTypeFilter) {
        scheduleTypeFilter.addEventListener('change', function() {
            const selectedType = this.value;
            // 필터 변경 시 페이지를 새로고침하여 새로운 타입 필터를 적용
            window.location.href = `/timeline?year=${currentYear}&month=${currentMonth}&date=${selectedDate}&type=${selectedType}`;
        });
    } else {
        console.warn('scheduleTypeFilter 요소를 찾을 수 없습니다.');
    }
});
