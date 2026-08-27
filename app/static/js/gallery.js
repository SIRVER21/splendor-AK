const search = document.querySelector("#gallery-search");
const cards = [...document.querySelectorAll(".gallery-card")];
const empty = document.querySelector(".empty-gallery");

if (search) {
  search.addEventListener("input", () => {
    const query = search.value.trim().toLowerCase();
    let visible = 0;
    for (const card of cards) {
      const matches = card.dataset.cardId.includes(query) || card.dataset.cardName.includes(query);
      card.hidden = !matches;
      if (matches) visible += 1;
    }
    empty.hidden = visible > 0;
  });
}
