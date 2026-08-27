<script setup>
import { computed } from 'vue'

const props = defineProps({
  points: { type: Array, required: true },
  result: { type: Object, default: null },
})

const pointsById = computed(() => {
  const m = {}
  for (const p of props.points) m[p.id] = p
  return m
})

// Eine Zeile pro ausgeglichenem Punkt
const rows = computed(() => {
  if (!props.result?.adjusted_coords) return []
  const std = props.result.point_std || {}
  const ell = props.result.error_ellipses || {}
  const out = []
  for (const [id, c] of Object.entries(props.result.adjusted_coords)) {
    const approx = pointsById.value[id]
    const s = std[id]
    const e = ell[id]
    out.push({
      id,
      ax: approx?.x, ay: approx?.y,           // Näherung
      x: c[0], y: c[1],                        // ausgeglichen
      dx: approx ? (c[0] - approx.x) * 1000 : null,  // Δ in mm
      dy: approx ? (c[1] - approx.y) * 1000 : null,
      sx: s ? s.sx * 1000 : null,              // σ in mm
      sy: s ? s.sy * 1000 : null,
      a: e ? e.a * 1000 : null,                // Halbachsen in mm
      b: e ? e.b * 1000 : null,
      theta: e ? e.theta : null,               // gon
    })
  }
  return out
})

const f = (v, d = 4) => (v == null ? '–' : v.toFixed(d))
</script>

<template>
  <div v-if="rows.length" class="result-table">
    <h3>Ergebnis: Koordinaten &amp; Genauigkeit</h3>
    <table>
      <thead>
        <tr>
          <th rowspan="2">Punkt</th>
          <th colspan="2">Näherung [m]</th>
          <th colspan="2">Ausgeglichen [m]</th>
          <th colspan="2">Δ [mm]</th>
          <th colspan="2">σ [mm]</th>
          <th colspan="3">Fehlerellipse</th>
        </tr>
        <tr>
          <th>X</th><th>Y</th>
          <th>X</th><th>Y</th>
          <th>ΔX</th><th>ΔY</th>
          <th>σX</th><th>σY</th>
          <th>a [mm]</th><th>b [mm]</th><th>θ [gon]</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in rows" :key="r.id">
          <td class="id">{{ r.id }}</td>
          <td>{{ f(r.ax, 4) }}</td><td>{{ f(r.ay, 4) }}</td>
          <td class="adj">{{ f(r.x, 4) }}</td><td class="adj">{{ f(r.y, 4) }}</td>
          <td>{{ f(r.dx, 1) }}</td><td>{{ f(r.dy, 1) }}</td>
          <td>{{ f(r.sx, 2) }}</td><td>{{ f(r.sy, 2) }}</td>
          <td>{{ f(r.a, 2) }}</td><td>{{ f(r.b, 2) }}</td><td>{{ f(r.theta, 4) }}</td>
        </tr>
      </tbody>
    </table>
    <p class="hint">
      σ und Halbachsen sind mit σ₀ (a posteriori) skaliert. „–" = Festpunkt (keine Genauigkeitsangabe).
    </p>
  </div>
</template>

<style scoped>
.result-table { margin: 1.5rem 0; overflow-x: auto; }
table { border-collapse: collapse; font-size: .85rem; }
th, td { border: 1px solid #ccc; padding: .25rem .5rem; text-align: right; }
th { background: #f4f4f4; text-align: center; }
td.id { font-weight: bold; text-align: left; }
td.adj { color: #1d6fbf; font-weight: 600; }
.hint { color: #666; font-size: .8rem; margin-top: .3rem; }
</style>
