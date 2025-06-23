document.addEventListener('DOMContentLoaded', function() {
    // DOM 요소 참조
    const scheduleDataContainer = document.getElementById('selected-schedule-data');
    const addScheduleButton = document.getElementById('addScheduleBtn');
    const scheduleFormModal = document.getElementById('scheduleFormModal');
    const saveScheduleBtn = document.getElementById('saveScheduleBtn');
    const cancelScheduleBtn = document.getElementById('cancelScheduleBtn');
    const editScheduleBtn = document.getElementById('editScheduleBtn');
    const deleteScheduleBtn = document.getElementById('deleteScheduleBtn');
    const deleteConfirmModal = document.getElementById('deleteConfirmModal');
    const deleteConfirmYesBtn = document.getElementById('deleteConfirmYesBtn');
    const deleteConfirmNoBtn = document.getElementById('deleteConfirmNoBtn');

    // 폼 내부 입력 필드
    const scheduleNameInput = document.getElementById('scheduleName');
    const schedulePersonNameInput = document.getElementById('schedulePersonName'); // 이름 입력 필드 추가
    const scheduleStartDateInput = document.getElementById('scheduleStartDate');
    const scheduleEndDateInput = document.getElementById('scheduleEndDate');
    const scheduleContentInput = document.getElementById('scheduleContent');
    const scheduleTypeSelect = document.getElementById('scheduleType');
    const scheduleStatusSelect = document.getElementById('scheduleStatus');
    const projectSelectionArea = document.getElementById('projectSelectionArea');
    const scheduleProjectTitleSelect = document.getElementById('scheduleProjectTitle');

    // 우측 패널 동적 업데이트를 위한 요소들
    const dailyScheduleHeader = document.getElementById('dailyScheduleHeader');
    const dailyScheduleList = document.getElementById('dailyScheduleList');
    const scheduleDetailCardContainer = document.getElementById('scheduleDetailCard');

    // 캘린더 네비게이션 버튼 및 현재 월 표시 요소
    const prevMonthBtn = document.querySelector('.prev-month');
    const nextMonthBtn = document.querySelector('.next-month');
    const currentMonthSpan = document.querySelector('.current-month');

    let currentSelectedScheduleIdParam = '';

    // 모달 열기 함수 (스크롤 방지 추가)
    function openModal() {
        if (scheduleFormModal) {
            scheduleFormModal.style.display = 'flex';
            document.body.classList.add('modal-open'); // body 스크롤 방지 클래스 추가
        }
    }

    // 모달 닫기 함수 (스크롤 방지 제거)
    function closeModal() {
        if (scheduleFormModal) {
            scheduleFormModal.style.display = 'none';
            document.body.classList.remove('modal-open'); // body 스크롤 방지 클래스 제거
            resetForm(); // 폼 초기화
        }
    }

    // 폼 초기화 함수
    function resetForm() {
        if (scheduleNameInput) scheduleNameInput.value = '';
        if (schedulePersonNameInput) schedulePersonNameInput.value = ''; // 이름 필드 초기화
        if (scheduleStartDateInput) scheduleStartDateInput.value = '';
        if (scheduleEndDateInput) scheduleEndDateInput.value = '';
        if (scheduleContentInput) scheduleContentInput.value = '';
        if (scheduleTypeSelect) scheduleTypeSelect.value = '';
        if (scheduleStatusSelect) scheduleStatusSelect.innerHTML = ''; // 상태 옵션 비우기

        if (projectSelectionArea) projectSelectionArea.style.display = 'none';
        if (scheduleProjectTitleSelect) scheduleProjectTitleSelect.value = '';

        if (saveScheduleBtn) {
            saveScheduleBtn.textContent = '일정 추가';
        }
        populateStatusOptions(); // 기본 상태 옵션 (아무것도 선택 안된 상태) 채움
    }

    // 상태 옵션을 동적으로 채우는 함수
    function populateStatusOptions(selectedType = '', currentStatus = '') {
        const options = STATUS_OPTIONS_BY_TYPE[selectedType] || [];
        scheduleStatusSelect.innerHTML = ''; // 기존 옵션 모두 제거

        if (options.length === 0 && selectedType !== '') {
            // 선택된 타입에 대한 옵션이 없을 경우, "상태 선택" 같은 메시지
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = '상태 선택';
            scheduleStatusSelect.appendChild(defaultOption);
        } else {
            options.forEach(status => {
                const option = document.createElement('option');
                option.value = status.value;
                option.textContent = status.text;
                if (status.value === currentStatus) {
                    option.selected = true;
                }
                scheduleStatusSelect.appendChild(option);
            });
        }

        // 아무 타입도 선택되지 않았을 때의 초기 옵션
        if (selectedType === '') {
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = '일정 타입을 먼저 선택하세요.';
            scheduleStatusSelect.appendChild(defaultOption);
        }
    }

    // 폼 데이터 수집 함수
    function collectFormData() {
        const scheduleName = scheduleNameInput ? scheduleNameInput.value.trim() : '';
        const personName = schedulePersonNameInput ? schedulePersonNameInput.value.trim() : ''; // 이름 필드 값
        const startDate = scheduleStartDateInput ? scheduleStartDateInput.value : '';
        const endDate = scheduleEndDateInput ? scheduleEndDateInput.value : '';
        const content = scheduleContentInput ? scheduleContentInput.value.trim() : '';
        const type = scheduleTypeSelect ? scheduleTypeSelect.value : '';
        const status = scheduleStatusSelect ? scheduleStatusSelect.value : '';

        // const writerName = "홍길동 대리"; // 실제 로그인 사용자 정보로 대체 필요 -> 이제 입력 필드에서 가져옴
        const projectTitle = (type === '프로젝트' && scheduleProjectTitleSelect) ? scheduleProjectTitleSelect.value : null;

        const data = {
            schedule_name: scheduleName,
            start_date: startDate,
            end_date: endDate,
            member: "", 
            content: content,
            type: type,
            status: status,
            tasks: [], 
            writer_name: personName, // 입력 필드에서 가져온 이름 사용
            project_title: projectTitle
        };
        return data;
    }

    // 캘린더 날짜 클릭 시 일정 로드
    function updateDailySchedules(date) {
        const formattedDate = date; 
        
        const dateParts = formattedDate.split('-');
        // "이날의 일정 (YYYY.MM.DD)" 형식으로 변경
        dailyScheduleHeader.textContent = `이날의 일정 (${dateParts[0]}.${dateParts[1]}.${dateParts[2]})`;

        fetch(`/api/schedules_by_date?date=${formattedDate}`)
            .then(response => response.json())
            .then(schedules => {
                dailyScheduleList.innerHTML = '';
                if (schedules.length === 0) {
                    dailyScheduleList.innerHTML = '<li class="no-schedule-message">일정 없음</li>';
                } else {
                    schedules.forEach(schedule => {
                        const listItem = document.createElement('li');
                        listItem.classList.add('daily-schedule-item', schedule.tag_class);
                        listItem.dataset.scheduleId = schedule.schedule_id_param;
                        listItem.textContent = schedule.name;
                        dailyScheduleList.appendChild(listItem);

                        listItem.addEventListener('click', function() {
                            const scheduleId = this.dataset.scheduleId;
                            // 현재 URL에서 year, month 파라미터 유지
                            const currentYear = urlParams.get('year') || new Date().getFullYear();
                            const currentMonth = urlParams.get('month') || (new Date().getMonth() + 1);
                            window.location.href = `/timeline?year=${currentYear}&month=${currentMonth}&date=${formattedDate}&schedule_id=${encodeURIComponent(scheduleId)}`;
                        });
                    });
                }
            })
            .catch(error => {
                console.error('Error fetching daily schedules:', error);
                dailyScheduleList.innerHTML = '<li class="no-schedule-message">일정을 불러오는 데 실패했습니다.</li>';
            });
    }

    // 캘린더 날짜 클릭 이벤트 리스너 추가
    document.querySelectorAll('.calendar-day').forEach(dayElement => {
        dayElement.addEventListener('click', function() {
            document.querySelectorAll('.calendar-day').forEach(d => d.classList.remove('selected-day'));
            this.classList.add('selected-day');

            const selectedDate = this.dataset.date;
            updateDailySchedules(selectedDate);

            scheduleDetailCardContainer.innerHTML = '<p class="no-schedule-selected">일정을 선택해주세요.</p>';
            currentSelectedScheduleIdParam = '';
        });
    });

    // 초기 로드 시 URL 파라미터에 따라 현재 선택된 날짜와 일정을 하이라이트
    const urlParams = new URLSearchParams(window.location.search);
    const initialSelectedDate = urlParams.get('date');
    
    if (initialSelectedDate) {
        document.querySelectorAll('.calendar-day').forEach(dayElement => {
            if (dayElement.dataset.date === initialSelectedDate) {
                dayElement.classList.add('selected-day');
            } else {
                dayElement.classList.remove('selected-day');
            }
        });
        updateDailySchedules(initialSelectedDate);
    }

    // "일정 추가" 버튼 클릭 시 모달 열기
    if (addScheduleButton) {
        addScheduleButton.addEventListener('click', function() {
            resetForm();
            openModal();
            if (saveScheduleBtn) saveScheduleBtn.textContent = '일정 추가';
        });
    }

    // 모달 내 "취소" 버튼 클릭 시 모달 닫기
    if (cancelScheduleBtn) {
        cancelScheduleBtn.addEventListener('click', function() {
            closeModal();
        });
    }

    // "일정 수정" 버튼 클릭 시 모달 열고 데이터 채우기
    if (editScheduleBtn) {
        editScheduleBtn.addEventListener('click', function() {
            const detail = scheduleDataContainer.dataset;

            if (!detail.scheduleId || detail.scheduleId === 'undefined' || detail.scheduleId === 'None') {
                alert('수정할 일정을 선택해주세요.');
                return;
            }

            resetForm(); // 폼 초기화

            if (scheduleNameInput) scheduleNameInput.value = detail.scheduleName || '';
            if (schedulePersonNameInput) schedulePersonNameInput.value = detail.personName || ''; // 이름 필드 채우기
            if (scheduleStartDateInput) scheduleStartDateInput.value = detail.startDate || '';
            if (scheduleEndDateInput) scheduleEndDateInput.value = detail.endDate || '';
            
            if (scheduleContentInput) scheduleContentInput.value = detail.content && detail.content !== 'None' ? detail.content : '';
            
            if (scheduleTypeSelect) {
                scheduleTypeSelect.value = detail.type || '';
                populateStatusOptions(detail.type, detail.status);
                
                if (detail.type === '프로젝트' && projectSelectionArea) {
                    projectSelectionArea.style.display = 'block';
                    if (scheduleProjectTitleSelect) scheduleProjectTitleSelect.value = detail.projectTitle || '';
                }
            }

            currentSelectedScheduleIdParam = detail.scheduleId || '';
            if (saveScheduleBtn) saveScheduleBtn.textContent = '일정 수정';
            openModal();
        });
    }

    // 모달 내 "저장" 버튼 클릭 시
    if (saveScheduleBtn) {
        saveScheduleBtn.addEventListener('click', async function() {
            const scheduleData = collectFormData();

            if (!scheduleData.schedule_name) {
                alert("일정 이름을 입력해주세요.");
                return;
            }
            if (!scheduleData.writer_name) { // 이름 필드 유효성 검사 추가
                alert("이름을 입력해주세요.");
                return;
            }
            if (!scheduleData.start_date || !scheduleData.end_date) {
                alert("시작일과 종료일을 입력해주세요.");
                return;
            }
            if (!scheduleData.type) {
                alert("일정 타입을 선택해주세요.");
                return;
            }
            if (scheduleData.type === '프로젝트' && !scheduleData.project_title) {
                alert("프로젝트 일정을 선택했을 경우 프로젝트 제목을 선택해주세요.");
                return;
            }
            if (!scheduleData.status) {
                alert("상태를 선택해주세요.");
                return;
            }

            let url = '';
            if (saveScheduleBtn.textContent === '일정 추가') {
                url = '/timeline/create_schedule';
            } else {
                url = '/timeline/update_schedule';
                scheduleData.original_schedule_id_param = currentSelectedScheduleIdParam;
            }

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(scheduleData)
                });
                const result = await response.json();
                if (result.success) {
                    alert(result.message);
                    closeModal();
                    // 현재 캘린더의 연도와 월, 선택된 날짜 파라미터를 유지하면서 새로고침
                    const currentYear = urlParams.get('year') || new Date().getFullYear();
                    const currentMonth = urlParams.get('month') || (new Date().getMonth() + 1);
                    const currentSelectedDate = document.querySelector('.calendar-day.selected-day')?.dataset.date || new Date().toISOString().slice(0,10);
                    
                    if (saveScheduleBtn.textContent === '일정 추가' && result.new_schedule_id) {
                         window.location.href = `/timeline?year=${currentYear}&month=${currentMonth}&date=${currentSelectedDate}&schedule_id=${encodeURIComponent(result.new_schedule_id)}`;
                    } else {
                        window.location.href = `/timeline?year=${currentYear}&month=${currentMonth}&date=${currentSelectedDate}`;
                    }
                } else {
                    alert('작업 실패: ' + result.message);
                }
            } catch (error) {
                console.error('요청 실패:', error);
                alert('요청 처리 중 오류가 발생했습니다.');
            }
        });
    }

    // "일정 삭제" 버튼 클릭 시 삭제 확인 모달 띄우기
    if (deleteScheduleBtn) {
        deleteScheduleBtn.addEventListener('click', function() {
            const detail = scheduleDataContainer.dataset;
            currentSelectedScheduleIdParam = detail.scheduleId || '';

            if (!currentSelectedScheduleIdParam || currentSelectedScheduleIdParam === 'undefined' || currentSelectedScheduleIdParam === 'None') {
                alert('삭제할 일정을 선택해주세요.');
                return;
            }

            if (deleteConfirmModal) {
                deleteConfirmModal.style.display = 'flex';
            }
        });
    }

    // 삭제 확인 모달의 "예" 버튼 클릭 시
    if (deleteConfirmYesBtn) {
        deleteConfirmYesBtn.addEventListener('click', async function() {
            if (currentSelectedScheduleIdParam) {
                try {
                    const response = await fetch('/timeline/delete_schedule', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ schedule_id_param: currentSelectedScheduleIdParam })
                    });
                    const result = await response.json();
                    if (result.success) {
                        alert(result.message);
                        if (deleteConfirmModal) deleteConfirmModal.style.display = 'none';
                        // 현재 캘린더의 연도와 월, 선택된 날짜 파라미터를 유지하면서 새로고침
                        const currentYear = urlParams.get('year') || new Date().getFullYear();
                        const currentMonth = urlParams.get('month') || (new Date().getMonth() + 1);
                        const currentSelectedDate = document.querySelector('.calendar-day.selected-day')?.dataset.date || new Date().toISOString().slice(0,10);
                        window.location.href = `/timeline?year=${currentYear}&month=${currentMonth}&date=${currentSelectedDate}`;
                    } else {
                        alert('삭제 실패: ' + result.message);
                    }
                } catch (error) {
                    console.error('삭제 요청 실패:', error);
                    alert('삭제 처리 중 오류가 발생했습니다.');
                }
            } else {
                if (deleteConfirmModal) deleteConfirmModal.style.display = 'none';
            }
        });
    }

    // 삭제 확인 모달의 "아니오" 버튼 클릭 시
    if (deleteConfirmNoBtn) {
        deleteConfirmNoBtn.addEventListener('click', function() {
            if (deleteConfirmModal) {
                deleteConfirmModal.style.display = 'none';
            }
        });
    }

    // 일정 타입 변경 시 프로젝트 선택 드롭다운 표시/숨김 및 상태 옵션 업데이트
    if (scheduleTypeSelect) {
        scheduleTypeSelect.addEventListener('change', function() {
            const selectedType = this.value;
            if (selectedType === '프로젝트' && projectSelectionArea) {
                projectSelectionArea.style.display = 'block';
            } else if (projectSelectionArea) {
                projectSelectionArea.style.display = 'none';
                if (scheduleProjectTitleSelect) scheduleProjectTitleSelect.value = '';
            }
            populateStatusOptions(selectedType);
        });
    }
    
    // 페이지 로드 시 초기 상태 옵션 채움
    const initialType = scheduleDataContainer.dataset.type || '';
    const initialStatus = scheduleDataContainer.dataset.status || '';
    populateStatusOptions(initialType, initialStatus);

    // 캘린더 이전 달/다음 달 이동 기능 추가
    function navigateMonth(direction) {
        const currentYear = parseInt(currentMonthSpan.dataset.year);
        const currentMonth = parseInt(currentMonthSpan.dataset.month);

        let newYear = currentYear;
        let newMonth = currentMonth + direction;

        if (newMonth > 12) {
            newMonth = 1;
            newYear++;
        } else if (newMonth < 1) {
            newMonth = 12;
            newYear--;
        }
        // 새 월의 1일로 기본 날짜 설정
        const newDate = `${newYear}-${String(newMonth).padStart(2, '0')}-01`;

        // URL 파라미터를 업데이트하여 페이지를 새로고침
        window.location.href = `/timeline?year=${newYear}&month=${newMonth}&date=${newDate}`;
    }

    if (prevMonthBtn) {
        prevMonthBtn.addEventListener('click', function() {
            navigateMonth(-1);
        });
    }

    if (nextMonthBtn) {
        nextMonthBtn.addEventListener('click', function() {
            navigateMonth(1);
        });
    }

});
