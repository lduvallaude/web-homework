// using vite, we can write our code with URLs that simply read
// /api/v2/xxx
// and vite will proxy them to whichever server is configured in vite.config.js,
// which is currently set to https://pixels-war.fly.dev
// so there's essentially no need for a global variable with the server URL..

// also note that it's probably wise to start with the TEST map

document.addEventListener("DOMContentLoaded",
    async () => {

        let MAP_ID = "TEST"
        let API_KEY = undefined

        // dimensions courantes de la carte
        let CURRENT_NI = 0
        let CURRENT_NJ = 0

        // intervalle d'auto-refresh
        let refreshInterval = null

        // récupération de la liste des cartes
        console.log("Retrieving maps from the server...")
        const maps_response = await fetch(`/api/v2/maps`, { credentials: "include" })
        const maps_json = await maps_response.json()

        if (!maps_response.ok) {
            alert(`Error retrieving maps: ${maps_response.status} ${maps_response.statusText}`)
            return
        }

        const select = document.getElementById("mapid-input")
        for (const { name, timeout } of maps_json) {
            const option = document.createElement("option")
            option.value = name
            const seconds = timeout / 1000000000
            option.textContent = `${name} (${seconds}s)`
            select.appendChild(option)
            console.log(`Map ${name} added to the dropdown`)
        }

        // connect
        async function connect(event) {
            // 1. récupère la carte choisie dans le dropdown
            MAP_ID = document.getElementById("mapid-input").value
            console.log(`Connecting to map ${MAP_ID}...`)

            // 2. envoie /init pour cette carte
            const init_response = await fetch(`/api/v2/maps/${MAP_ID}/init`, {
                method: "GET",
                credentials: "include",
            })

            if (!init_response.ok) {
                alert(`Error initializing map: ${init_response.status} ${init_response.statusText}`)
                return
            }

            const init_json = await init_response.json()
            console.log("Init response:", init_json)

            // 3. récupère les dimensions et les pixels
            const { ni, nj, data, api_key } = init_json

            // 4. stocke la clé API et les dimensions
            API_KEY = api_key
            CURRENT_NI = ni
            CURRENT_NJ = nj
            console.log(`Map ${MAP_ID}: ${ni} rows x ${nj} cols — API key: ${API_KEY}`)

            // 5. dessine la carte
            draw_map(ni, nj, data)

            // 6. (re)lance l'auto-refresh toutes les 2 secondes
            if (refreshInterval) clearInterval(refreshInterval)
            refreshInterval = setInterval(() => refresh(), 2000)
        }

        // attache connect au bouton Connect
        document.getElementById("connect-btn").addEventListener("click", connect)

        // draw_map
        function draw_map(ni, nj, data) {
            const grid = document.getElementById("grid")

            // nettoie l'ancienne carte
            grid.innerHTML = ""

            // définit le nombre de colonnes CSS
            grid.style.gridTemplateColumns = `repeat(${nj}, 1fr)`

            // crée un div par pixel
            for (let i = 0; i < ni; i++) {
                for (let j = 0; j < nj; j++) {
                    const [r, g, b] = data[i][j]
                    const div = document.createElement("div")
                    div.classList.add("pixel")
                    div.style.backgroundColor = `rgb(${r}, ${g}, ${b})`
                    // stocke les coordonnées dans les attributs data-
                    div.dataset.i = i
                    div.dataset.j = j
                    // clic → colorier le pixel
                    div.addEventListener("click", () => set_pixel(div, i, j))
                    // survol → affiche les coordonnées
                    div.addEventListener("mouseenter", () => show_coords(i, j))
                    grid.appendChild(div)
                }
            }
        }

        //TMP: to test the previous function: 3 lines and 5 columns
        draw_map(3, 5, [
            [ [255, 0, 0], [255, 255, 0], [255, 0, 0], [255, 255, 0], [255, 0, 0] ],
            [ [255, 255, 0], [255, 0, 0], [255, 255, 0], [255, 0, 0], [255, 255, 0] ],
            [ [255, 0, 0], [255, 255, 0], [255, 0, 0], [255, 255, 0], [255, 0, 0] ],
        ])

        // apply_changes 
        function apply_changes(ni, nj, changes) {
            const grid = document.getElementById("grid")
            for (const [i, j, r, g, b] of changes) {
                // l'index dans la grille : ligne i × nb colonnes + colonne j
                const index = i * nj + j
                const div = grid.children[index]
                if (div) {
                    div.style.backgroundColor = `rgb(${r}, ${g}, ${b})`
                }
            }
        }

        //TMP: to test the previous function, let's change the color of 3 pixels
        apply_changes(3, 5, [
            [1, 1, 0, 0, 255],
            [1, 2, 0, 0, 255],
            [1, 3, 0, 0, 255],
        ])

        // refresh 
        async function refresh() {
            if (!MAP_ID) return

            const response = await fetch(`/api/v2/maps/${MAP_ID}/changes`, {
                method: "GET",
                credentials: "include",
            })

            if (!response.ok) {
                console.warn(`Refresh error: ${response.status} ${response.statusText}`)
                return
            }

            const { changes } = await response.json()
            if (changes && changes.length > 0) {
                apply_changes(CURRENT_NI, CURRENT_NJ, changes)
            }
        }

        // attache refresh au bouton Refresh (si présent dans le HTML)
        const refreshBtn = document.getElementById("refresh-btn")
        if (refreshBtn) {
            refreshBtn.addEventListener("click", () => refresh())
        }

        // set_pixel
        async function set_pixel(div, i, j) {
            if (!API_KEY) {
                alert("Connecte-toi d'abord à une carte !")
                return
            }

            const [r, g, b] = getPickedColorInRGB()

            const response = await fetch(`/api/v2/maps/${MAP_ID}/pixel`, {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json",
                    "API-KEY": API_KEY,
                },
                body: JSON.stringify({ i, j, r, g, b }),
            })

            if (!response.ok) {
                const err = await response.json().catch(() => ({}))
                console.warn(`set_pixel error: ${response.status}`, err)
                // si c'est un timeout, on pourrait afficher un message
                if (response.status === 429) {
                    console.log("Timeout pas encore écoulé, patiente un peu !")
                }
                return
            }

            // mise à jour locale immédiate (pas besoin d'attendre le prochain refresh)
            div.style.backgroundColor = `rgb(${r}, ${g}, ${b})`

            // refresh immédiat pour voir les autres changements aussi
            await refresh()
        }

        // coordonnées au survol
        function show_coords(i, j) {
            const coordsEl = document.getElementById("coords")
            if (coordsEl) coordsEl.textContent = `(${i}, ${j})`
        }

        // no need to change anything below
        // just little helper functions for your convenience

        // retrieve RGB color from the color picker
        function getPickedColorInRGB() {
            const colorHexa = document.getElementById("colorpicker").value

            const r = parseInt(colorHexa.substring(1, 3), 16)
            const g = parseInt(colorHexa.substring(3, 5), 16)
            const b = parseInt(colorHexa.substring(5, 7), 16)

            return [r, g, b]
        }

        // in the other direction, to put the color of a pixel in the color picker
        // (the color picker insists on having a color in hexadecimal...)
        function pickColorFrom(div) {
            const bg = window.getComputedStyle(div).backgroundColor
            const [r, g, b] = bg.match(/\d+/g)
            const rh = parseInt(r).toString(16).padStart(2, '0')
            const gh = parseInt(g).toString(16).padStart(2, '0')
            const bh = parseInt(b).toString(16).padStart(2, '0')
            const hex = `#${rh}${gh}${bh}`
            document.getElementById("colorpicker").value = hex
        }
    }
)