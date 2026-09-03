const editor = document.querySelector("#card-editor");

if (editor) {
  const isCreate = editor.dataset.cardMode === "create";
  const preview = document.querySelector(".preview-panel iframe");
  const resources = ["lmd", "intelligence", "logistics", "medical", "technology"];
  const resourceLabels = {
    lmd: "LMD",
    intelligence: "Intelligence",
    logistics: "Logistics",
    medical: "Medical",
    technology: "Technology",
  };

  const number = (name) => Number(editor.elements[name].value);

  const syncPreview = () => {
    const card = preview?.contentDocument?.querySelector(".card");
    const image = preview?.contentDocument?.querySelector(".art img");
    if (!card || !image) return;

    const resource = editor.elements.resource_type.value;
    card.classList.remove(...resources.map((name) => `resource-${name}`));
    card.classList.add(`resource-${resource}`);
    card.style.setProperty("--card-background", editor.elements.background_color.value);

    image.style.objectPosition = `${number("artwork_x")}% ${number("artwork_y")}%`;
    image.style.transform = `scale(${number("artwork_scale")})`;
    image.style.transformOrigin = "center center";

    const affinity = card.querySelector(".resource-affinity");
    if (affinity) affinity.textContent = resourceLabels[resource] ?? resource;
  };

  const setupArtworkDragging = () => {
    const document = preview?.contentDocument;
    const image = document?.querySelector(".art img");
    if (!image) return;

    image.draggable = false;
    image.style.cursor = "grab";

    let dragging = false;
    let startX = 0;
    let startY = 0;
    let originalX = 50;
    let originalY = 50;

    image.addEventListener("pointerdown", (event) => {
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
      if (!dragging) return;
      event.preventDefault();
      const rect = image.parentElement.getBoundingClientRect();
      const nextX = originalX - ((event.clientX - startX) / rect.width) * 100;
      const nextY = originalY - ((event.clientY - startY) / rect.height) * 100;
      editor.elements.artwork_x.value = Math.max(-200, Math.min(300, nextX)).toFixed(1);
      editor.elements.artwork_y.value = Math.max(-200, Math.min(300, nextY)).toFixed(1);
      syncPreview();
    });

    const stopDragging = () => {
      dragging = false;
      image.style.cursor = "grab";
    };
    image.addEventListener("pointerup", stopDragging);
    image.addEventListener("pointercancel", stopDragging);

    image.addEventListener("wheel", (event) => {
      event.preventDefault();
      const current = number("artwork_scale");
      const next = current + (event.deltaY < 0 ? 0.05 : -0.05);
      editor.elements.artwork_scale.value = Math.max(0.5, Math.min(3, next)).toFixed(2);
      syncPreview();
    }, { passive: false });
  };

  const syncFromInputs = () => syncPreview();
  ["resource_type", "artwork_x", "artwork_y", "artwork_scale", "background_color"].forEach((name) => {
    editor.elements[name].addEventListener("input", syncFromInputs);
    editor.elements[name].addEventListener("change", syncFromInputs);
  });
  preview?.addEventListener("load", () => {
    syncPreview();
    setupArtworkDragging();
  });

  const uploadButton = document.querySelector("#upload-artwork");
  const fileInput = document.querySelector("#artwork-file");
  const uploadMessage = document.querySelector("#artwork-upload-message");

  uploadButton?.addEventListener("click", async () => {
    const file = fileInput?.files?.[0];
    if (!file) {
      uploadMessage.textContent = "Choose an image first.";
      uploadMessage.className = "save-message error";
      return;
    }
    if (!/^(image\/png|image\/jpeg|image\/webp)$/.test(file.type)) {
      uploadMessage.textContent = "Use PNG, JPEG, or WebP.";
      uploadMessage.className = "save-message error";
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      uploadMessage.textContent = "Image must be 10 MB or smaller.";
      uploadMessage.className = "save-message error";
      return;
    }

    uploadButton.disabled = true;
    uploadMessage.textContent = "Uploading…";
    uploadMessage.className = "save-message";

    try {
      const data = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });

      const response = await fetch(`/api/card/${editor.dataset.cardId}/artwork`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ data }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail ?? "Unable to upload artwork.");

      editor.elements.artwork.value = result.artwork;
      uploadMessage.textContent = "Artwork uploaded. Save the card to keep the current layout.";
      uploadMessage.className = "save-message saved";
      if (preview?.contentDocument) {
        const image = preview.contentDocument.querySelector(".art img");
        if (image) {
          image.src = `/${result.artwork}?v=${Date.now()}`;
        }
      }
    } catch (error) {
      uploadMessage.textContent = error.message;
      uploadMessage.className = "save-message error";
    } finally {
      uploadButton.disabled = false;
    }
  });

  editor.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
      id: editor.elements.id.value.trim(),
      name: editor.elements.name.value,
      tier: number("tier"),
      operator_class: editor.elements.operator_class.value,
      influence: number("influence"),
      artwork: editor.elements.artwork.value,
      artwork_x: number("artwork_x"),
      artwork_y: number("artwork_y"),
      artwork_scale: number("artwork_scale"),
      background_color: editor.elements.background_color.value,
      resource_type: editor.elements.resource_type.value,
      rhodes_island_emblems: number("rhodes_island_emblems"),
      cost: {
        lmd: number("cost_lmd"),
        intelligence: number("cost_intelligence"),
        logistics: number("cost_logistics"),
        medical: number("cost_medical"),
        technology: number("cost_technology"),
      },
    };

    const message = editor.querySelector(".save-message");
    const endpoint = isCreate ? "/api/card" : `/api/card/${editor.dataset.cardId}`;
    const method = isCreate ? "POST" : "PUT";

    try {
      const response = await fetch(endpoint, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const result = await response.json();
      if (!response.ok) {
        message.textContent = result.detail ?? "Unable to save card.";
        message.className = "save-message error";
        return;
      }

      if (isCreate) {
        window.location.assign(`/card/${result.card.id}`);
        return;
      }

      message.textContent = "Saved. Use Generate PNG when ready.";
      message.className = "save-message saved";
      window.setTimeout(() => window.location.reload(), 650);
    } catch (error) {
      message.textContent = "Unable to reach the server.";
      message.className = "save-message error";
    }
  });
}
