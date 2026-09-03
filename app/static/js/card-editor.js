const editor = document.querySelector("#card-editor");

if (editor) {
  const isCreate = editor.dataset.cardMode === "create";
  const preview = document.querySelector(".preview-panel iframe");
  const mouseToggle = document.querySelector("#artwork-mouse-enabled");
  const resources = ["lmd", "intelligence", "logistics", "medical", "technology"];
  const labels = { lmd: "LMD", intelligence: "Intelligence", logistics: "Logistics", medical: "Medical", technology: "Technology" };
  const number = (name) => Number(editor.elements[name].value);

  function syncPreview() {
    const doc = preview?.contentDocument;
    const card = doc?.querySelector(".card");
    const image = doc?.querySelector(".art img");
    if (!card || !image) return;
    const resource = editor.elements.resource_type.value;
    card.classList.remove(...resources.map((r) => `resource-${r}`));
    card.classList.add(`resource-${resource}`);
    card.style.setProperty("--card-background", editor.elements.background_color.value);
    const x = number("artwork_x");
    const y = number("artwork_y");
    image.style.objectPosition = "50% 50%";
    image.style.transform = `translateX(${(50 - x) * 4}px) translateY(${(y - 50) * 4}px) scale(${number("artwork_scale")})`;
    image.style.transformOrigin = "center center";
    const affinity = card.querySelector(".resource-affinity");
    if (affinity) affinity.textContent = labels[resource] ?? resource;
  }

  function setupDragging() {
    const image = preview?.contentDocument?.querySelector(".art img");
    if (!image) return;
    image.draggable = false;
    let dragging = false, startX = 0, startY = 0, originalX = 50, originalY = 50;
    const enabled = () => mouseToggle?.checked !== false;
    const cursor = () => { image.style.cursor = enabled() ? "grab" : "default"; };
    cursor();
    image.addEventListener("pointerdown", (event) => {
      if (!enabled()) return;
      event.preventDefault();
      dragging = true;
      startX = event.clientX;
      startY = event.clientY;
      originalX = number("artwork_x");
      originalY = number("artwork_y");
      image.setPointerCapture(event.pointerId);
      image.style.cursor = "grabbing";
    });
    image.addEventListener("pointermove", (event) => {
      if (!dragging || !enabled()) return;
      event.preventDefault();
      const rect = image.parentElement.getBoundingClientRect();
      const x = originalX - ((event.clientX - startX) / rect.width) * 100;
      const y = originalY + ((event.clientY - startY) / rect.height) * 25;
      editor.elements.artwork_x.value = Math.max(-200, Math.min(300, x)).toFixed(1);
      editor.elements.artwork_y.value = Math.max(-200, Math.min(300, y)).toFixed(1);
      syncPreview();
    });
    const stop = () => { dragging = false; cursor(); };
    image.addEventListener("pointerup", stop);
    image.addEventListener("pointercancel", stop);
    image.addEventListener("wheel", (event) => {
      if (!enabled()) return;
      event.preventDefault();
      const next = number("artwork_scale") + (event.deltaY < 0 ? 0.05 : -0.05);
      editor.elements.artwork_scale.value = Math.max(0.5, Math.min(3, next)).toFixed(2);
      syncPreview();
    }, { passive: false });
    mouseToggle?.addEventListener("change", () => { if (dragging) dragging = false; cursor(); });
  }

  ["resource_type", "artwork_x", "artwork_y", "artwork_scale", "background_color"].forEach((name) => {
    editor.elements[name].addEventListener("input", syncPreview);
    editor.elements[name].addEventListener("change", syncPreview);
  });
  preview?.addEventListener("load", () => { syncPreview(); setupDragging(); });

  const fileInput = document.querySelector("#artwork-file");
  const uploadButton = document.querySelector("#upload-artwork");
  const uploadMessage = document.querySelector("#artwork-upload-message");
  const validFile = (file) => file && /^(image\/png|image\/jpeg|image\/webp)$/.test(file.type) && file.size <= 10 * 1024 * 1024;
  const readFile = (file) => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });

  fileInput?.addEventListener("change", async () => {
    const file = fileInput.files?.[0];
    if (!file) return;
    if (!validFile(file)) {
      uploadMessage.textContent = "Use PNG, JPEG, or WebP, up to 10 MB.";
      uploadMessage.className = "save-message error";
      return;
    }
    const data = await readFile(file);
    const image = preview?.contentDocument?.querySelector(".art img");
    if (image) { image.src = data; image.onload = syncPreview; }
    uploadMessage.textContent = isCreate ? "Artwork selected and shown in the preview. It will be saved when you create the card." : "Artwork selected.";
    uploadMessage.className = "save-message saved";
  });

  uploadButton?.addEventListener("click", async () => {
    const file = fileInput?.files?.[0];
    if (!file) { uploadMessage.textContent = "Choose an image first."; uploadMessage.className = "save-message error"; return; }
    if (isCreate) return;
    if (!validFile(file)) { uploadMessage.textContent = "Use PNG, JPEG, or WebP, up to 10 MB."; uploadMessage.className = "save-message error"; return; }
    uploadButton.disabled = true;
    uploadMessage.textContent = "Uploading…";
    try {
      const response = await fetch(`/api/card/${editor.dataset.cardId}/artwork`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ data: await readFile(file) }) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail ?? "Unable to upload artwork.");
      editor.elements.artwork.value = result.artwork;
      const image = preview?.contentDocument?.querySelector(".art img");
      if (image) image.src = `/${result.artwork}?v=${Date.now()}`;
      uploadMessage.textContent = "Artwork uploaded. Save the card to keep the current layout.";
      uploadMessage.className = "save-message saved";
    } catch (error) {
      uploadMessage.textContent = error.message;
      uploadMessage.className = "save-message error";
    } finally { uploadButton.disabled = false; }
  });

  editor.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
      id: editor.elements.id.value.trim(), name: editor.elements.name.value, tier: number("tier"), operator_class: editor.elements.operator_class.value,
      influence: number("influence"), artwork: editor.elements.artwork.value, artwork_x: number("artwork_x"), artwork_y: number("artwork_y"),
      artwork_scale: number("artwork_scale"), background_color: editor.elements.background_color.value, resource_type: editor.elements.resource_type.value,
      rhodes_island_emblems: number("rhodes_island_emblems"), cost: {
        lmd: number("cost_lmd"), intelligence: number("cost_intelligence"), logistics: number("cost_logistics"), medical: number("cost_medical"), technology: number("cost_technology")
      }
    };
    if (isCreate && fileInput?.files?.[0]) {
      const file = fileInput.files[0];
      if (!validFile(file)) { const m = editor.querySelector(".save-message"); m.textContent = "Use PNG, JPEG, or WebP, up to 10 MB."; m.className = "save-message error"; return; }
      payload.artwork_data = await readFile(file);
    }
    const message = editor.querySelector(".save-message");
    try {
      const response = await fetch(isCreate ? "/api/card" : `/api/card/${editor.dataset.cardId}`, { method: isCreate ? "POST" : "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const result = await response.json();
      if (!response.ok) { message.textContent = result.detail ?? "Unable to save card."; message.className = "save-message error"; return; }
      if (isCreate) { window.location.assign(`/card/${result.card.id}`); return; }
      message.textContent = "Saved. Use Generate PNG when ready.";
      message.className = "save-message saved";
      window.setTimeout(() => window.location.reload(), 650);
    } catch { message.textContent = "Unable to reach the server."; message.className = "save-message error"; }
  });
}
