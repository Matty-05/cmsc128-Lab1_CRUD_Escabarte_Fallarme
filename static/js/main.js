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

      // Delete with a 3-second undo window.
      function initUndoDelete() {
        var modal = document.getElementById('undo-modal');
        var undoBtn = document.getElementById('undo-btn');
        var messageEl = document.getElementById('undo-message');
        var countdownEl = document.getElementById('undo-countdown');
        var pending = null;

        function finalizePending() {
          if (!pending) return;
          clearTimeout(pending.timeoutId);
          clearInterval(pending.intervalId);
          modal.hidden = true;
          pending.form.submit();
          pending = null;
        }

        function cancelPending() {
          if (!pending) return;
          clearTimeout(pending.timeoutId);
          clearInterval(pending.intervalId);
          pending.item.classList.remove('pending-delete');
          modal.hidden = true;
          pending = null;
        }

        document.querySelectorAll('.delete-form').forEach(function (form) {
          form.addEventListener('submit', function (e) {
            e.preventDefault();

            if (pending) finalizePending();

            var item = form.closest('.task-item');
            var titleEl = item.querySelector('.task-title');
            var title = titleEl ? titleEl.textContent : 'Task';

            item.classList.add('pending-delete');
            messageEl.textContent = '"' + title + '" will be deleted.';

            var secondsLeft = 3;
            countdownEl.textContent = secondsLeft;
            modal.hidden = false;

            var intervalId = setInterval(function () {
              secondsLeft -= 1;
              if (secondsLeft >= 0) countdownEl.textContent = secondsLeft;
              if (secondsLeft <= 0) clearInterval(intervalId);
            }, 1000);

            var timeoutId = setTimeout(finalizePending, 3000);

            pending = { form: form, item: item, timeoutId: timeoutId, intervalId: intervalId };
          });
        });

        undoBtn.addEventListener('click', cancelPending);
      }

      document.addEventListener('DOMContentLoaded', function () {
        markOverdueTasks();
        initUndoDelete();
      });
    })();