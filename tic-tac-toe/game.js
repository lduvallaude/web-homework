let player = "cross";

const grid = document.getElementById("grid");

function addCallbacksToSquares() {
    for (const box of grid.querySelectorAll("div")) {
      
      box.addEventListener("click", () => {
        if (!(box.classList.contains("cross") || box.classList.contains("circle"))) {
            box.classList.add(player);
            if (!checkWin(player)) {
            updateplayer();   
            }
        else {
            if (!checkWin(player)) {
            alert("This square is already occupied!");  
            } 
        }
    }
      });
    };
};

function updateplayer() {
  if (player === "cross") {
    player = "circle";
  } else {
    player = "cross";
  }
}

function resetGame() {
    const resetBtn = document.getElementById("btn-reset");
    resetBtn.addEventListener("click", () => {
        for (const box of grid.querySelectorAll("div")) {
            box.classList.remove("cross");
            box.classList.remove("circle");
        }
        player = "cross";
    });
}

function checkWin(player) {
    const squares = grid.querySelectorAll("div");
    const winningCombinations = [
        [0, 1, 2], // Row 1
        [3, 4, 5], // Row 2
        [6, 7, 8], // Row 3
        [0, 3, 6], // Column 1
        [1, 4, 7], // Column 2
        [2, 5, 8], // Column 3
        [0, 4, 8], // Diagonal top-left to bottom-right
        [2, 4, 6]  // Diagonal top-right to bottom-left
    ];

    for (const combination of winningCombinations) {
        const [a, b, c] = combination;
        if (squares[a].classList.contains(player) &&
            squares[b].classList.contains(player) &&
            squares[c].classList.contains(player)) {
            alert(`${player} wins!`);
            return true;
        }

    }
    return false;
}

addCallbacksToSquares();
resetGame();


