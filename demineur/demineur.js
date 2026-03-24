const grid = document.getElementById("grid");
const GRID_SIZE = 10;
const NUM_BOMBS = 10;
let squares = [];

function createGrid() {
    grid.innerHTML = ""; // permet de vider la grille avant de la recréer
    squares = [];
    for (let row = 0; row < GRID_SIZE; row++) {
        for (let col = 0; col < GRID_SIZE; col++) {
            const box = document.createElement("div");
            box.dataset.row = row;
            box.dataset.column = col;
            grid.appendChild(box);
            squares.push(box);
        }
    }
}

function placeBombs() {
    let bombsPlaced = 0;
    while (bombsPlaced < NUM_BOMBS) {
        const index = Math.floor(Math.random() * squares.length); // Math.floor arrondit à l'entier inférieur
        const box = squares[index];
        if (!box.classList.contains("bomb")) {
            box.classList.add("bomb");
            bombsPlaced++;
        }
    }
}

function revealNeighbours(box) {
    const row = +box.dataset.row;
    const col = Number(box.dataset.column); // Number() (ou +) convertit la chaîne en nombre

    if (box.classList.contains("revealed")) return;

    box.classList.add("revealed");

    if (box.classList.contains("bomb")) {
        box.textContent = "💣";
        alert("Game over!");
        return;
    }

    let bombs = 0;

    for (let i = row - 1; i <= row + 1; i++) {
        for (let j = col - 1; j <= col + 1; j++) {
            if (i >= 0 && i < GRID_SIZE && j >= 0 && j < GRID_SIZE) { // on s'assure de ne pas sortir des limites de la grille
                if (i === row && j === col) continue;
                const index = i * GRID_SIZE + j;
                const neighbourBox = squares[index];
                if (neighbourBox.classList.contains("bomb")) bombs++;
            }
        }
    }

    if (bombs > 0) {
        box.textContent = bombs;
    } else {
        // Si aucune bombe autour, on révèle automatiquement les voisins
        for (let i = row - 1; i <= row + 1; i++) {
            for (let j = col - 1; j <= col + 1; j++) {
                if (i >= 0 && i < GRID_SIZE && j >= 0 && j < GRID_SIZE) {
                    const index = i * GRID_SIZE + j;
                    const neighbourBox = squares[index];
                    if (!neighbourBox.classList.contains("revealed")) {
                        revealNeighbours(neighbourBox);
                    }
                }
            }
        }
    }
}

function addCallbacksToSquares() {
    for (const box of squares) {
        box.addEventListener("click", () => {
            revealNeighbours(box);
            checkWin();
        });
    }
}

function checkWin() {
    let revealedCount = 0;
    for (const box of squares) {
        if (box.classList.contains("revealed") && !box.classList.contains("bomb")) {
            revealedCount++;
        }
    }

    if (revealedCount === GRID_SIZE * GRID_SIZE - NUM_BOMBS) {
        alert("Félicitations, vous avez gagné !");
        revealAllBombs();
    }
}

function revealAllBombs() {
    for (const box of squares) {
        if (box.classList.contains("bomb")) {
            box.classList.add("revealed");
            box.textContent = "💣";
        }
    }
}

function resetGame() {
    createGrid();
    placeBombs();
    addCallbacksToSquares();
}

document.getElementById("btn-reset").addEventListener("click", resetGame);

resetGame();