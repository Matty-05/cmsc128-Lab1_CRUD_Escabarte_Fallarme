(function () {
  function markOverdueTasks() {
    var now = new Date();

  document.querySelectorAll('.task-item').forEach(function (item) {
    var dueRaw = item.dataset.dueDate;
    var isDone = item.dataset.isDone === '1';
    if (!dueRaw || isDone) return;

    var due = new Date(dueRaw);
    if (isNaN(due.getTime()) || due >= now) return;

    item.classList.add('overdue-task');
    var meta = item.querySelector('.task-meta');
    if (meta && !meta.querySelector('.badge.overdue')) {
      var badge = document.createElement('span');
      badge.className = 'badge overdue';
      badge.textContent = 'Overdue';
      meta.appendChild(badge);
    }
  });
}

  // Confirm a deletion before starting the existing three-second Undo window.
  function initUndoDelete() {
    var confirmation = document.getElementById('delete-confirmation');
    if (!confirmation) return;

    var deleteMessage = document.getElementById('delete-message');
    var undoToast = document.getElementById('undo-modal');
    var undoButton = document.getElementById('undo-btn');
    var undoMessage = document.getElementById('undo-message');
    var countdown = document.getElementById('undo-countdown');
    var deleteButtons = document.querySelectorAll('.delete-form .delete');
    var selected = null;
    var pending = null;

    function closeConfirmation() {
      var task = selected;
      selected = null;
      confirmation.close();
      task.button.focus({ preventScroll: true });
      return task;
    }

    function setDeleteDisabled(disabled) {
      deleteButtons.forEach(function (button) { button.disabled = disabled; });
    }

    deleteButtons.forEach(function (button) {
      button.addEventListener('click', function () {
        if (pending || confirmation.open) return;
        var item = button.closest('.task-item');
        var title = item.querySelector('.task-title').textContent.trim();
        selected = { button: button, form: button.form, item: item, title: title };
        deleteMessage.textContent = '“' + title + '” will be removed.';
        confirmation.showModal();
      });
    });

    document.getElementById('cancel-delete').addEventListener('click', closeConfirmation);
    confirmation.addEventListener('cancel', function (event) {
      event.preventDefault();
      closeConfirmation();
    });

    document.getElementById('confirm-delete').addEventListener('click', function () {
      var task = closeConfirmation();
      setDeleteDisabled(true);
      task.item.classList.add('pending-delete');

      var secondsLeft = 3;
      undoMessage.textContent = '“' + task.title + '” will be deleted in three seconds.';
      countdown.textContent = secondsLeft;
      undoToast.hidden = false;
      undoButton.focus({ preventScroll: true });

      pending = {
        task: task,
        intervalId: setInterval(function () {
          countdown.textContent = --secondsLeft;
        }, 1000),
        timeoutId: setTimeout(function () {
          clearInterval(pending.intervalId);
          undoToast.hidden = true;
          task.form.submit();
        }, 3000)
      };
    });

    undoButton.addEventListener('click', function () {
      if (!pending) return;
      clearTimeout(pending.timeoutId);
      clearInterval(pending.intervalId);
      var task = pending.task;
      pending = null;
      task.item.classList.remove('pending-delete');
      undoToast.hidden = true;
      setDeleteDisabled(false);
      task.button.focus({ preventScroll: true });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    markOverdueTasks();
    initUndoDelete();
  });
})();

document.querySelectorAll('.show-password').forEach(function (btn) {
  btn.addEventListener('click', function () {
    var input = document.getElementById(btn.dataset.target);
    if (!input) return;
    var reveal = input.type === 'password';
    input.type = reveal ? 'text' : 'password';
    btn.textContent = reveal ? 'Hide' : 'Show';
  });
});
 

// Warn before leaving Profile with unsaved edits
(function () {
  const forms = document.querySelectorAll('form[data-warn-unsaved]');
  let hasUnsavedChanges = false;

  forms.forEach((form) => {
    form.addEventListener('input', () => { hasUnsavedChanges = true; });
    form.addEventListener('reset', () => { hasUnsavedChanges = false; });
    form.addEventListener('submit', () => { hasUnsavedChanges = false; });
  });

  window.addEventListener('beforeunload', (event) => {
    if (!hasUnsavedChanges) return;
    event.preventDefault();
    event.returnValue = '';
  });
})();

// Keep submitter values (notably list_id) when disabling submit buttons.
document.addEventListener('submit', function (event) {
  if (event.defaultPrevented) return;
  var form = event.target;
  if (form.dataset.submitting) {
    event.preventDefault();
    return;
  }
  var submitter = event.submitter;
  if (submitter && submitter.name) {
    var value = document.createElement('input');
    value.type = 'hidden';
    value.name = submitter.name;
    value.value = submitter.value;
    form.appendChild(value);
  }
  form.dataset.submitting = 'true';
  form.setAttribute('aria-busy', 'true');
  form.querySelectorAll('button[type="submit"], input[type="submit"]').forEach(function (button) {
    button.disabled = true;
  });
});
