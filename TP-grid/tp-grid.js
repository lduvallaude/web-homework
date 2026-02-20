document.addEventListener("DOMContentLoaded", () => {
  initialCleanup();
  const grid = document.getElementById("grid");

  const totalEl = document.getElementById("total");
  const redEl = document.getElementById("red");
  const clickedEl = document.getElementById("clicked");

  function updateStats() {
    const squares = grid.querySelectorAll("div");
    const total = squares.length;
    let redCount = 0;
    let clickedCount = 0;

    squares.forEach((sq) => {
      if (sq.classList.contains("red")) redCount++;
      if (sq.classList.contains("clicked")) clickedCount++;
    });

    totalEl.innerText = total;
    redEl.innerText = redCount;
    clickedEl.innerText = clickedCount;
  }

  function toggleColor(element, color) {
    element.style.backgroundColor = color; 
  }

  document.getElementById("btn-add-line").addEventListener("click", () => {
    for (let i = 0; i < 10; i++) {
      const square = document.createElement("div");
      grid.appendChild(square);
      square.addEventListener("mouseover", () => {
        toggleColor(square, "red");
        updateStats();
      });
      square.addEventListener("click", () => {
        toggleColor(square, "blue");
        square.classList.add("clicked");
        updateStats();
      });
    }
    
  });
    



  function addCallbacksToSquares() {
    for (const box of grid.querySelectorAll("div")) {
      
      box.addEventListener("mouseover", () => {
          box.classList.add("red");
          toggleColor(box, "red");
          updateStats();
      });

      
      box.addEventListener("click", () => {
        box.classList.remove("red");
        box.classList.add("clicked");
        toggleColor(box, "blue");

        updateStats();
      });
    }
  }

  // Initial callbacks sur carrés existants
  addCallbacksToSquares();
  updateStats();
});
  

  


/**
 * Cleans up the document so that the exercise is easier.
 *
 * There are some text and comment nodes that are in the initial DOM, it's nice
 * to clean them up beforehand.
 */
function initialCleanup() {
  const nodesToRemove = [];
  document.getElementById("grid").childNodes.forEach((node, key) => {
    if (node.nodeType !== Node.ELEMENT_NODE) {
      nodesToRemove.push(node);
    }
  });
  for (const node of nodesToRemove) {
    node.remove();
  }
}



