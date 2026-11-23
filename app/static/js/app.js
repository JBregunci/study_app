(function () {
  "use strict";

  var root = document.documentElement;

  function currentTheme() {
    return root.dataset.theme === "dark" ? "dark" : "light";
  }

  function updateThemeButton() {
    var button = document.getElementById("theme-toggle");
    if (!button) return;
    var dark = currentTheme() === "dark";
    button.textContent = dark ? "Tema claro" : "Tema escuro";
    button.setAttribute("aria-pressed", dark ? "true" : "false");
  }

  function setupTheme() {
    var button = document.getElementById("theme-toggle");
    if (!button || button.dataset.ready) return;
    button.dataset.ready = "1";
    updateThemeButton();
    button.addEventListener("click", function () {
      var next = currentTheme() === "dark" ? "light" : "dark";
      root.dataset.theme = next;
      localStorage.setItem("study-theme", next);
      updateThemeButton();
    });
  }

  function formatClock(total) {
    total = Math.max(0, Math.floor(total));
    var hours = Math.floor(total / 3600);
    var minutes = Math.floor((total % 3600) / 60);
    var seconds = total % 60;
    var mm = String(minutes).padStart(2, "0");
    var ss = String(seconds).padStart(2, "0");
    return hours ? hours + ":" + mm + ":" + ss : mm + ":" + ss;
  }

  function submitTimeout(form) {
    if (!form) return;
    form.noValidate = true;
    var timedOut = form.querySelector('input[name="timed_out"]');
    if (timedOut) timedOut.value = "1";
    var submit = form.querySelector('button[type="submit"]');
    if (submit) submit.disabled = true;
    if (typeof form.requestSubmit === "function") form.requestSubmit();
    else form.submit();
  }

  function setupTimers(scope) {
    scope.querySelectorAll("[data-timer]").forEach(function (timer) {
      if (timer.dataset.ready) return;
      timer.dataset.ready = "1";
      var elapsed = Number(timer.dataset.elapsed || 0);
      var limit = Number(timer.dataset.limit || 0);
      var form = document.getElementById(timer.dataset.form || "");
      var finished = false;
      var interval = null;

      function render() {
        timer.textContent = formatClock(elapsed);
        if (limit > 0) {
          var remaining = Math.max(limit - elapsed, 0);
          timer.classList.toggle("timer-warning", remaining <= 30);
          timer.title = formatClock(remaining) + " restantes";
          if (!finished && remaining <= 0) {
            finished = true;
            submitTimeout(form);
          }
        }
      }

      if (form) {
        form.addEventListener(
          "submit",
          function () {
            finished = true;
            if (interval) window.clearInterval(interval);
          },
          { once: true }
        );
      }

      render();
      if (!finished) {
        interval = window.setInterval(function () {
          elapsed += 1;
          render();
        }, 1000);
      }
    });
  }

  function setupKeyboard() {
    document.addEventListener("keydown", function (event) {
      if (event.ctrlKey || event.metaKey || event.altKey) return;
      if (!(event.target instanceof Element)) return;
      if (
        event.target.closest(
          "input:not([type='radio']), textarea, select, button, a, summary"
        )
      ) {
        return;
      }
      var key = event.key.toLowerCase();
      var form = document.getElementById("question-form");
      if (form) {
        var radios = Array.prototype.slice.call(
          form.querySelectorAll('input[type="radio"]')
        );
        var radio =
          radios.find(function (item) {
            return item.dataset.key === key;
          }) || radios[Number(key) - 1];
        if (radio) {
          radio.checked = true;
          event.preventDefault();
          return;
        }
        if (key === "enter") {
          event.preventDefault();
          if (typeof form.requestSubmit === "function") form.requestSubmit();
          else form.submit();
          return;
        }
      }
      if (key === "n") {
        var next = document.querySelector("[data-next]");
        if (next) {
          event.preventDefault();
          next.click();
        }
      }
    });
  }


  function setupContestDropdowns() {
    document.querySelectorAll("[data-contest-dropdown]").forEach(function (dropdown) {
      if (dropdown.dataset.ready) return;
      dropdown.dataset.ready = "1";
      var toggle = dropdown.querySelector("[data-contest-toggle]");
      var menu = dropdown.querySelector("[data-contest-menu]");
      var logo = dropdown.querySelector("[data-contest-logo]");
      var label = dropdown.querySelector("[data-contest-label]");
      var edicao = dropdown.querySelector("[data-contest-edicao]");
      var concurso = dropdown.querySelector("[data-contest-concurso]");
      if (!toggle || !menu || !logo || !label || !edicao || !concurso) return;

      function close() {
        menu.hidden = true;
        toggle.setAttribute("aria-expanded", "false");
      }

      function open() {
        menu.hidden = false;
        toggle.setAttribute("aria-expanded", "true");
      }

      toggle.addEventListener("click", function (event) {
        event.stopPropagation();
        if (menu.hidden) open();
        else close();
      });

      menu.querySelectorAll("[data-label][data-logo]").forEach(function (option) {
        option.addEventListener("click", function (event) {
          event.preventDefault();
          edicao.value = option.dataset.edicao || "";
          concurso.value = option.dataset.concurso || "";
          label.textContent = option.dataset.label || "Todos os concursos";
          logo.src = option.dataset.logo;
          menu.querySelectorAll(".contest-option").forEach(function (item) {
            item.classList.toggle("is-active", item === option);
          });
          close();
        });
      });

      document.addEventListener("click", function (event) {
        if (!dropdown.contains(event.target)) close();
      });

      dropdown.addEventListener("keydown", function (event) {
        if (event.key === "Escape") close();
      });
    });
  }

  function setupBuilder() {
    var filters = document.querySelector("[data-picker-filters]");
    if (!filters || filters.dataset.ready) return;
    filters.dataset.ready = "1";

    var items = Array.prototype.slice.call(
      document.querySelectorAll("[data-picker-item]")
    );
    var selectedCount = document.querySelector("[data-selected-count]");
    var visibleCount = document.querySelector("[data-visible-count]");
    var empty = document.querySelector("[data-picker-empty]");
    var search = filters.querySelector('[data-picker-filter="search"]');
    var topic = filters.querySelector('[data-picker-filter="topic"]');
    var exam = filters.querySelector('[data-picker-filter="exam"]');
    var difficulty = filters.querySelector('[data-picker-filter="difficulty"]');

    function checkboxes() {
      return Array.prototype.slice.call(
        document.querySelectorAll("[data-picker-checkbox]")
      );
    }

    function updateCount() {
      if (selectedCount) {
        selectedCount.textContent = String(
          checkboxes().filter(function (item) {
            return item.checked;
          }).length
        );
      }
      if (visibleCount) {
        visibleCount.textContent = String(
          items.filter(function (item) {
            return !item.hidden;
          }).length
        );
      }
      if (empty) {
        empty.hidden = items.some(function (item) {
          return !item.hidden;
        });
      }
    }

    function apply() {
      var query = (search && search.value ? search.value : "").trim().toLowerCase();
      var topicValue = topic ? topic.value : "";
      var examValue = exam ? exam.value : "";
      var difficultyValue = difficulty ? difficulty.value : "";
      items.forEach(function (item) {
        var matchesSearch = !query || (item.dataset.text || "").includes(query);
        var matchesTopic = !topicValue || item.dataset.topic === topicValue;
        var examSlugs = (item.dataset.exams || "").split(",");
        var matchesExam = !examValue || examSlugs.includes(examValue);
        var matchesDifficulty =
          !difficultyValue || item.dataset.difficulty === difficultyValue;
        item.hidden = !(
          matchesSearch &&
          matchesTopic &&
          matchesExam &&
          matchesDifficulty
        );
      });
      updateCount();
    }

    [search, topic, exam, difficulty].forEach(function (control) {
      if (!control) return;
      control.addEventListener(
        control.tagName === "INPUT" ? "input" : "change",
        apply
      );
    });

    filters.addEventListener("submit", function (event) {
      event.preventDefault();
    });
    filters.addEventListener("keydown", function (event) {
      if (event.key === "Enter") event.preventDefault();
    });

    document.querySelectorAll("[data-random-select]").forEach(function (button) {
      button.addEventListener("click", function () {
        var amount = Number(button.dataset.randomSelect || 0);
        checkboxes().forEach(function (checkbox) {
          checkbox.checked = false;
        });
        var visible = items.filter(function (item) {
          return !item.hidden;
        });
        for (var index = visible.length - 1; index > 0; index -= 1) {
          var randomIndex = Math.floor(Math.random() * (index + 1));
          var swap = visible[index];
          visible[index] = visible[randomIndex];
          visible[randomIndex] = swap;
        }
        visible.slice(0, amount).forEach(function (item) {
          var checkbox = item.querySelector("[data-picker-checkbox]");
          if (checkbox) checkbox.checked = true;
        });
        updateCount();
      });
    });

    var clear = document.querySelector("[data-clear-selection]");
    if (clear) {
      clear.addEventListener("click", function () {
        checkboxes().forEach(function (checkbox) {
          checkbox.checked = false;
        });
        updateCount();
      });
    }

    document.addEventListener("change", function (event) {
      if (event.target.matches("[data-picker-checkbox]")) updateCount();
    });

    apply();
  }

  function setupConfirms() {
    document.querySelectorAll("form[data-confirm]").forEach(function (form) {
      if (form.dataset.ready) return;
      form.dataset.ready = "1";
      form.addEventListener("submit", function (event) {
        if (!window.confirm(form.dataset.confirm || "Confirmar esta ação?")) {
          event.preventDefault();
        }
      });
    });
  }

  function setupAfterSwap(event) {
    var target = event.target;
    if (target && target.querySelectorAll) {
      setupTimers(target);
      var feedback = target.querySelector("[data-feedback-focus]");
      if (feedback) feedback.focus();
    }
    setupConfirms();
  }

  function init(scope) {
    setupTheme();
    setupTimers(scope || document);
    setupContestDropdowns();
    setupBuilder();
    setupConfirms();
  }

  document.addEventListener("DOMContentLoaded", function () {
    init(document);
  });
  document.body.addEventListener("htmx:afterSwap", setupAfterSwap);
  document.body.addEventListener("htmx:load", function (event) {
    if (event.target && event.target.querySelectorAll) {
      setupTimers(event.target);
      setupConfirms();
    }
  });
  setupKeyboard();
})();
