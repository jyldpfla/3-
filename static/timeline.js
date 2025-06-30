document.addEventListener('DOMContentLoaded', function() {
    // Get necessary DOM elements
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
    const schedulePersonNameSelect = document.getElementById('schedulePersonName'); // Author field
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

    const selectedMembers = new Set(); // Set to manage participants (stores objects with id and name)
    const memberList = document.getElementById('memberList'); // Participants list UI

    // New participant selection UI container
    const departmentMemberPicker = document.getElementById('departmentMemberPicker');

    // Filter dropdown element
    const scheduleTypeFilter = document.getElementById('scheduleTypeFilter');

    // Logged-in user information (passed from timeline.html via data attributes)
    const scheduleDataElement = document.getElementById('selected-schedule-data');
    const loggedInUserId = scheduleDataElement ? scheduleDataElement.dataset.loggedInUserId : 'None';
    const loggedInUserName = loggedInUserId !== 'None' ? window.user_names.find(user => user._id === loggedInUserId)?.name : '-'; // Get name using ID


    const allUsersFlattened = {}; // Flattened object to quickly find user info by ID
    if (window.user_names) { // Use window.user_names directly
        window.user_names.forEach(user => {
            allUsersFlattened[user._id] = { // Use _id as key
                id: user._id,
                name: user.name,
                position: user.position,
                department: user.department
            };
        });
    } else {
        console.warn("WARN: window.user_names is not defined. User data might not be loading correctly.");
    }

    let currentScheduleId = null; // ID of the currently selected or being modified/deleted schedule
    let isEditMode = false; // Flag for edit mode

    // Function to get URL parameters
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
    let currentTypeFilter = urlParams.type; // Current selected type filter value
    currentScheduleId = urlParams.schedule_id; // Initial schedule ID setting

    // Function to update the selected date title
    function updateSelectedDateTitle() {
        const dateObj = new Date(selectedDate);
        selectedDateTitle.textContent = `${dateObj.getFullYear()}년 ${dateObj.getMonth() + 1}월 ${dateObj.getDate()}일`;
    }

    // Update selected date title on initial load
    updateSelectedDateTitle();

    // Function to open modal
    function openModal(modal) {
        modal.style.display = 'flex'; // Change to flex for vertical and horizontal centering
    }

    // Function to close modal
    function closeModal(modal) {
        modal.style.display = 'none';
    }

    // Function to update participants list UI (memberList)
    function updateMemberListUI() {
        memberList.innerHTML = ''; // Clear existing list
        selectedMembers.forEach(member => {
            const li = document.createElement("li");
            // Display name, position, and department next to participant's name
            li.textContent = `${member.name} (${member.position} - ${member.department})`; 

            const removeBtn = document.createElement("button");
            removeBtn.textContent = "❌";
            removeBtn.style.marginLeft = "10px";
            removeBtn.style.backgroundColor = "transparent";
            removeBtn.style.border = "none";
            removeBtn.style.cursor = "pointer";
            removeBtn.style.color = "#dc3545";
            removeBtn.style.fontSize = "1.1em";

            // Add click event listener to delete button
            // Only allow removal if logged in
            if (window.is_logged_in) {
                removeBtn.addEventListener("click", function () {
                    selectedMembers.delete(member); // Remove from Set
                    li.remove(); // Remove from UI
                    // Deselect the corresponding checkbox in the new UI
                    const checkboxToDeselect = document.getElementById(`member-${member.id}`);
                    if (checkboxToDeselect) {
                        checkboxToDeselect.checked = false;
                    }
                });
            } else {
                removeBtn.disabled = true; // Disable button if not logged in
                removeBtn.style.cursor = 'not-allowed';
                removeBtn.title = '로그인 후 이용 가능합니다.'; // Add tooltip
            }

            li.appendChild(removeBtn);
            memberList.appendChild(li);
        });
    }

    // Render department-specific participant selection UI
    function renderDepartmentMemberPicker() {
        if (!departmentMemberPicker) {
            console.error("ERROR: 'departmentMemberPicker' element not found.");
            return;
        }
        departmentMemberPicker.innerHTML = ''; // Clear existing content

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
            memberListUl.style.display = 'none'; // Hidden by default

            window.grouped_users_by_department[department].forEach(user => {
                const memberLi = document.createElement('li');
                memberLi.classList.add('member-item');
                memberLi.dataset.memberId = user.id;

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.id = `member-${user.id}`;
                checkbox.value = user.id;
                // Set checkbox state based on whether the user is in selectedMembers Set
                checkbox.checked = Array.from(selectedMembers).some(m => m.id === user.id);

                const label = document.createElement('label');
                label.htmlFor = `member-${user.id}`;
                label.textContent = `${user.name} (${user.position})`;

                memberLi.appendChild(checkbox);
                memberLi.appendChild(label);
                memberListUl.appendChild(memberLi);

                // Add change event listener to checkbox
                // Only allow checking/unchecking if logged in
                if (window.is_logged_in) {
                    checkbox.addEventListener('change', function() {
                        const memberId = this.value;
                        const userObj = allUsersFlattened[memberId];

                        if (this.checked) {
                            if (userObj) {
                                // Add to Set if no object with the same ID exists (prevent duplicates)
                                const alreadyExists = Array.from(selectedMembers).some(
                                    m => m.id === userObj.id
                                );
                                if (!alreadyExists) {
                                    selectedMembers.add(userObj);
                                }
                            }
                        } else {
                            // Remove member with matching ID from Set
                            const memberToRemove = Array.from(selectedMembers).find(m => m.id === memberId);
                            if (memberToRemove) {
                                selectedMembers.delete(memberToRemove);
                            }
                        }
                        updateMemberListUI(); // Update selected participants list UI
                    });
                } else {
                    checkbox.disabled = true; // Disable checkbox if not logged in
                    checkbox.style.cursor = 'not-allowed';
                    checkbox.title = '로그인 후 이용 가능합니다.'; // Add tooltip
                }
            });

            deptDiv.appendChild(memberListUl);
            departmentMemberPicker.appendChild(deptDiv);

            // Toggle member list on department header click
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

    // Function to load status options based on schedule type
    function loadStatusOptions(selectedType, currentStatus = null) {
        scheduleStatusSelect.innerHTML = '<option value="">-- 타입 선택 후 선택 --</option>'; // Default option

        if (selectedType && STATUS_OPTIONS_BY_TYPE[selectedType]) {
            STATUS_OPTIONS_BY_TYPE[selectedType].forEach(option => {
                const opt = document.createElement('option');
                opt.value = option.value;
                opt.textContent = option.text;
                scheduleStatusSelect.appendChild(opt);
            });
            scheduleStatusSelect.disabled = false; // Enable if options exist
        } else {
            scheduleStatusSelect.disabled = true; // Disable if no options
        }

        // Select the current status if provided
        if (currentStatus) {
            scheduleStatusSelect.value = currentStatus;
        }
    }

    // Event for schedule type selection change
    scheduleTypeSelect.addEventListener('change', function() {
        // Only allow if logged in
        if (!window.is_logged_in) {
            showCustomMessageBox('로그인된 사용자만 일정을 추가/수정할 수 있습니다.');
            scheduleTypeSelect.value = ''; // Reset selection
            return;
        }
        const selectedType = this.value;
        loadStatusOptions(selectedType); // Load status options

        // Show project selection area if project type is selected
        if (selectedType === '프로젝트') {
            projectSelectionArea.style.display = 'block';
            scheduleProjectTitleSelect.required = true;
        } else {
            projectSelectionArea.style.display = 'none';
            scheduleProjectTitleSelect.required = false;
            scheduleProjectTitleSelect.value = '';
        }
    });

    // Calendar day click event
    calendarGrid.addEventListener('click', function(event) {
        const dayElement = event.target.closest('.calendar-day');
        if (dayElement) {
            const date = dayElement.dataset.date;
            // Navigate to selected date (keep type filter)
            window.location.href = `/timeline?year=${currentYear}&month=${currentMonth}&date=${date}&type=${currentTypeFilter}`;
        }
    });

    // Previous month button click event
    prevMonthBtn.addEventListener('click', function() {
        if (currentMonth === 1) {
            currentMonth = 12;
            currentYear--;
        } else {
            currentMonth--;
        }
        // Navigate to previous month (keep type filter)
        window.location.href = `/timeline?year=${currentYear}&month=${currentMonth}&date=${selectedDate}&type=${currentTypeFilter}`;
    });

    // Next month button click event
    nextMonthBtn.addEventListener('click', function() {
        if (currentMonth === 12) {
            currentMonth = 1;
            currentYear++;
        } else {
            currentMonth++;
        }
        // Navigate to next month (keep type filter)
        window.location.href = `/timeline?year=${currentYear}&month=${currentMonth}&date=${selectedDate}&type=${currentTypeFilter}`;
    });

    // Daily schedule list item click event
    dailyScheduleList.addEventListener('click', function(event) {
        const listItem = event.target.closest('.schedule-item');
        if (listItem) {
            currentScheduleId = listItem.dataset.scheduleId;
            // Navigate with selected schedule ID (keep type filter)
            window.location.href = `/timeline?year=${currentYear}&month=${currentMonth}&date=${selectedDate}&schedule_id=${currentScheduleId}&type=${currentTypeFilter}`;
        }
    });

    // 'Add Schedule' button click event
    if (addScheduleBtn) {
        addScheduleBtn.addEventListener('click', function() {
            if (!window.is_logged_in) { // Double-check login status
                showCustomMessageBox('로그인된 사용자만 일정을 추가할 수 있습니다.');
                return;
            }
            scheduleFormModal.querySelector('.modal-title').textContent = '일정 추가';
            saveScheduleBtn.textContent = '일정 추가';
            isEditMode = false;
            currentScheduleId = null;

            // Clear all input fields
            scheduleNameInput.value = '';
            scheduleContentTextarea.value = '';
            scheduleTypeSelect.value = '';
            scheduleProjectTitleSelect.value = '';
            projectSelectionArea.style.display = 'none';
            scheduleProjectTitleSelect.required = false;

            // Set start/end dates to currently selected date by default
            scheduleStartDateInput.value = selectedDate;
            scheduleEndDateInput.value = selectedDate;
            scheduleStartTimeInput.value = '09:00';
            scheduleEndTimeInput.value = '18:00';

            // Auto-fill author field with logged-in user's ID and disable it
            if (loggedInUserId && loggedInUserId !== 'None') {
                schedulePersonNameSelect.value = loggedInUserId; // Set value to ObjectId string
            } else {
                schedulePersonNameSelect.value = ''; // Clear if no logged-in user
            }
            schedulePersonNameSelect.disabled = true; // Always disable

            loadStatusOptions(''); // Initialize status options
            selectedMembers.clear(); // Clear participants list
            
            renderDepartmentMemberPicker(); // Render new participant selection UI (checkboxes unchecked)
            updateMemberListUI(); // Update participants UI (should be empty)

            openModal(scheduleFormModal); // Open modal
        });
    }

    // 'Edit Schedule' button click event
    if (editScheduleBtn) {
        editScheduleBtn.addEventListener('click', async function() { 
            if (!window.is_logged_in) { // Double-check login status
                showCustomMessageBox('로그인된 사용자만 일정을 수정할 수 있습니다.');
                return;
            }
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

            // Fill form with selected schedule details
            scheduleNameInput.value = scheduleDataElement.dataset.scheduleName;
            scheduleContentTextarea.value = scheduleDataElement.dataset.content;
            scheduleStartDateInput.value = scheduleDataElement.dataset.startDate;
            scheduleStartTimeInput.value = scheduleDataElement.dataset.startTime;
            scheduleEndDateInput.value = scheduleDataElement.dataset.endDate;
            scheduleEndTimeInput.value = scheduleDataElement.dataset.endTime;

            // Set and disable author field (using personId)
            const schedulePersonId = scheduleDataElement.dataset.personId;
            if (schedulePersonId && schedulePersonId !== 'None') {
                schedulePersonNameSelect.value = schedulePersonId; // Set by ID
            } else {
                schedulePersonNameSelect.value = ''; // Clear if author ID is missing or invalid
            }
            schedulePersonNameSelect.disabled = true; // Always disable

            const scheduleType = scheduleDataElement.dataset.type;
            scheduleTypeSelect.value = scheduleType;
            loadStatusOptions(scheduleType, scheduleDataElement.dataset.status);

            // Show project selection area and set value if project type
            if (scheduleType === '프로젝트') {
                projectSelectionArea.style.display = 'block';
                scheduleProjectTitleSelect.value = scheduleDataElement.dataset.projectTitle;
                scheduleProjectTitleSelect.required = true;
            } else {
                projectSelectionArea.style.display = 'none';
                scheduleProjectTitleSelect.value = '';
                scheduleProjectTitleSelect.required = false;
            }

            // Load and display participants list
            selectedMembers.clear(); // Clear existing selected participants

            const memberIdsString = scheduleDataElement.dataset.memberIds; 
            if (memberIdsString) { 
                try {
                    const ids = JSON.parse(memberIdsString); 
                    console.log("DEBUG: Parsed memberIds from dataset (on edit):", ids);
                    if (Array.isArray(ids) && allUsersFlattened) {
                        ids.forEach(memberId => {
                            const userObj = allUsersFlattened[memberId]; // Find user info by ID
                            if (userObj) {
                                selectedMembers.add(userObj); // Add user object to Set
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
            renderDepartmentMemberPicker(); // Render new participant selection UI (reflect initial selection)
            updateMemberListUI(); // Update participants UI

            openModal(scheduleFormModal); // Open modal
        });
    } else {
        console.warn('editScheduleBtn element not found.');
    }

    // 'Add/Edit Schedule' modal save button click event
    saveScheduleBtn.addEventListener('click', function() {
        if (!window.is_logged_in) { // Double-check login status
            showCustomMessageBox('로그인된 사용자만 일정을 추가/수정할 수 있습니다.');
            return;
        }

        const scheduleName = scheduleNameInput.value.trim();
        const scheduleStartDate = scheduleStartDateInput.value;
        const scheduleStartTime = scheduleStartTimeInput.value;
        const scheduleEndDate = scheduleEndDateInput.value;
        const scheduleEndTime = scheduleEndTimeInput.value;
        const scheduleType = scheduleTypeSelect.value;
        const scheduleStatus = scheduleStatusSelect.value;
        const scheduleProjectTitle = scheduleProjectTitleSelect.value;
        const scheduleContent = scheduleContentTextarea.value.trim();

        // Validate required input fields (author field is disabled, so excluded from validation)
        if (!scheduleName || !scheduleStartDate || !scheduleStartTime || !scheduleEndDate || !scheduleEndTime || !scheduleType || !scheduleStatus) {
            showCustomMessageBox('필수 입력 필드를 모두 채워주세요.');
            return;
        }

        if (scheduleType === '프로젝트' && !scheduleProjectTitle) {
            showCustomMessageBox('프로젝트 일정을 선택한 경우 프로젝트 목록을 선택해주세요.');
            return;
        }

        // If start date is later than end date
        if (new Date(scheduleStartDate) > new Date(scheduleEndDate)) {
            showCustomMessageBox('시작 날짜는 종료 날짜보다 빠르거나 같아야 합니다.');
            return;
        }

        // If start and end dates are the same, compare times
        if (scheduleStartDate === scheduleEndDate && scheduleStartTime > scheduleEndTime) {
            showCustomMessageBox('시작 시간은 종료 시간보다 빠르거나 같아야 합니다.');
            return;
        }

        // Extract participant IDs and convert to JSON string (list of ID strings, not object array)
        const selectedMemberIdsArray = Array.from(selectedMembers).map(m => m.id);
        const memberIdsJsonString = JSON.stringify(selectedMemberIdsArray); 
        
        console.log("DEBUG (JS): selectedMembers Set contents:", Array.from(selectedMembers));
        console.log("DEBUG (JS): Extracted selectedMemberIdsArray:", selectedMemberIdsArray);
        console.log("DEBUG (JS): Sending member_ids JSON string to backend:", memberIdsJsonString);

        const data = {
            schedule_name: scheduleName,
            member_ids: memberIdsJsonString, // Change: send participant ID array as JSON string
            // The author is determined by the backend using the session user_id, so there's no need to send schedule_person_name from frontend.
            // Therefore, this field is removed.
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
            data.original_schedule_id_param = currentScheduleId; // Required for update
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
                // Parse server error message
                return response.json().then(errorData => { // Attempt to parse as JSON
                    throw new Error('Server error: ' + (errorData.message || response.statusText));
                }).catch(() => { // If JSON parsing fails, use plain text
                    return response.text().then(text => {
                        throw new Error('Server error: ' + text);
                    });
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showCustomMessageBox(data.message);
                closeModal(scheduleFormModal);
                // Refresh page on success (keep selected date and schedule ID, keep type filter)
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

    // 'Add/Edit Schedule' modal cancel button click event
    if (cancelScheduleBtn) {
        cancelScheduleBtn.addEventListener('click', function() {
            closeModal(scheduleFormModal);
        });
    } else {
        console.warn('cancelScheduleBtn element not found.');
    }

    // 'Delete Schedule' button click event
    if (deleteScheduleBtn) {
        deleteScheduleBtn.addEventListener('click', function() {
            if (!window.is_logged_in) { // Double-check login status
                showCustomMessageBox('로그인된 사용자만 일정을 삭제할 수 있습니다.');
                return;
            }
            const scheduleDataElement = document.getElementById('selected-schedule-data');
            const detailScheduleId = scheduleDataElement.dataset.scheduleId;

            if (detailScheduleId === 'None' || !detailScheduleId) {
                showCustomMessageBox('삭제할 일정을 선택해주세요.');
                return;
            }

            currentScheduleId = detailScheduleId;
            openModal(deleteConfirmModal); // Open delete confirmation modal
        });
    } else {
        console.warn('deleteScheduleBtn element not found.');
    }

    // 'Delete Confirmation' modal cancel button click event
    cancelDeleteBtn.addEventListener('click', function() {
        closeModal(deleteConfirmModal);
        currentScheduleId = null; // Reset schedule ID
    });

    // 'Delete Confirmation' modal delete button click event
    confirmDeleteBtn.addEventListener('click', function() {
        if (!window.is_logged_in) { // Double-check login status
            showCustomMessageBox('로그인된 사용자만 일정을 삭제할 수 있습니다.');
            closeModal(deleteConfirmModal);
            return;
        }

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
        .then(response => {
            if (!response.ok) {
                 // Parse server error message
                return response.json().then(errorData => { // Attempt to parse as JSON
                    throw new Error('Server error: ' + (errorData.message || response.statusText));
                }).catch(() => { // If JSON parsing fails, use plain text
                    return response.text().then(text => {
                        throw new Error('Server error: ' + text);
                    });
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showCustomMessageBox(data.message);
                closeModal(deleteConfirmModal);
                currentScheduleId = null; // Reset schedule ID
                // Refresh page on success (keep selected date, type filter)
                window.location.href = `/timeline?year=${currentYear}&month=${currentMonth}&date=${selectedDate}&type=${currentTypeFilter}`;
            } else {
                showCustomMessageBox('오류: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error (delete):', error);
            showCustomMessageBox('서버 통신 중 오류가 발생했습니다. ' + error.message);
        });
    });

    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === scheduleFormModal) {
            closeModal(scheduleFormModal);
        }
        if (event.target === deleteConfirmModal) {
            closeModal(deleteConfirmModal);
        }
    });

    // Custom message box function to replace alert()
    function showCustomMessageBox(message) {
        alert(message); // Retaining existing alert (can be changed to custom modal if requested)
    }

    // Schedule type filter change event listener [New Logic]
    if (scheduleTypeFilter) {
        scheduleTypeFilter.addEventListener('change', function() {
            const selectedType = this.value;
            window.location.href = `/timeline?year=${currentYear}&month=${currentMonth}&date=${selectedDate}&type=${selectedType}`;
        });
    } else {
        console.warn('scheduleTypeFilter element not found.');
    }
});
