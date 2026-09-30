(function () {
  "use strict";

  const form = document.getElementById("routine-editor");
  const dataEl = document.getElementById("editor-data");
  if (!form || !dataEl) return;

  const data = JSON.parse(dataEl.textContent);
  const catalog = new Map(data.catalog.map((ex) => [ex.id, ex]));
  const LIMITS = {
    default_sets: [1, 20, "series"],
    default_reps: [1, 100, "repeticiones"],
    intensity_pct: [1, 100, "% del peso máximo"],
    duration_min: [1, 240, "minutos"],
    rest_seconds: [0, 900, "segundos de descanso"],
  };

  const titleInput = document.getElementById("editor-title");
  const list = document.getElementById("editor-list");
  const empty = document.getElementById("editor-empty");
  const count = document.getElementById("editor-count");
  const feedbackEl = document.getElementById("editor-feedback");
  const saveBtn = document.getElementById("editor-save");
  const itemTpl = document.getElementById("editor-item-tpl");

  let items = data.items.map((it) => ({ ...it }));
  let dirty = false;
  titleInput.value = data.title;

  async function postJSON(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify(body || {}),
    });
    const payload = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = Array.isArray(payload.detail) ? "Revisa los datos." : payload.detail;
      throw new Error(detail || "No se pudo completar la acción.");
    }
    return payload;
  }

  function feedback(text, kind) {
    feedbackEl.hidden = !text;
    feedbackEl.textContent = text || "";
    feedbackEl.className = "share-feedback" + (kind ? " " + kind : "");
  }

  function markDirty() {
    dirty = true;
    feedback("");
  }

  function defaultsFor(ex) {
    return ex.cardio
      ? { exercise_id: ex.id, default_sets: 1, default_reps: 1, intensity_pct: null,
          duration_min: 10, rest_seconds: 60, note: "" }
      : { exercise_id: ex.id, default_sets: 3, default_reps: 10, intensity_pct: null,
          duration_min: null, rest_seconds: 90, note: "" };
  }

  /* ---------------------------------------------------------- lista */
  function render() {
    list.replaceChildren();
    items.forEach((item, idx) => {
      const ex = catalog.get(item.exercise_id);
      const node = itemTpl.content.firstElementChild.cloneNode(true);
      node.dataset.index = String(idx);
      node.querySelector(".editor-item-n").textContent = String(idx + 1);
      const thumb = node.querySelector(".gv-thumb");
      thumb.classList.add(ex.illustrated ? "is-illustration" : "is-icon");
      thumb.querySelector("img").src = ex.image;
      node.querySelector(".gv-exercise-name").textContent = ex.name;
      node.querySelector(".editor-item-meta").textContent =
        `${ex.group_label} · ${ex.equipment}` + (ex.enabled ? "" : " · no está en Mi gym");
      node.querySelectorAll("[data-kind]").forEach((label) => {
        label.hidden = label.dataset.kind !== (ex.cardio ? "cardio" : "strength");
      });
      node.querySelectorAll("[data-f]").forEach((input) => {
        const value = item[input.dataset.f];
        input.value = value === null || value === undefined ? "" : String(value);
        input.setAttribute("aria-label", `${input.closest("label").textContent.trim() || "Nota"} de ${ex.name}`);
      });
      const [up, down, remove] = node.querySelectorAll("[data-act]");
      up.disabled = idx === 0;
      down.disabled = idx === items.length - 1;
      up.setAttribute("aria-label", `Subir ${ex.name}`);
      down.setAttribute("aria-label", `Bajar ${ex.name}`);
      remove.setAttribute("aria-label", `Quitar ${ex.name}`);
      list.appendChild(node);
    });
    empty.hidden = items.length > 0;
    count.textContent = items.length ? `(${items.length})` : "";
  }

  list.addEventListener("input", (e) => {
    const input = e.target.closest("[data-f]");
    if (!input) return;
    const item = items[Number(input.closest(".editor-item").dataset.index)];
    const field = input.dataset.f;
    if (field === "note") {
      item.note = input.value;
    } else {
      item[field] = input.value.trim() === "" ? null : Number(input.value);
    }
    markDirty();
  });

  list.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-act]");
    if (!btn) return;
    const idx = Number(btn.closest(".editor-item").dataset.index);
    const act = btn.dataset.act;
    let focusIdx = idx;
    if (act === "up" && idx > 0) {
      [items[idx - 1], items[idx]] = [items[idx], items[idx - 1]];
      focusIdx = idx - 1;
    } else if (act === "down" && idx < items.length - 1) {
      [items[idx + 1], items[idx]] = [items[idx], items[idx + 1]];
      focusIdx = idx + 1;
    } else if (act === "remove") {
      items.splice(idx, 1);
      focusIdx = Math.min(idx, items.length - 1);
    } else {
      return;
    }
    markDirty();
    render();
    const target = list.children[focusIdx];
    if (target) {
      const same = target.querySelector(`[data-act="${act}"]:not(:disabled)`);
      (same || target.querySelector("[data-act]:not(:disabled)"))?.focus();
    } else {
      document.getElementById("editor-add").focus();
    }
  });

  titleInput.addEventListener("input", markDirty);

  /* ---------------------------------------------------------- catálogo */
  const picker = document.getElementById("picker-dialog");
  const search = document.getElementById("picker-search");
  const groupsEl = document.getElementById("picker-groups");
  const pickerList = document.getElementById("picker-list");
  const hiddenNote = document.getElementById("picker-hidden");
  let group = "all";
  let showAll = false;

  const normalize = (s) => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();

  function renderGroups() {
    groupsEl.replaceChildren();
    [{ key: "all", label: "Todos" }, ...data.groups].forEach((g) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "gv-tab" + (g.key === group ? " active" : "");
      b.textContent = g.label;
      b.setAttribute("aria-pressed", g.key === group ? "true" : "false");
      b.addEventListener("click", () => {
        group = g.key;
        renderGroups();
        renderPicker();
      });
      groupsEl.appendChild(b);
    });
  }

  function renderPicker() {
    const q = normalize(search.value.trim());
    const added = new Set(items.map((it) => it.exercise_id));
    const matches = data.catalog.filter(
      (ex) => (group === "all" || ex.group === group) && (!q || normalize(ex.name).includes(q))
    );
    const visible = showAll ? matches : matches.filter((ex) => ex.enabled);
    const hidden = matches.length - visible.length;
    pickerList.replaceChildren();
    visible.forEach((ex) => {
      const li = document.createElement("li");
      const b = document.createElement("button");
      b.type = "button";
      b.className = "gv-exercise-row picker-row";
      const isAdded = added.has(ex.id);
      b.disabled = isAdded;
      b.innerHTML =
        `<span class="gv-thumb editor-thumb ${ex.illustrated ? "is-illustration" : "is-icon"}"><img alt="" loading="lazy"></span>` +
        `<span class="gv-exercise-row-body"><span class="gv-exercise-name"></span><span class="editor-item-meta"></span></span>` +
        `<i class="ti ${isAdded ? "ti-check" : "ti-plus"} picker-icon" aria-hidden="true"></i>`;
      b.querySelector("img").src = ex.image;
      b.querySelector(".gv-exercise-name").textContent = ex.name;
      b.querySelector(".editor-item-meta").textContent =
        `${ex.group_label} · ${ex.equipment}` + (isAdded ? " · ya está en la rutina" : "");
      b.addEventListener("click", () => {
        items.push(defaultsFor(ex));
        markDirty();
        render();
        renderPicker();
        feedback(`${ex.name} añadido.`, "ok");
      });
      li.appendChild(b);
      pickerList.appendChild(li);
    });
    if (!visible.length) {
      const li = document.createElement("li");
      li.className = "gym-empty";
      li.textContent = "Ningún ejercicio coincide.";
      pickerList.appendChild(li);
    }
    hiddenNote.hidden = !hidden && !showAll;
    hiddenNote.replaceChildren();
    if (hidden || showAll) {
      hiddenNote.append(
        showAll ? "Mostrando todo el catálogo. " : `${hidden} oculto${hidden > 1 ? "s" : ""} por tu equipo en Mi gym. `
      );
      const toggle = document.createElement("button");
      toggle.type = "button";
      toggle.className = "gv-btn-inline";
      toggle.textContent = showAll ? "Ver solo mi equipo" : "Ver todos";
      toggle.addEventListener("click", () => {
        showAll = !showAll;
        renderPicker();
      });
      hiddenNote.appendChild(toggle);
    }
  }

  search.addEventListener("input", renderPicker);
  document.getElementById("editor-add").addEventListener("click", () => {
    renderGroups();
    renderPicker();
    picker.showModal();
    search.focus();
  });

  /* ---------------------------------------------------------- guardar */
  function validate() {
    const title = titleInput.value.trim();
    if (!title) return ["Ponle un nombre a la rutina.", titleInput];
    if (!items.length) return ["Añade al menos un ejercicio.", document.getElementById("editor-add")];
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      const ex = catalog.get(item.exercise_id);
      const fields = ex.cardio
        ? ["duration_min", "rest_seconds"]
        : ["default_sets", "default_reps", "intensity_pct", "rest_seconds"];
      for (const f of fields) {
        const v = item[f];
        if (f === "intensity_pct" && v === null) continue;
        const [lo, hi, label] = LIMITS[f];
        if (v === null || !Number.isInteger(v) || v < lo || v > hi) {
          const input = list.children[i].querySelector(`[data-f="${f}"]`);
          return [`${ex.name}: ${label} entre ${lo} y ${hi}.`, input];
        }
      }
    }
    return null;
  }

  function payload() {
    return {
      title: titleInput.value.trim(),
      items: items.map((it) => {
        const ex = catalog.get(it.exercise_id);
        return {
          exercise_id: it.exercise_id,
          default_sets: ex.cardio ? 1 : it.default_sets,
          default_reps: ex.cardio ? 1 : it.default_reps,
          intensity_pct: ex.cardio ? null : it.intensity_pct,
          duration_min: ex.cardio ? it.duration_min : null,
          rest_seconds: it.rest_seconds,
          note: (it.note || "").trim(),
        };
      }),
    };
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const problem = validate();
    if (problem) {
      feedback(problem[0], "error");
      problem[1].focus();
      return;
    }
    saveBtn.disabled = true;
    feedback("Guardando…");
    try {
      const url = data.templateId
        ? `/api/v1/workouts/${data.templateId}/items`
        : "/api/v1/workouts";
      const res = await postJSON(url, payload());
      dirty = false;
      window.location.href = res.url;
    } catch (err) {
      saveBtn.disabled = false;
      feedback(err.message, "error");
    }
  });

  /* ---------------------------------------------------------- duplicar y eliminar */
  const dupBtn = document.getElementById("editor-duplicate");
  if (dupBtn) {
    dupBtn.addEventListener("click", async () => {
      if (dirty) {
        feedback("Guarda los cambios antes de duplicar.", "error");
        return;
      }
      dupBtn.disabled = true;
      try {
        const res = await postJSON(`/api/v1/workouts/${data.templateId}/duplicate`);
        window.location.href = res.url;
      } catch (err) {
        dupBtn.disabled = false;
        feedback(err.message, "error");
      }
    });
  }

  const delDialog = document.getElementById("delete-dialog");
  if (delDialog) {
    document.getElementById("editor-delete").addEventListener("click", () => {
      delDialog.showModal();
      document.getElementById("delete-cancel").focus();
    });
    const confirmBtn = document.getElementById("delete-confirm");
    confirmBtn.addEventListener("click", async () => {
      confirmBtn.disabled = true;
      try {
        const res = await postJSON(`/api/v1/workouts/${data.templateId}/delete`);
        dirty = false;
        window.location.href = res.url;
      } catch (err) {
        confirmBtn.disabled = false;
        delDialog.close();
        feedback(err.message, "error");
      }
    });
  }

  window.addEventListener("beforeunload", (e) => {
    if (dirty) e.preventDefault();
  });

  render();
})();
