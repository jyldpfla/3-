
document.addEventListener('DOMContentLoaded', function() {
    const editButton = document.querySelector('.edit-btn');
    const deleteButton = document.querySelector('.delete-btn');
    const saveButton = document.querySelector('.save-btn');
    const cancelButton = document.querySelector('.cancel-btn');
    const deleteConfirmation = document.querySelector('.delete-confirmation');
    const scheduleDisplayMode = document.querySelector('.schedule-display-mode');
    const scheduleEditMode = document.querySelector('.schedule-edit-mode');

    editButton.addEventListener('click', function() {
        scheduleDisplayMode.classList.add('hidden');
        scheduleEditMode.classList.remove('hidden');
        editButton.classList.add('hidden');
        deleteButton.classList.add('hidden');
        saveButton.classList.remove('hidden');
        cancelButton.classList.remove('hidden');
    });

    cancelButton.addEventListener('click', function() {
        scheduleDisplayMode.classList.remove('hidden');
        scheduleEditMode.classList.add('hidden');
        editButton.classList.remove('hidden');
        deleteButton.classList.remove('hidden');
        saveButton.classList.add('hidden');
        cancelButton.classList.add('hidden');
    });

    deleteButton.addEventListener('click', function() {
        deleteConfirmation.classList.remove('hidden');
    });

});