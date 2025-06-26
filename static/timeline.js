document.addEventListener('DOMContentLoaded', function() {
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

    const selectedMembers = new Set();
    const memberList = document.getElementById('memberList');

    const scheduleMembersSelect = document.getElementById("scheduleMembers");
    if (scheduleMembersSelect) {
        scheduleMembersSelect.addEventListener("change", function () {
            const selectedValue = this.value;
            const selectedOption = this.options[this.selectedIndex];
            const selectedName = selectedOption.dataset.name;

            if (selectedValue && selectedName) {
                const memberObj = { id: selectedValue, name: selectedName };

                const alreadyExists = Array.from(selectedMembers).some(
                    m => m.id === memberObj.id
                );
                if (!alreadyExists) {
                    selectedMembers.add(memberObj);
                    updateMemberListUI();
                }
            }
            this.value = "";
        });
    }
    let currentScheduleId = null;
    let isEditMode = false;

    function getUrlParams() {
        const params = new URLSearchParams(window.location.search);
        return {
            year: parseInt(params.get('year')) || new Date().getFullYear(),
            month: parseInt(params.get('month')) || new Date().getMonth() + 1,
            date: params.get('date') || new Date().toISOString().slice(0, 10),
            schedule_id: params.get('schedule_id') || null
        };
    }

    let urlParams = getUrlParams();
    let currentYear = urlParams.year;
    let currentMonth = urlParams.month;
    let selectedDate = urlParams.date;
    currentScheduleId = urlParams.schedule_id;

    function openModal(modal) {
        modal.style.display = 'block';
    }

    function closeModal(modal) {
        modal.style.display = 'none';
    }

    function updateMemberListUI() {
        memberList.innerHTML = '';
        selectedMembers.forEach(member => {
            const li = document.createElement("li");
            li.textContent = member.name;
            const removeBtn = document.createElement("button");
            removeBtn.textContent = "❌";
            removeBtn.style.marginLeft = "10px";
            removeBtn.style.backgroundColor = "transparent";
            removeBtn.style.border = "none";
            removeBtn.style.cursor = "pointer";
            removeBtn.style.color = "#dc3545";
            removeBtn.style.fontSize = "1.1em";

            removeBtn.addEventListener("click", function () {
                selectedMembers.delete(member);
                li.remove();
            });

            li.appendChild(removeBtn);
            memberList.appendChild(li);
        });
    }

    function loadStatusOptions(selectedType, currentStatus = null) {
        scheduleStatusSelect.innerHTML = '<option value="">-- 타입 선택 후 선택 --</option>';

        if (selectedType && STATUS_OPTIONS_BY_TYPE[selectedType]) {
            STATUS_OPTIONS_BY_TYPE[selectedType].forEach(option => {
                const opt = document.createElement('option');
                opt.value = option.value;
                opt.textContent = option.text;
                scheduleStatusSelect.appendChild(opt);
            });
            scheduleStatusSelect.disabled = false;
        } else {
            scheduleStatusSelect.disabled = true;
        }

        if (currentStatus) {
            scheduleStatusSelect.value = currentStatus;
        }
    }

    scheduleTypeSelect.addEventListener('change', function() {
        const selectedType = this.value;
        loadStatusOptions(selectedType);

        if (selectedType === '프로젝트') {
            projectSelectionArea.style.display = 'block';
            scheduleProjectTitleSelect.required = true;
        } else {
            projectSelectionArea.style.display = 'none';
            scheduleProjectTitleSelect.required = false;
            scheduleProjectTitleSelect.value = '';
        }
    });

    calendarGrid.addEventListener('click', function(event) {
        const dayElement = event.target.closest('.calendar-day');
        if (dayElement) {
            const date = dayElement.dataset.date;
            window.location.href = `/timeline?year=${currentYear}&month=${currentMonth}&date=${date}`;
        }
    });

    prevMonthBtn.addEventListener('click', function() {
        if (currentMonth === 1) {
            currentMonth = 12;
            currentYear--;
        } else {
            currentMonth--;
        }
        window.location.href = `/timeline?year=${currentYear}&month=${currentMonth}&date=${selectedDate}`;
    });

    nextMonthBtn.addEventListener('click', function() {
        if (currentMonth === 12) {
            currentMonth = 1;
            currentYear++;
        } else {
            currentMonth++;
        }
        window.location.href = `/timeline?year=${currentYear}&month=${currentMonth}&date=${selectedDate}`;
    });

    dailyScheduleList.addEventListener('click', function(event) {
        const listItem = event.target.closest('.schedule-item');
        if (listItem) {
            currentScheduleId = listItem.dataset.scheduleId;
            window.location.href = `/timeline?year=${currentYear}&month=${currentMonth}&date=${selectedDate}&schedule_id=${currentScheduleId}`;
        }
    });

    addScheduleBtn.addEventListener('click', function() {
        scheduleFormModal.querySelector('.modal-title').textContent = '일정 추가';
        scheduleNameInput.value = '';
        schedulePersonNameSelect.value = ''; 
        scheduleContentTextarea.value = '';
        scheduleTypeSelect.value = '';
        scheduleProjectTitleSelect.value = '';
        projectSelectionArea.style.display = 'none';
        scheduleProjectTitleSelect.required = false;

        scheduleStartDateInput.value = selectedDate;
        scheduleEndDateInput.value = selectedDate;
        scheduleStartTimeInput.value = '09:00';
        scheduleEndTimeInput.value = '18:00';

        loadStatusOptions('');
        saveScheduleBtn.textContent = '일정 추가';
        isEditMode = false;
        currentScheduleId = null;

        selectedMembers.clear();
        updateMemberListUI();

        openModal(scheduleFormModal);
    });
if (editScheduleBtn) {
    editScheduleBtn.addEventListener('click', function() {
        const scheduleDataElement = document.getElementById('selected-schedule-data');
        const detailScheduleId = scheduleDataElement.dataset.scheduleId;

        if (detailScheduleId === 'None' || !detailScheduleId) {
            alert('수정할 일정을 선택해주세요.');
            return;
        }

        currentScheduleId = detailScheduleId;
        isEditMode = true;
        
        scheduleFormModal.querySelector('.modal-title').textContent = '일정 수정';
        saveScheduleBtn.textContent = '일정 수정';

        scheduleNameInput.value = scheduleDataElement.dataset.scheduleName;
        schedulePersonNameSelect.value = scheduleDataElement.dataset.personName;
        scheduleContentTextarea.value = scheduleDataElement.dataset.content;
        scheduleStartDateInput.value = scheduleDataElement.dataset.startDate;
        scheduleStartTimeInput.value = scheduleDataElement.dataset.startTime;
        scheduleEndDateInput.value = scheduleDataElement.dataset.endDate;
        scheduleEndTimeInput.value = scheduleDataElement.dataset.endTime;

        const scheduleType = scheduleDataElement.dataset.type;
        scheduleTypeSelect.value = scheduleType;
        loadStatusOptions(scheduleType, scheduleDataElement.dataset.status);

        if (scheduleType === '프로젝트') {
            projectSelectionArea.style.display = 'block';
            scheduleProjectTitleSelect.value = scheduleDataElement.dataset.projectTitle;
            scheduleProjectTitleSelect.required = true;
        } else {
            projectSelectionArea.style.display = 'none';
            scheduleProjectTitleSelect.value = '';
            scheduleProjectTitleSelect.required = false;
        }

        selectedMembers.clear();
        const memberNamesString = scheduleDataElement.dataset.memberIds;
        if (memberNamesString) { 
            try {
                const ids = JSON.parse(memberNamesString);
                if (Array.isArray(ids) && window.user_names) {
                    ids.forEach(memberId => {
                        const userObj = window.user_names.find(u => 
                            (u._id && u._id['$oid'] === memberId) || u._id === memberId
                        );
                        if (userObj) {
                            const actualId = (userObj._id && userObj._id['$oid']) ? userObj._id['$oid'] : userObj._id;
                            selectedMembers.add({ id: actualId, name: userObj.name });
                        }
                    });
                }
            } catch (e) {
                console.error("Failed to parse memberIds as JSON:", e);
            }
        }

        updateMemberListUI();

        openModal(scheduleFormModal);
    });
} else {
    console.warn('editScheduleBtn 요소를 찾을 수 없습니다.');
}
    saveScheduleBtn.addEventListener('click', function() {
        const scheduleName = scheduleNameInput.value.trim();
        const schedulePersonName = schedulePersonNameSelect.value;
        const scheduleStartDate = scheduleStartDateInput.value;
        const scheduleStartTime = scheduleStartTimeInput.value;
        const scheduleEndDate = scheduleEndDateInput.value;
        const scheduleEndTime = scheduleEndTimeInput.value;
        const scheduleType = scheduleTypeSelect.value;
        const scheduleStatus = scheduleStatusSelect.value;
        const scheduleProjectTitle = scheduleProjectTitleSelect.value;
        const scheduleContent = scheduleContentTextarea.value.trim();

        if (!scheduleName || !schedulePersonName || !scheduleStartDate || !scheduleStartTime || !scheduleEndDate || !scheduleEndTime || !scheduleType || !scheduleStatus) {
            alert('필수 입력 필드를 모두 채워주세요.');
            return;
        }

        if (scheduleType === '프로젝트' && !scheduleProjectTitle) {
            alert('프로젝트 일정을 선택한 경우 프로젝트 목록을 선택해주세요.');
            return;
        }

        const selectedArray = Array.from(selectedMembers).map(m => m.name);
        const jsonString = JSON.stringify(selectedArray);

        const data = {
            schedule_name: scheduleName,
            person_name: schedulePersonName,
            member_names: jsonString,
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
            data.original_schedule_id_param = currentScheduleId;
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
            return response.text().then(text => {
                throw new Error('서버 오류: ' + text);
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert(data.message);
            closeModal(scheduleFormModal);
            const refreshUrl = `/timeline?year=${currentYear}&month=${currentMonth}&date=${selectedDate}` + 
                            (currentScheduleId ? `&schedule_id=${currentScheduleId}` : '');
            window.location.href = refreshUrl;
        } else {
            alert('오류: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('서버 통신 중 오류가 발생했습니다. 서버 상태를 확인해주세요.');
    });

    });

        if (cancelScheduleBtn) {
            cancelScheduleBtn.addEventListener('click', function() {
                closeModal(scheduleFormModal);
            });
        } else {
            console.warn('cancelScheduleBtn 요소를 찾을 수 없습니다.');
        }

        if (deleteScheduleBtn) {
            deleteScheduleBtn.addEventListener('click', function() {
                const scheduleDataElement = document.getElementById('selected-schedule-data');
                const detailScheduleId = scheduleDataElement.dataset.scheduleId;

                if (detailScheduleId === 'None' || !detailScheduleId) {
                    alert('삭제할 일정을 선택해주세요.');
                    return;
                }

                currentScheduleId = detailScheduleId;
                openModal(deleteConfirmModal);
            });
        } else {
            console.warn('deleteScheduleBtn 요소를 찾을 수 없습니다.');
        }

    cancelDeleteBtn.addEventListener('click', function() {
        closeModal(deleteConfirmModal);
        currentScheduleId = null;
    });

    confirmDeleteBtn.addEventListener('click', function() {
        if (!currentScheduleId) {
            alert('삭제할 일정 정보가 없습니다.');
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
                alert(data.message);
                closeModal(deleteConfirmModal);
                currentScheduleId = null;
                window.location.href = `/timeline?year=${currentYear}&month=${currentMonth}&date=${selectedDate}`;
            } else {
                alert('오류: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('서버 통신 중 오류가 발생했습니다.');
        });
    });

    window.addEventListener('click', function(event) {
        if (event.target === scheduleFormModal) {
            closeModal(scheduleFormModal);
        }
        if (event.target === deleteConfirmModal) {
            closeModal(deleteConfirmModal);
        }
    });

    const initialScheduleId = urlParams.schedule_id;
    if (initialScheduleId && initialScheduleId !== 'None') {
    }
});
