<script setup>
import { ref, onMounted } from 'vue'
import { usePyodide, pyodideStatus } from './composables/usePyodide'
import { adjustNetwork } from './services/adjustment'
import PointsTable from './components/PointsTable.vue'
import ObservationsTable from './components/ObservationsTable.vue'
import NetworkPlot from './components/NetworkPlot.vue'

const result = ref(null)
const error = ref(null)
const ellipseScale = ref(2000)   // Überhöhungsfaktor für die Ellipsen-Darstellung

// Netz reaktiv – wird von den Tabellen live bearbeitet
const network = ref({
  name: 'Einfaches Dreieck',
  settings: { include_scale: false },
  points: [
    { id: 'A', x: 0,   y: 0,  z: 0, fixed_x: true, fixed_y: true, fixed_z: true },
    { id: 'B', x: 100, y: 0,  z: 0, fixed_x: true, fixed_y: true, fixed_z: true },
    { id: 'N', x: 50,  y: 80, z: 0, fixed_z: true },
  ],
  observations: [
    { id: 'd1', type: 'distance', station: 'A', target: 'N', value: 94.34, std_dev: 0.002, enabled: true },
    { id: 'd2', type: 'distance', station: 'B', target: 'N', value: 94.34, std_dev: 0.002, enabled: true },
    { id: 'd3', type: 'distance', station: 'A', target: 'B', value: 100.0, std_dev: 0.002, enabled: true },
  ],
})

// Rechenkern beim Start vorwärmen
onMounted(() => { usePyodide() })

async function runAdjustment() {
  error.value = null
  result.value = null
  try {
    const res = await adjustNetwork(network.value)
    if (!res.converged) {
      error.value =
        'Die Ausgleichung ist nicht konvergiert. ' +
        'Mögliche Ursache: Ein Neupunkt ist durch zu wenige Beobachtungen ' +
        'nicht bestimmbar (unterbestimmtes/singuläres System). ' +
        'Prüfe, ob jeder nicht-fixierte Punkt genügend Beobachtungen hat.'
      return
    }
    result.value = res
  } catch (e) {
    error.value = String(e)
  }
}

// Testnetz mit realistisch verrauschten Beobachtungen (sigma_0 ~ 1)
function loadNoisyTestNetwork() {
  result.value = null
  error.value = null

  const sigma = 0.003  // 3 mm Streckengenauigkeit
  // Wahre Geometrie: N mittig oben
  const trueDist = {
    'A-N': Math.hypot(50 - 0, 80 - 0),      // A(0,0)   -> N(50,80)
    'B-N': Math.hypot(50 - 100, 80 - 0),    // B(100,0) -> N(50,80)
    'A-B': 100.0,
  }
  // Gauß-Rauschen (Box-Muller)
  const noise = (s) => {
    const u1 = Math.random(), u2 = Math.random()
    return s * Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2)
  }

  network.value = {
    name: 'Verrauschtes Dreieck',
    settings: { include_scale: false },
    points: [
      { id: 'A', x: 0,   y: 0,  z: 0, fixed_x: true, fixed_y: true, fixed_z: true },
      { id: 'B', x: 100, y: 0,  z: 0, fixed_x: true, fixed_y: true, fixed_z: true },
      { id: 'N', x: 48,  y: 78, z: 0, fixed_z: true },  // leicht schiefe Näherung
    ],
    observations: [
      { id: 'd1', type: 'distance', station: 'A', target: 'N',
        value: +(trueDist['A-N'] + noise(sigma)).toFixed(4), std_dev: sigma, enabled: true },
      { id: 'd2', type: 'distance', station: 'B', target: 'N',
        value: +(trueDist['B-N'] + noise(sigma)).toFixed(4), std_dev: sigma, enabled: true },
      { id: 'd3', type: 'distance', station: 'A', target: 'B',
        value: +(trueDist['A-B'] + noise(sigma)).toFixed(4), std_dev: sigma, enabled: true },
    ],
  }
}
</script>

<template>
  <main>
    <h1>OpenAdjust</h1>
    <p>Rechenkern: <b :class="pyodideStatus">{{ pyodideStatus }}</b></p>

    <PointsTable v-model="network.points" />
    <ObservationsTable v-model="network.observations" :points="network.points" />

    <p>
      <button @click="loadNoisyTestNetwork">Verrauschtes Testnetz laden</button>
    </p>

    <label class="slider">
      Ellipsen-Überhöhung: {{ ellipseScale }}×
      <input type="range" min="100" max="10000" step="100" v-model.number="ellipseScale" />
    </label>

    <p>
      <button :disabled="pyodideStatus !== 'ready'" @click="runAdjustment">
        Netz ausgleichen
      </button>
    </p>

    <p v-if="error" class="error">Fehler: {{ error }}</p>

    <NetworkPlot
      :points="network.points"
      :observations="network.observations"
      :result="result"
      :ellipse-scale="ellipseScale"
    />

    <section v-if="result" class="result">
      <h3>Ergebnis „{{ network.name }}"</h3>
      <ul>
        <li>Konvergiert: <b>{{ result.converged }}</b> ({{ result.iterations }} Iterationen)</li>
        <li>σ₀ (a posteriori): <b>{{ result.sigma_0.toExponential(3) }}</b></li>
        <li>Redundanz: <b>{{ result.redundancy }}</b></li>
        <li v-for="(coord, pid) in result.adjusted_coords" :key="pid">
          {{ pid }}: <b>x = {{ coord[0].toFixed(4) }}, y = {{ coord[1].toFixed(4) }}</b>
        </li>
        <li>Globaler Modelltest: <b>{{ result.test.passed ? 'bestanden' : 'nicht bestanden' }}</b></li>
      </ul>
    </section>
  </main>
</template>

<style>
main { font-family: system-ui, sans-serif; max-width: 800px; margin: 3rem auto; padding: 0 1rem; }
button { padding: .5rem 1rem; font-size: 1rem; cursor: pointer; margin-top: .5rem; }
button:disabled { cursor: not-allowed; opacity: .5; }
.slider { display: block; margin: .5rem 0; font-size: .9rem; }
.slider input { vertical-align: middle; width: 260px; margin-left: .5rem; }
.error { color: #b02a37; }
.result { margin-top: 1.5rem; }
.loading { color: #b8860b; }
.ready { color: #157347; }
</style>
