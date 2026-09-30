(function () {
  "use strict";

  async function postJSON(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify(body || {}),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = Array.isArray(data.detail) ? "Revisa los datos." : data.detail;
      throw new Error(detail || "No se pudo completar la acción.");
    }
    return data;
  }

  function feedback(el, text, kind) {
    if (!el) return;
    el.hidden = !text;
    el.textContent = text || "";
    el.className = "share-feedback" + (kind ? " " + kind : "");
  }

  /* ---------------------------------------------------------- compartir */
  const shareForm = document.getElementById("share-form");
  if (shareForm) {
    const fb = document.getElementById("share-feedback");
    shareForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(shareForm);
      feedback(fb, "Enviando…");
      try {
        await postJSON("/api/v1/workouts/share", {
          template_id: Number(fd.get("template_id")),
          to_user_id: Number(fd.get("to_user_id")),
          message: String(fd.get("message") || ""),
        });
        feedback(fb, "Rutina compartida. La otra persona puede aceptarla en Compartidos.", "ok");
        setTimeout(() => window.location.reload(), 800);
      } catch (err) {
        feedback(fb, err.message, "error");
      }
    });
  }

  document.querySelectorAll(".accept-share-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const fb = btn.parentElement.querySelector(".share-feedback");
      btn.disabled = true;
      feedback(fb, "Aceptando…");
      try {
        const data = await postJSON(`/api/v1/workouts/shared/${btn.dataset.id}/accept`);
        window.location.href = `/app/workouts?aceptada=${data.id}#rutinas-compartidas`;
      } catch (err) {
        btn.disabled = false;
        feedback(fb, err.message, "error");
      }
    });
  });

  /* ---------------------------------------------------------- diálogos */
  document.querySelectorAll("[data-open-dialog]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const dlg = document.getElementById(btn.dataset.openDialog);
      if (dlg && dlg.showModal) dlg.showModal();
    });
  });
  document.querySelectorAll("dialog").forEach((dlg) => {
    dlg.addEventListener("click", (e) => {
      if (e.target === dlg) dlg.close();
    });
    dlg.querySelectorAll("[data-close-dialog]").forEach((b) =>
      b.addEventListener("click", () => dlg.close())
    );
  });

  const dayShare = document.getElementById("day-share-form");
  if (dayShare) {
    const fb = document.getElementById("day-share-feedback");
    dayShare.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(dayShare);
      feedback(fb, "Enviando…");
      try {
        await postJSON("/api/v1/workouts/share", {
          template_id: Number(dayShare.dataset.templateId),
          to_user_id: Number(fd.get("to_user_id")),
          message: String(fd.get("message") || ""),
        });
        feedback(fb, "¡Listo! La invitación quedó pendiente de aceptar.", "ok");
      } catch (err) {
        feedback(fb, err.message, "error");
      }
    });
  }

  /* ---------------------------------------------------------- iniciar día */
  document.querySelectorAll("[data-start-workout]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const fb = document.getElementById("start-feedback");
      btn.disabled = true;
      try {
        const data = await postJSON(`/api/v1/workouts/${btn.dataset.startWorkout}/start`);
        window.location.href = data.url;
      } catch (err) {
        btn.disabled = false;
        feedback(fb, err.message, "error");
      }
    });
  });

  /* ---------------------------------------------------------- sesión */
  const panel = document.getElementById("session-panel");
  if (panel) {
    const sessionId = panel.dataset.sessionId;
    const exerciseId = Number(panel.dataset.exerciseId);
    const cardio = panel.dataset.cardio === "1";
    const restTotal = Number(panel.dataset.rest) || 90;
    const cardioTotal = Number(panel.dataset.duration) || 300;
    const timerBtn = document.getElementById("rest-timer");
    const timerText = document.getElementById("rest-timer-text");
    const timerHint = document.getElementById("rest-timer-hint");
    const timerFill = document.getElementById("rest-timer-fill");
    const autostartKey = `gymve-rest-${sessionId}-${exerciseId}`;
    let interval = null;
    let startedAt = 0;

    const mmss = (s) => {
      const v = Math.max(0, Math.round(s));
      return String(Math.floor(v / 60)).padStart(2, "0") + ":" + String(v % 60).padStart(2, "0");
    };
    const setFill = (ratio) => {
      const pct = Math.max(0, Math.min(1, ratio)) * 100;
      timerFill.setAttribute("stroke-dasharray", `${pct.toFixed(1)}, 100`);
    };
    const stop = (label) => {
      clearInterval(interval);
      interval = null;
      timerBtn.classList.remove("running");
      timerHint.innerHTML = '<i class="ti ti-player-play"></i>';
      if (label) timerText.textContent = label;
    };
    const tick = () => {
      const elapsed = (Date.now() - startedAt) / 1000;
      if (cardio) {
        timerText.textContent = mmss(elapsed);
        setFill(elapsed / cardioTotal);
        if (elapsed >= cardioTotal && !timerBtn.classList.contains("done")) {
          timerBtn.classList.add("done");
          if (navigator.vibrate) navigator.vibrate([200, 100, 200]);
        }
        return;
      }
      const left = restTotal - elapsed;
      timerText.textContent = mmss(left);
      setFill(left / restTotal);
      if (left <= 0) {
        stop("¡Listo!");
        timerBtn.classList.add("done");
        setFill(0);
        if (navigator.vibrate) navigator.vibrate([200, 100, 200]);
      }
    };
    const start = () => {
      timerBtn.classList.remove("done");
      timerBtn.classList.add("running");
      timerHint.innerHTML = '<i class="ti ti-player-stop"></i>';
      startedAt = Date.now();
      tick();
      interval = setInterval(tick, 250);
    };
    timerBtn.addEventListener("click", () => {
      if (interval) {
        if (cardio) {
          const minutes = Math.max(0.5, Math.round(((Date.now() - startedAt) / 60000) * 2) / 2);
          const input = document.querySelector('#log-set-form input[name="duration_min"]');
          if (input) input.value = minutes;
          stop();
        } else {
          stop(mmss(restTotal));
          setFill(1);
        }
      } else {
        start();
      }
    });
    if (!cardio && sessionStorage.getItem(autostartKey)) {
      sessionStorage.removeItem(autostartKey);
      start();
    }

    const logForm = document.getElementById("log-set-form");
    const logFb = document.getElementById("log-feedback");
    logForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(logForm);
      const body = { exercise_id: exerciseId };
      if (cardio) {
        body.duration_min = Number(fd.get("duration_min"));
      } else {
        body.weight_kg = Number(fd.get("weight_kg") || 0);
        body.reps = Number(fd.get("reps"));
      }
      const submit = logForm.querySelector("button[type=submit]");
      submit.disabled = true;
      try {
        await postJSON(`/api/v1/sessions/${sessionId}/sets`, body);
        if (!cardio) sessionStorage.setItem(autostartKey, "1");
        window.location.reload();
      } catch (err) {
        submit.disabled = false;
        feedback(logFb, err.message, "error");
      }
    });

    document.querySelectorAll("[data-delete-set]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (!window.confirm("¿Borrar esta serie?")) return;
        btn.disabled = true;
        try {
          await postJSON(`/api/v1/sessions/${sessionId}/sets/${btn.dataset.deleteSet}/delete`);
          window.location.reload();
        } catch (err) {
          btn.disabled = false;
          feedback(logFb, err.message, "error");
        }
      });
    });
  }

  document.querySelectorAll("[data-complete-session]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      btn.disabled = true;
      try {
        const data = await postJSON(`/api/v1/sessions/${btn.dataset.completeSession}/complete`);
        window.location.href = data.url;
      } catch {
        btn.disabled = false;
      }
    });
  });

  /* ---------------------------------------------------------- Mi gym */
  const eqForm = document.getElementById("equipment-form");
  if (eqForm) {
    const fb = document.getElementById("equipment-feedback");
    eqForm.addEventListener("change", async () => {
      const enabled = Array.from(eqForm.querySelectorAll("input[name=enabled]:checked")).map(
        (i) => i.value
      );
      feedback(fb, "Guardando…");
      try {
        await postJSON("/api/v1/me/equipment", { enabled });
        feedback(fb, "Equipo actualizado.", "ok");
      } catch (err) {
        feedback(fb, err.message, "error");
      }
    });
  }

  document.querySelectorAll("[data-machine-form]").forEach((form) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      const fb = form.querySelector(".share-feedback");
      try {
        await postJSON(`/api/v1/machines/${form.dataset.machineForm}`, {
          brand: String(fd.get("brand") || ""),
          model: String(fd.get("model") || ""),
          confirmed: fd.get("confirmed") === "on",
        });
        window.location.reload();
      } catch (err) {
        feedback(fb, err.message, "error");
      }
    });
  });
})();
