document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const taskForm = document.getElementById('task-form');
  const taskIdInput = document.getElementById('task-id');
  const titleInput = document.getElementById('title');
  const dueDateInput = document.getElementById('due-date');
  const prioritySelect = document.getElementById('priority');
  const tagSelect = document.getElementById('tag');
  const formHeading = document.getElementById('form-heading');
  const submitBtn = document.getElementById('submit-btn');
  const cancelEditBtn = document.getElementById('cancel-edit-btn');
  const formError = document.getElementById('form-error');
  const taskList = document.getElementById('task-list');
  const emptyState = document.getElementById('empty-state');

  // Assign unique IDs to hardcoded list items on load
  document.querySelectorAll('.task-item').forEach((item, index) => {
    if (!item.dataset.id) {
      item.dataset.id = `task-${index + 1}`;
    }
  });

  // Helper: Format date string to "Sep 15, 2026, 11:59 PM"
  function formatDueDate(dateTimeStr) {
    if (!dateTimeStr) return '';
    const date = new Date(dateTimeStr);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  }

  // Helper: Check if date is in the past
  function isOverdue(dateTimeStr) {
    if (!dateTimeStr) return false;
    return new Date(dateTimeStr) < new Date();
  }

  // Helper: Prevent XSS attacks
  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // Reset form back to "Add task" default state
  function resetFormState() {
    taskForm.reset();
    taskIdInput.value = '';
    formHeading.textContent = 'Add a task';
    submitBtn.textContent = 'Add task';
    cancelEditBtn.hidden = true;
    formError.hidden = true;
  }

  // Handle clicking "Edit" on existing list items
  taskList.addEventListener('click', (e) => {
    const editBtn = e.target.closest('.icon-btn');
    if (!editBtn || editBtn.classList.contains('delete') || editBtn.textContent.trim() !== 'Edit') {
      return;
    }

    const taskItem = editBtn.closest('.task-item');
    const id = taskItem.dataset.id;
    const title = taskItem.querySelector('.task-title').textContent.trim();

    // Extract priority from class (e.g., priority-High)
    const priorityBadge = taskItem.querySelector('[class*="priority-"]');
    const priority = priorityBadge ? priorityBadge.textContent.trim() : '';

    // Extract tag (skipping priority and overdue badges)
    const tagBadges = Array.from(taskItem.querySelectorAll('.badge')).filter(
      b => !b.className.includes('priority-') && !b.classList.contains('overdue')
    );
    const tag = tagBadges[0] ? tagBadges[0].textContent.trim() : '';

    // Extract ISO datetime from <time> tag attribute
    const timeEl = taskItem.querySelector('time');
    const dueDate = timeEl ? timeEl.getAttribute('datetime') : '';

    // Populate form fields
    taskIdInput.value = id;
    titleInput.value = title;
    dueDateInput.value = dueDate;
    prioritySelect.value = priority;
    tagSelect.value = tag;

    // Switch UI form state to Edit mode
    formHeading.textContent = 'Edit Task';
    submitBtn.textContent = 'Save Task';
    cancelEditBtn.hidden = false;
    formError.hidden = true;
    titleInput.focus();
  });

  // Handle clicking "Cancel" during edit mode
  cancelEditBtn.addEventListener('click', resetFormState);

  // Handle Form Submission (Both Add and Save Edit)
  taskForm.addEventListener('submit', (e) => {
    e.preventDefault();

    const title = titleInput.value.trim();
    const dueDate = dueDateInput.value;
    const priority = prioritySelect.value;
    const tag = tagSelect.value;
    const editingId = taskIdInput.value;

    // Validation: Title, priority, and tag are required
    if (!title || !priority || !tag) {
      formError.textContent = 'Please fill out all required fields (*).';
      formError.hidden = false;
      return;
    }

    formError.hidden = true;

    const formattedDate = formatDueDate(dueDate);
    const overdue = isOverdue(dueDate);

    if (editingId) {
      // EDIT MODE: Update existing task DOM node directly
      const targetItem = document.querySelector(`.task-item[data-id="${editingId}"]`);
      if (targetItem) {
        targetItem.querySelector('.task-title').textContent = title;
        targetItem.querySelector('.task-meta').innerHTML = `
          <span class="badge priority-${priority}">${priority}</span>
          <span class="badge">${tag}</span>
          ${dueDate ? `<time class="task-due-date" datetime="${dueDate}">Due: ${formattedDate}</time>` : ''}
          ${overdue ? `<span class="badge overdue">Overdue</span>` : ''}
        `;
      }
    } else {
      // ADD MODE: Create new task element and prepend to list
      const li = document.createElement('li');
      li.className = 'task-item';
      li.dataset.id = `task-${Date.now()}`;

      li.innerHTML = `
        <input type="checkbox" />
        <div class="task-body">
          <div class="task-title">${escapeHtml(title)}</div>
          <div class="task-meta">
            <span class="badge priority-${priority}">${priority}</span>
            <span class="badge">${tag}</span>
            ${dueDate ? `<time class="task-due-date" datetime="${dueDate}">Due: ${formattedDate}</time>` : ''}
            ${overdue ? `<span class="badge overdue">Overdue</span>` : ''}
          </div>
        </div>
        <div class="task-actions">
          <button class="icon-btn">Edit</button>
          <button class="icon-btn delete">Delete</button>
        </div>
      `;

      taskList.prepend(li);

      if (emptyState) {
        emptyState.hidden = true;
      }
    }

    // Reset form controls to default state
    resetFormState();
  });
});