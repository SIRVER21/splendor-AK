const editor = document.querySelector("#card-editor");

if (editor) {
  editor.addEventListener("submit", async (event) => {
    event.preventDefault();
    const number = (name) => Number(editor.elements[name].value);
    const payload = {
      name: editor.elements.name.value,
      tier: number("tier"),
      operator_class: editor.elements.operator_class.value,
      influence: number("influence"),
      artwork: editor.elements.artwork.value,
      rhodes_island_emblems: number("rhodes_island_emblems"),
      originium_bonus: number("originium_bonus"),
      cost: {
        lmd: number("cost_lmd"), intelligence: number("cost_intelligence"),
        logistics: number("cost_logistics"), medical: number("cost_medical"), arts: number("cost_arts"),
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
