<script setup>
import { computed } from 'vue'

const props = defineProps({
  points: { type: Array, required: true },
  observations: { type: Array, default: () => [] },
  result: { type: Object, default: null },   // Ausgleichungsergebnis (optional)
})

const SIZE = 600
const PADDING = 55

// Schnellzugriff: ID -> Punkt
const pointsById = computed(() => {
  const map = {}
  for (const p of props.points) map[p.id] = p
  return map
})

// Bounding-Box: Näherungs- UND ausgeglichene Koordinaten einbeziehen
const bounds = computed(() => {
  const xs = [], ys = []
  for (const p of props.points) { xs.push(p.x); ys.push(p.y) }
  if (props.result?.adjusted_coords) {
    for (const c of Object.values(props.result.adjusted_coords)) {
      xs.push(c[0]); ys.push(c[1])
    }
  }
  if (xs.length === 0) return null
  return {
    minX: Math.min(...xs), maxX: Math.max(...xs),
    minY: Math.min(...ys), maxY: Math.max(...ys),
  }
})

const scale = computed(() => {
  const b = bounds.value
  if (!b) return 1
  const span = Math.max((b.maxX - b.minX) || 1, (b.maxY - b.minY) || 1)
  return (SIZE - 2 * PADDING) / span
})

// Weltkoordinate -> SVG-Pixel (Geodäsie: X=Nord oben, Y=Ost rechts)
function toSvg(x, y) {
  const b = bounds.value
  return {
    x: PADDING + (y - b.minY) * scale.value,
    y: SIZE - PADDING - (x - b.minX) * scale.value,
  }
}

const isFixed = (p) => p.fixed_x && p.fixed_y
const hasResult = computed(() => !!props.result?.adjusted_coords)

// Beste bekannte Position: ausgeglichen falls vorhanden, sonst Näherung
function bestPos(id) {
  const adj = props.result?.adjusted_coords?.[id]
  if (adj) return toSvg(adj[0], adj[1])
  const p = pointsById.value[id]
  return p ? toSvg(p.x, p.y) : null
}

// Linien-Bauer (nimmt eine Positions-Funktion)
function buildLines(posFn) {
  if (!bounds.value) return []
  const out = []
  for (const o of props.observations) {
    if (o.enabled === false) continue
    const a = posFn(o.station)
    const b = posFn(o.target)
    if (!a || !b) continue
    out.push({ x1: a.x, y1: a.y, x2: b.x, y2: b.y, id: o.id })
  }
  return out
}

// Näherungslinien (immer; blass, sobald ein Ergebnis vorliegt)
const approxLines = computed(() => buildLines(id => {
  const p = pointsById.value[id]
  return p ? toSvg(p.x, p.y) : null
}))

// Ausgeglichene Linien (nur nach Rechnung)
const adjustedLines = computed(() =>
  hasResult.value ? buildLines(bestPos) : []
)

// Näherungspunkte (aus der Tabelle)
const nodes = computed(() => {
  if (!bounds.value) return []
  return props.points.map(p => ({
    ...toSvg(p.x, p.y), id: p.id, fixed: isFixed(p),
  }))
})

// Ausgeglichene Punkte (mit Weltkoordinaten für Beschriftung)
const adjustedNodes = computed(() => {
  if (!bounds.value || !props.result?.adjusted_coords) return []
  const out = []
  for (const [id, c] of Object.entries(props.result.adjusted_coords)) {
    out.push({ ...toSvg(c[0], c[1]), id, wx: c[0], wy: c[1] })
  }
  return out
})
</script>

<template>
  <div class="plot">
    <h3>Netzplan</h3>
    <svg :width="SIZE" :height="SIZE" class="netzplan">
      <!-- Näherungslinien: kräftig ohne Ergebnis, blass mit Ergebnis -->
      <line
        v-for="l in approxLines" :key="'ap-' + l.id"
        :x1="l.x1" :y1="l.y1" :x2="l.x2" :y2="l.y2"
        stroke="#888" stroke-width="1.5"
        :opacity="hasResult ? 0.25 : 1"
      />

      <!-- Ausgeglichene Linien (nur nach Rechnung) -->
      <line
        v-for="l in adjustedLines" :key="'ad-' + l.id"
        :x1="l.x1" :y1="l.y1" :x2="l.x2" :y2="l.y2"
        stroke="#1d6fbf" stroke-width="1.8"
      />

      <!-- Näherungspunkte -->
      <g v-for="n in nodes" :key="n.id">
        <polygon
          v-if="n.fixed"
          :points="`${n.x},${n.y - 7} ${n.x - 6},${n.y + 5} ${n.x + 6},${n.y + 5}`"
          fill="#157347" stroke="#0d4a2f"
        />
        <circle
          v-else
          :cx="n.x" :cy="n.y" r="6"
          fill="none" stroke="#b02a37" stroke-width="1.5" stroke-dasharray="3 2"
        />
        <text :x="n.x + 9" :y="n.y - 6" font-size="12" fill="#222"
              class="label">{{ n.id }}</text>
        <text :x="n.x + 9" :y="n.y + 8" font-size="9" fill="#888"
              class="label">
          {{ pointsById[n.id].x.toFixed(1) }} / {{ pointsById[n.id].y.toFixed(1) }}
        </text>
      </g>

      <!-- Ausgeglichene Punkte + Beschriftung -->
      <g v-for="a in adjustedNodes" :key="'adj-' + a.id">
        <circle :cx="a.x" :cy="a.y" r="4.5" fill="#1d6fbf" opacity="0.9" />
        <text :x="a.x + 9" :y="a.y + 20" font-size="9" fill="#1d6fbf"
              class="label">
          {{ a.wx.toFixed(1) }} / {{ a.wy.toFixed(1) }}
        </text>
      </g>

      <!-- Koordinatenkreuz unten links (N = Nord/X oben, O = Ost/Y rechts) -->
      <g class="axes" transform="translate(28, 575)">
        <line x1="0" y1="0" x2="0" y2="-28" stroke="#333" stroke-width="1.5"
              marker-end="url(#arrow)" />
        <text x="-3" y="-32" font-size="11" fill="#333">N (X)</text>
        <line x1="0" y1="0" x2="28" y2="0" stroke="#333" stroke-width="1.5"
              marker-end="url(#arrow)" />
        <text x="30" y="4" font-size="11" fill="#333">O (Y)</text>
      </g>

      <defs>
        <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3"
                orient="auto" markerUnits="strokeWidth">
          <path d="M0,0 L6,3 L0,6 Z" fill="#333" />
        </marker>
      </defs>
    </svg>

    <p class="legend">
      <span class="fix">▲</span> Festpunkt &nbsp;
      <span class="new">◌</span> Neupunkt (Näherung) &nbsp;
      <span class="adj">●</span> ausgeglichen
    </p>
  </div>
</template>

<style scoped>
.plot { margin: 1rem 0; }
.netzplan { border: 1px solid #ddd; background: #fafafa; }
.legend { font-size: .85rem; color: #444; }
.legend .fix { color: #157347; }
.legend .new { color: #b02a37; }
.legend .adj { color: #1d6fbf; }
/* Text-Kontur, damit Labels über Linien lesbar bleiben */
.label {
  paint-order: stroke;
  stroke: #fafafa;
  stroke-width: 2.5px;
  stroke-linejoin: round;
}
</style>
