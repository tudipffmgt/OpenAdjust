<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  observations: { type: Array, required: true },
  result: { type: Object, default: null },
})

const RAD_TO_MGON = 200000.0 / Math.PI   // rad -> mgon
const ANGLE_TYPES = new Set(['direction', 'zenith'])

const TYPE_LABEL = {
  distance: 'Horizontalstrecke',
  direction: 'Horizontalrichtung',
  zenith: 'Zenitwinkel',
  levelling: 'Höhenunterschied',
}

// Auswählbare Grenzwerte (Data-Snooping nach Baarda)
const BAARDA_PRESETS = [
  { label: 'α₀ = 5 %  (k = 2.80)',   value: 2.80 },
  { label: 'α₀ = 1 %  (k = 3.10)',   value: 3.10 },
  { label: 'α₀ = 0.1 % (k = 3.29)',  value: 3.29 },
]
const baardaLimit = ref(3.29)   // Standard: Baarda-Klassiker

const RED_LIMIT = 4.0   // ab hier grober Fehler sehr wahrscheinlich (Vorlesung)

function severity(w) {
  if (w == null) return 'none'
  const aw = Math.abs(w)
  if (aw >= RED_LIMIT) return 'exceed'        // rot
  if (aw >= baardaLimit.value) return 'warn'  // gelb
  return 'ok'                                 // grün
}


// Eine Zeile pro (aktiver) Beobachtung, Residuum passend umgerechnet
const rows = computed(() => {
  const res = props.result?.residuals
  if (!res) return []
  const nv = props.result.normalized_residuals || []
  const out = []
  // nur aktive Beobachtungen gehen in die Ausgleichung -> gleiche Reihenfolge
  const active = props.observations.filter(o => o.enabled !== false)
  active.forEach((o, i) => {
    const vRaw = res[i]
    if (vRaw == null) return
    const isAngle = ANGLE_TYPES.has(o.type)
    // Data-Snooping klassisch mit a-priori σ0 = 1 (nicht a-posteriori!)
    const wRaw = nv[i]
    const w = wRaw == null ? null : wRaw * props.result.sigma_0
    out.push({
      id: o.id,
      type: TYPE_LABEL[o.type] || o.type,
      station: o.station,
      target: o.target,
      value: o.value,                       // in GUI-Einheit (gon bzw. m)
      unit: isAngle ? 'gon' : 'm',
      v: isAngle ? vRaw * RAD_TO_MGON : vRaw * 1000,  // mgon bzw. mm
      vUnit: isAngle ? 'mgon' : 'mm',
      w: w,                                  // normierte Verbesserung (dimensionslos)
      severity: severity(w),
    })
  })
  return out
})


const f = (v, d = 2) => (v == null ? '–' : v.toFixed(d))
</script>

<template>
  <div v-if="rows.length" class="res-table">
    <h3>Ergebnis: Verbesserungen (Residuen)</h3>

    <label class="limit">
      Grenzwert (Data-Snooping):
      <select v-model.number="baardaLimit">
        <option v-for="p in BAARDA_PRESETS" :key="p.value" :value="p.value">
          {{ p.label }}
        </option>
      </select>
    </label>

    <table>
      <thead>
        <tr>
          <th>ID</th><th>Typ</th><th>Von</th><th>Nach</th>
          <th>Beobachtung</th><th>v (Verbesserung)</th><th>NV (w)</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in rows" :key="r.id">
          <td class="id">{{ r.id }}</td>
          <td class="type">{{ r.type }}</td>
          <td>{{ r.station }}</td>
          <td>{{ r.target }}</td>
          <td>{{ f(r.value, 4) }} {{ r.unit }}</td>
          <td :class="{ big: Math.abs(r.v) > 5 }">
            {{ r.v > 0 ? '+' : '' }}{{ f(r.v, 2) }} {{ r.vUnit }}
          </td>
          <td :class="'nv-' + r.severity">
            {{ r.w == null ? '–' : f(Math.abs(r.w), 2) }}
          </td>
        </tr>
      </tbody>
    </table>

    <p class="hint">
      v = ausgeglichener Wert − Beobachtung. NV = normierte Verbesserung |v|/σ_v.
      Ampel: grün = unauffällig (&lt; {{ baardaLimit.toFixed(2) }}), gelb = grenzwertig,
      rot = grober Fehler wahrscheinlich (≥ {{ RED_LIMIT.toFixed(1) }}).
      Der grün/gelb-Übergang hängt von α₀ ab.
    </p>
  </div>
</template>



<style scoped>
.res-table { margin: 1.5rem 0; overflow-x: auto; }
table { border-collapse: collapse; font-size: .85rem; }
th, td { border: 1px solid #ccc; padding: .25rem .6rem; text-align: right; }
th { background: #f4f4f4; text-align: center; }
td.id { font-weight: bold; text-align: left; }
td.type { text-align: left; }
td.big { color: #b02a37; font-weight: 700; }  /* auffällige Verbesserung */
.hint { color: #666; font-size: .8rem; margin-top: .3rem; }
.limit { display: block; margin: .5rem 0; font-size: .85rem; }
.limit select { margin-left: .4rem; }

/* Ampel für normierte Verbesserungen */
td.nv-ok     { background: #eaf6ee; color: #0d4a2f; font-weight: 600; }
td.nv-warn   { background: #fff3cd; color: #7a5a00; font-weight: 700; }
td.nv-exceed { background: #b02a37; color: #fff;    font-weight: 700; }
td.nv-none   { color: #999; }
</style>

