const editor = document.querySelector("#card-editor");

if (editor) {
  const preview = document.querySelector(".preview-panel iframe");
  const resources = ["lmd", "intelligence", "logistics", "medical", "technology"];
  const resourceLabels = {
    lmd: "LMD",
    intelligence: "Intelligence",
    logistics: "Logistics",
    medical: "Medical",
    technology: "Technology",
  };

  const syncPreviewAccent = () => {
    const card = preview?.contentDocument?.querySelector(".card");
    if (!card) return;
    const resource = editor.elements.resource_type.value;
    card.classList.remove(...resources.map((name) => `resource-${name}`));
    card.classList.add(`resource-${resource}`);
    const affinity = card.querySelector(".resource-affinity");
    if (affinity) affinity.textContent = resourceLabels[resource] ?? resource;
  };

  editor.elements.resource_type.addEventListener("change", syncPreviewAccent);
  preview?.addEventListener("load", syncPreviewAccent);

  editor.addEventListener("submit", async (event) => {
    event.preventDefault();
    const number = (name) => Number(editor.elements[name].value);
    const payload = {
      name: editor.elements.name.value,
      tier: number("tier"),
      operator_class: editor.elements.operator_class.value,
      influence: number("influence"),
      artwork: editor.elements.artwork.value,
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
    const response = await fetch(`/api/card/${editor.dataset.cardId}`, {
      method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!response.ok) { message.textContent = result.detail; message.className = "save-message error"; return; }
    message.textContent = "Saved. Use Generate PNG when ready.";
    message.className = "save-message saved";
    window.setTimeout(() => window.location.reload(), 650);
  });
}
