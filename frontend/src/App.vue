<script setup>
import { ref, onMounted, computed } from 'vue'
import { usePyodide, pyodideStatus } from './composables/usePyodide'
import { adjustNetwork } from './services/adjustment'
import PointsTable from './components/PointsTable.vue'
import ObservationsTable from './components/ObservationsTable.vue'
import NetworkPlot from './components/NetworkPlot.vue'
import ResultTable from './components/ResultTable.vue'
import ResidualsTable from './components/ResidualsTable.vue'

const result = ref(null)
const error = ref(null)
const ellipseScale = ref(2000)

// --- Beispiel-Katalog (erweiterbar) -----------------------------------------
const EXAMPLES = [
  { id: 'triangle',       label: '1a) Streckennetz – Dreieck (exakt)' },
  { id: 'triangle_noisy', label: '1b) Streckennetz – Dreieck (verrauscht)' },
  { id: 'dir_small', label: '2) Strecken-/Richtungsnetz – klein (r=2)' },
  { id: 'dir_small_noisy', label: '2b) Strecken-/Richtungsnetz – klein (verrauscht)' },

  // später: '2) Strecken-/Richtungsnetz', '3) Tunnelnetz'
]
const selectedExample = ref('triangle')


// true, wenn ein Beispiel mit Zufallsrauschen aktiv ist
const isNoisy = computed(() => selectedExample.value === 'triangle_noisy' ||
  selectedExample.value === 'dir_small_noisy')

// Neues Messrauschen ziehen (wahres Netz bleibt, nur Messung neu simuliert)
function resimulate() {
  const factory = FACTORIES[selectedExample.value]
  if (!factory) return
  network.value = factory()   // Factory würfelt intern neu
  result.value = null         // altes Ergebnis verwerfen -> zum Neu-Rechnen anregen
  error.value = null
}

function makeDirectionNetwork() {
  // Wahres Netz: A(0,0), B(100,0), N(50,60)
  const A = [0, 0], B = [100, 0], N = [50, 60]
  // Richtungswinkel im Uhrzeigersinn (Nord=X=0, Ost=Y): bearing = atan2(dy, dx)
  const bearingGon = (fr, to) => {
    let b = Math.atan2(to[1] - fr[1], to[0] - fr[0]) * 200 / Math.PI
    return (b + 400) % 400
  }
  const dist = (fr, to) => Math.hypot(to[0] - fr[0], to[1] - fr[1])

  // Willkürliche wahre Orientierungen der Standpunkte (gon)
  const oA = 30, oB = 250
  // gemessene Richtung r = Azimut - o (mod 400)
  const r = (fr, to, o) => (bearingGon(fr, to) - o + 400) % 400

  const sDir = 0.001   // ~10 mgon in gon-Einheit? -> siehe Hinweis unten
  const sDist = 0.003

  return {
    name: 'Strecken-/Richtungsnetz (klein)',
    settings: { include_scale: false },
    points: [
      { id: 'A', x: 0,   y: 0,  z: 0, fixed_x: true, fixed_y: true, fixed_z: true },
      { id: 'B', x: 100, y: 0,  z: 0, fixed_x: true, fixed_y: true, fixed_z: true },
      { id: 'N', x: 48,  y: 58, z: 0, fixed_z: true },   // Näherung leicht daneben
    ],
    observations: [
      // Richtungen (gon) – teilen sich je Standpunkt EINE Orientierung
      { id: 'rA_B', type: 'direction', station: 'A', target: 'B', value: +r(A,B,oA).toFixed(4), std_dev: 0.0010, enabled: true },
      { id: 'rA_N', type: 'direction', station: 'A', target: 'N', value: +r(A,N,oA).toFixed(4), std_dev: 0.0010, enabled: true },
      { id: 'rB_A', type: 'direction', station: 'B', target: 'A', value: +r(B,A,oB).toFixed(4), std_dev: 0.0010, enabled: true },
      { id: 'rB_N', type: 'direction', station: 'B', target: 'N', value: +r(B,N,oB).toFixed(4), std_dev: 0.0010, enabled: true },
      // Strecken (m)
      { id: 'dA_N', type: 'distance', station: 'A', target: 'N', value: +dist(A,N).toFixed(4), std_dev: sDist, enabled: true },
      { id: 'dB_N', type: 'distance', station: 'B', target: 'N', value: +dist(B,N).toFixed(4), std_dev: sDist, enabled: true },
    ],
  }
}


function makeTriangle() {
  return {
    name: 'Streckennetz (Dreieck)',
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
  }
}

function makeNoisyTriangle() {
  const sigma = 0.003
  const trueDist = {
    'A-N': Math.hypot(50 - 0, 80 - 0),
    'B-N': Math.hypot(50 - 100, 80 - 0),
    'A-B': 100.0,
  }
  const noise = (s) => {
    const u1 = Math.random(), u2 = Math.random()
    return s * Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2)
  }
  return {
    name: 'Streckennetz (verrauscht)',
    settings: { include_scale: false },
    points: [
      { id: 'A', x: 0,   y: 0,  z: 0, fixed_x: true, fixed_y: true, fixed_z: true },
      { id: 'B', x: 100, y: 0,  z: 0, fixed_x: true, fixed_y: true, fixed_z: true },
      { id: 'N', x: 48,  y: 78, z: 0, fixed_z: true },
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

function makeNoisyDirectionNetwork() {
  const A = [0, 0], B = [100, 0], N = [50, 60]
  const bearingGon = (fr, to) => {
    let b = Math.atan2(to[1] - fr[1], to[0] - fr[0]) * 200 / Math.PI
    return (b + 400) % 400
  }
  const dist = (fr, to) => Math.hypot(to[0] - fr[0], to[1] - fr[1])
  const oA = 30, oB = 250
  const r = (fr, to, o) => (bearingGon(fr, to) - o + 400) % 400

  // Box-Muller: eine N(0, s)-Zufallszahl
  const noise = (s) => {
    const u1 = Math.random(), u2 = Math.random()
    return s * Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2)
  }

  const sDir  = 0.001   // 1 mgon (Richtungs-σ)
  const sDist = 0.003   // 3 mm  (Strecken-σ)

  return {
    name: 'Strecken-/Richtungsnetz (verrauscht)',
    settings: { include_scale: false },
    points: [
      { id: 'A', x: 0,   y: 0,  z: 0, fixed_x: true, fixed_y: true, fixed_z: true },
      { id: 'B', x: 100, y: 0,  z: 0, fixed_x: true, fixed_y: true, fixed_z: true },
      { id: 'N', x: 48,  y: 58, z: 0, fixed_z: true },
    ],
    observations: [
      { id: 'rA_B', type: 'direction', station: 'A', target: 'B',
        value: +((r(A,B,oA) + noise(sDir) + 400) % 400).toFixed(4), std_dev: sDir, enabled: true },
      { id: 'rA_N', type: 'direction', station: 'A', target: 'N',
        value: +((r(A,N,oA) + noise(sDir) + 400) % 400).toFixed(4), std_dev: sDir, enabled: true },
      { id: 'rB_A', type: 'direction', station: 'B', target: 'A',
        value: +((r(B,A,oB) + noise(sDir) + 400) % 400).toFixed(4), std_dev: sDir, enabled: true },
      { id: 'rB_N', type: 'direction', station: 'B', target: 'N',
        value: +((r(B,N,oB) + noise(sDir) + 400) % 400).toFixed(4), std_dev: sDir, enabled: true },
      { id: 'dA_N', type: 'distance', station: 'A', target: 'N',
        value: +(dist(A,N) + noise(sDist)).toFixed(4), std_dev: sDist, enabled: true },
      { id: 'dB_N', type: 'distance', station: 'B', target: 'N',
        value: +(dist(B,N) + noise(sDist)).toFixed(4), std_dev: sDist, enabled: true },
    ],
  }
}


const FACTORIES = { triangle: makeTriangle, triangle_noisy: makeNoisyTriangle, dir_small: makeDirectionNetwork,  dir_small_noisy: makeNoisyDirectionNetwork }

// Startnetz
const network = ref(makeTriangle())

function loadExample() {
  result.value = null
  error.value = null
  const factory = FACTORIES[selectedExample.value]
  if (factory) network.value = factory()
}

// --- Rechenkern -------------------------------------------------------------
onMounted(() => { usePyodide() })

async function runAdjustment() {
  error.value = null
  result.value = null
  try {
    const res = await adjustNetwork(network.value)
    if (!res.converged) {
      error.value =
        'Die Ausgleichung ist nicht konvergiert. Mögliche Ursache: Ein Neupunkt ist ' +
        'durch zu wenige Beobachtungen nicht bestimmbar (unterbestimmtes System).'
      return
    }
    result.value = res
  } catch (e) {
    error.value = String(e)
  }
}
</script>

<template>
  <main>
    <h1>OpenAdjust</h1>
    <p>Rechenkern: <b :class="pyodideStatus">{{ pyodideStatus }}</b></p>

    <!-- Beispiel-Auswahl -->
    <div class="example-picker">
      <label>
        Beispiel:
        <select v-model="selectedExample">
          <option v-for="ex in EXAMPLES" :key="ex.id" :value="ex.id">{{ ex.label }}</option>
        </select>
      </label>
      <button @click="loadExample">Beispiel laden</button>
      <button
        v-if="isNoisy"
        class="dice"
        @click="resimulate"
        title="Zieht neues Messrauschen aus derselben Verteilung"
      >
        🎲 Neue Messung simulieren
      </button>
    </div>

    <PointsTable v-model="network.points" />
    <ObservationsTable v-model="network.observations" :points="network.points" />

    <!-- Aktionsleiste mit klarem Abstand -->
    <div class="action-bar">
      <button :disabled="pyodideStatus !== 'ready'" @click="runAdjustment">
        Netz ausgleichen
      </button>
    </div>

    <p v-if="error" class="error">Fehler: {{ error }}</p>

    <!-- Ergebnis-Banner: direkt nach dem Button -->
    <section v-if="result" class="status" :class="{ ok: result.test.passed, warn: !result.test.passed }">
      <span>{{ result.converged ? '✓ konvergiert' : '✗ nicht konvergiert' }} ({{ result.iterations }} Iter.)</span>
      <span>σ₀ = <b>{{ result.sigma_0.toFixed(3) }}</b></span>
      <span>Redundanz r = <b>{{ result.redundancy }}</b></span>
      <span>Globaltest: <b>{{ result.test.passed ? 'bestanden' : 'nicht bestanden' }}</b></span>
    </section>

    <NetworkPlot
      :points="network.points"
      :observations="network.observations"
      :result="result"
      :ellipse-scale="ellipseScale"
    />

    <!-- Ellipsen-Überhöhung: nach dem Plot, nur wenn Ergebnis da -->
    <label v-if="result" class="slider">
      Ellipsen-Überhöhung: {{ ellipseScale }}×
      <input type="range" min="100" max="10000" step="100" v-model.number="ellipseScale" />
    </label>

    <ResultTable :points="network.points" :result="result" />
    <ResidualsTable :observations="network.observations" :result="result" />
  </main>
</template>

<style>
main { font-family: system-ui, sans-serif; max-width: 800px; margin: 3rem auto; padding: 0 1rem; }
button { padding: .5rem 1rem; font-size: 1rem; cursor: pointer; }
button:disabled { cursor: not-allowed; opacity: .5; }
.example-picker { display: flex; align-items: center; gap: .8rem; flex-wrap: wrap; margin: 1rem 0; }
.example-picker select { padding: .3rem; font-size: .95rem; }
.example-picker .hint { color: #888; font-size: .8rem; }
.example-picker .dice { background: #eef4fb; border: 1px solid #1d6fbf; color: #1d6fbf; }
.action-bar { margin: 1.5rem 0 .5rem; }
.slider { display: block; margin: .5rem 0; font-size: .9rem; }
.slider input { vertical-align: middle; width: 260px; margin-left: .5rem; }
.error { color: #b02a37; }
.loading { color: #b8860b; }
.ready { color: #157347; }
.status {
  display: flex; flex-wrap: wrap; gap: 1.2rem;
  padding: .6rem 1rem; margin: 1rem 0; border-radius: 6px;
  font-size: .9rem; border: 1px solid;
}
.status.ok   { background: #eaf6ee; border-color: #157347; color: #0d4a2f; }
.status.warn { background: #fdeaec; border-color: #b02a37; color: #7a1c25; }
.status b { font-variant-numeric: tabular-nums; }
</style>
