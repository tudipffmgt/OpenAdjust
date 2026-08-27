<script setup>
import { computed } from 'vue'

const props = defineProps({
  points: { type: Array, required: true },
  observations: { type: Array, default: () => [] },
  result: { type: Object, default: null },
  ellipseScale: { type: Number, default: 2000 },
})

const SIZE = 600
const PADDING = 55

const pointsById = computed(() => {
  const map = {}
  for (const p of props.points) map[p.id] = p
  return map
})

// Bounding-Box: Näherungs- UND ausgeglichene Koordinaten
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

function bestPos(id) {
  const adj = props.result?.adjusted_coords?.[id]
  if (adj) return toSvg(adj[0], adj[1])
  const p = pointsById.value[id]
  return p ? toSvg(p.x, p.y) : null
}

function buildConnections(posFn) {
  if (!bounds.value) return []
  const map = new Map()
  for (const o of props.observations) {
    if (o.enabled === false) continue
    const [p, q] = [o.station, o.target].slice().sort()
    const key = p + '|' + q
    let c = map.get(key)
    if (!c) { c = { key, p, q, hasDist: false, dirPQ: false, dirQP: false }; map.set(key, c) }
    if (o.type === 'distance') c.hasDist = true
    if (o.type === 'direction') {
      if (o.station === p) c.dirPQ = true
      else c.dirQP = true
    }
  }
  const out = []
  for (const c of map.values()) {
    const a = posFn(c.p), b = posFn(c.q)
    if (!a || !b) continue
    out.push({
      ...c,
      hasDir: c.dirPQ || c.dirQP,
      reciprocalDir: c.dirPQ && c.dirQP,
      x1: a.x, y1: a.y, x2: b.x, y2: b.y,
      mx: (a.x + b.x) / 2, my: (a.y + b.y) / 2,               // Mitte (einseitig)
      t1x: a.x + (b.x - a.x) / 3,     t1y: a.y + (b.y - a.y) / 3,      // 1/3
      t2x: a.x + (b.x - a.x) * 2 / 3, t2y: a.y + (b.y - a.y) * 2 / 3,  // 2/3
    })
  }
  return out
}


const approxConns = computed(() => buildConnections(id => {
  const p = pointsById.value[id]
  return p ? toSvg(p.x, p.y) : null
}))

const adjustedConns = computed(() =>
  hasResult.value ? buildConnections(bestPos) : []
)


const nodes = computed(() => {
  if (!bounds.value) return []
  return props.points.map(p => ({
    ...toSvg(p.x, p.y), id: p.id, fixed: isFixed(p),
  }))
})

const adjustedNodes = computed(() => {
  if (!bounds.value || !props.result?.adjusted_coords) return []
  const out = []
  for (const [id, c] of Object.entries(props.result.adjusted_coords)) {
    out.push({ ...toSvg(c[0], c[1]), id, wx: c[0], wy: c[1] })
  }
  return out
})

// Fehlerellipsen aus den Halbachsen-Vektoren des Kerns
const ellipses = computed(() => {
  const src = props.result?.error_ellipses
  if (!bounds.value || !src) return []
  const out = []
  for (const [id, e] of Object.entries(src)) {
    const adj = props.result.adjusted_coords[id]
    if (!adj) continue
    const center = toSvg(adj[0], adj[1])
    const k = props.ellipseScale

    // Halbachsen-Endpunkte in Weltkoords -> überhöht -> in Pixel
    const majEnd = toSvg(adj[0] + e.major_vec[0] * k, adj[1] + e.major_vec[1] * k)
    const minEnd = toSvg(adj[0] + e.minor_vec[0] * k, adj[1] + e.minor_vec[1] * k)

    const rMaj = Math.hypot(majEnd.x - center.x, majEnd.y - center.y)
    const rMin = Math.hypot(minEnd.x - center.x, minEnd.y - center.y)
    const angleDeg = Math.atan2(majEnd.y - center.y, majEnd.x - center.x) * 180 / Math.PI

    out.push({ id, cx: center.x, cy: center.y, rx: rMaj, ry: rMin, angle: angleDeg })
  }
  return out
})
</script>

<template>
  <div class="plot">
    <h3>Netzplan</h3>
    <svg :width="SIZE" :height="SIZE" class="netzplan">
       <!-- Näherungslinien: Pelzer-Signaturen -->
      <template v-for="l in approxConns" :key="'ap-' + l.key">
        <line v-if="l.hasDist && !l.hasDir"
          :x1="l.x1" :y1="l.y1" :x2="l.x2" :y2="l.y2"
          stroke="#888" stroke-width="1.5" :opacity="hasResult ? 0.25 : 1" />
        <line v-else-if="l.hasDir && !l.hasDist"
          :x1="l.x1" :y1="l.y1" :x2="l.x2" :y2="l.y2"
          stroke="#888" stroke-width="1.5" stroke-dasharray="8 5" :opacity="hasResult ? 0.25 : 1" />
        <template v-else-if="l.reciprocalDir">
          <line :x1="l.x1" :y1="l.y1" :x2="l.t1x" :y2="l.t1y"
            stroke="#888" stroke-width="1.5" :opacity="hasResult ? 0.25 : 1" />
          <line :x1="l.t1x" :y1="l.t1y" :x2="l.t2x" :y2="l.t2y"
            stroke="#888" stroke-width="1.5" stroke-dasharray="8 5" :opacity="hasResult ? 0.25 : 1" />
          <line :x1="l.t2x" :y1="l.t2y" :x2="l.x2" :y2="l.y2"
            stroke="#888" stroke-width="1.5" :opacity="hasResult ? 0.25 : 1" />
        </template>
        <template v-else>
          <line :x1="l.x1" :y1="l.y1" :x2="l.mx" :y2="l.my"
            stroke="#888" stroke-width="1.5" :opacity="hasResult ? 0.25 : 1" />
          <line :x1="l.mx" :y1="l.my" :x2="l.x2" :y2="l.y2"
            stroke="#888" stroke-width="1.5" stroke-dasharray="8 5" :opacity="hasResult ? 0.25 : 1" />
        </template>
      </template>


      <!-- Ausgeglichene Linien: Pelzer-Signaturen -->
      <template v-for="l in adjustedConns" :key="'ad-' + l.key">
        <line v-if="l.hasDist && !l.hasDir"
          :x1="l.x1" :y1="l.y1" :x2="l.x2" :y2="l.y2"
          stroke="#1d6fbf" stroke-width="1.8" />
        <line v-else-if="l.hasDir && !l.hasDist"
          :x1="l.x1" :y1="l.y1" :x2="l.x2" :y2="l.y2"
          stroke="#1d6fbf" stroke-width="1.6" stroke-dasharray="8 5" />
        <template v-else-if="l.reciprocalDir">
          <line :x1="l.x1" :y1="l.y1" :x2="l.t1x" :y2="l.t1y" stroke="#1d6fbf" stroke-width="1.8" />
          <line :x1="l.t1x" :y1="l.t1y" :x2="l.t2x" :y2="l.t2y" stroke="#1d6fbf" stroke-width="1.6" stroke-dasharray="8 5" />
          <line :x1="l.t2x" :y1="l.t2y" :x2="l.x2" :y2="l.y2" stroke="#1d6fbf" stroke-width="1.8" />
        </template>
        <template v-else>
          <line :x1="l.x1" :y1="l.y1" :x2="l.mx" :y2="l.my" stroke="#1d6fbf" stroke-width="1.8" />
          <line :x1="l.mx" :y1="l.my" :x2="l.x2" :y2="l.y2" stroke="#1d6fbf" stroke-width="1.6" stroke-dasharray="8 5" />
        </template>
      </template>




      <!-- Fehlerellipsen -->
      <ellipse
        v-for="el in ellipses" :key="'el-' + el.id"
        :cx="el.cx" :cy="el.cy" :rx="el.rx" :ry="el.ry"
        :transform="`rotate(${el.angle} ${el.cx} ${el.cy})`"
        fill="rgba(29,111,191,0.12)" stroke="#1d6fbf"
        stroke-width="1.2" stroke-dasharray="4 2"
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
        <!-- Näherungskoordinaten nur zeigen, solange KEIN Ergebnis da ist -->
        <text v-if="!hasResult"
              :x="n.x + 9" :y="n.y + 8" font-size="9" fill="#888"
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

      <!-- Koordinatenkreuz unten links -->
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
      <span class="adj">●</span> ausgeglichen &nbsp;
      <span class="ell">⬭</span> Fehlerellipse &nbsp;
      <span class="line-solid">──</span> Strecke &nbsp;
      <span class="line-dash">‑ ‑</span> Richtung &nbsp;
      <span class="line-both">─‑</span> Strecke + Richtung

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
.legend .ell { color: #1d6fbf; }
.legend .line-solid { color: #1d6fbf; letter-spacing: -1px; }
.legend .line-dash  { color: #1d6fbf; letter-spacing: 1px; }

.label {
  paint-order: stroke;
  stroke: #fafafa;
  stroke-width: 2.5px;
  stroke-linejoin: round;
}
</style>
