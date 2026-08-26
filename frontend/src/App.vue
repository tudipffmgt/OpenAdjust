<script setup>
import { ref, onMounted } from 'vue'
import { usePyodide, pyodideStatus } from './composables/usePyodide'
import { adjustNetwork } from './services/adjustment'
import PointsTable from './components/PointsTable.vue'
import ObservationsTable from './components/ObservationsTable.vue'
import NetworkPlot from './components/NetworkPlot.vue'



const result = ref(null)
const error = ref(null)

// Netz reaktiv – wird von der Punkte-Tabelle live bearbeitet
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
</script>

<template>
  <main>
    <h1>OpenAdjust</h1>
    <p>Rechenkern: <b :class="pyodideStatus">{{ pyodideStatus }}</b></p>

    <PointsTable v-model="network.points" />
    <ObservationsTable v-model="network.observations" :points="network.points" />
    <NetworkPlot    :points="network.points"
                    :observations="network.observations"
                    :result="result" />

    <button :disabled="pyodideStatus !== 'ready'" @click="runAdjustment">
      Netz ausgleichen
    </button>

    <p v-if="error" class="error">Fehler: {{ error }}</p>

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
main { font-family: system-ui, sans-serif; max-width: 720px; margin: 3rem auto; padding: 0 1rem; }
button { padding: .5rem 1rem; font-size: 1rem; cursor: pointer; margin-top: .5rem; }
button:disabled { cursor: not-allowed; opacity: .5; }
.error { color: #b02a37; }
.result { margin-top: 1.5rem; }
.loading { color: #b8860b; }
.ready { color: #157347; }
</style>
