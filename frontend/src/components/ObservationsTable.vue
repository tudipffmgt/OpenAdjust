<script setup>
// Beobachtungen als v-model, Punkte als Prop (für Station/Ziel-Dropdowns)
const observations = defineModel({ type: Array, required: true })
const props = defineProps({
  points: { type: Array, required: true },
})

const OBS_TYPES = [
  { value: 'distance',  label: 'Horizontalstrecke (m)' },
  { value: 'direction', label: 'Horizontalrichtung (gon)' },
  { value: 'zenith',    label: 'Zenitwinkel (gon)' },
  { value: 'levelling', label: 'Höhenunterschied (m)' },
]


// Einheit je nach Beobachtungstyp (Winkel -> gon, sonst m)
function unitFor(type) {
  return (type === 'direction' || type === 'zenith') ? 'gon' : 'm'
}
// Schrittweite fürs Spinner-Feld (Winkel feiner als Strecken/Höhen)
function stepFor(type) {
  return (type === 'direction' || type === 'zenith') ? '0.0001' : '0.001'
}

function addObservation() {
  const firstId = props.points[0]?.id ?? ''
  const secondId = props.points[1]?.id ?? firstId
  observations.value.push({
    id: `o${observations.value.length + 1}`,
    type: 'distance',
    station: firstId,
    target: secondId,
    value: 0,
    std_dev: 0.002,
    enabled: true,
  })
}

function removeObservation(index) {
  observations.value.splice(index, 1)
}
</script>

<template>
  <div class="obs-table">
    <h3>Beobachtungen</h3>
    <table>
      <thead>
        <tr>
          <th>ID</th><th>Typ</th><th>Von</th><th>Nach</th>
          <th>Wert</th><th>σ</th><th>Aktiv</th><th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(o, i) in observations" :key="i">
          <td><input v-model="o.id" class="id" /></td>
          <td>
            <select v-model="o.type">
              <option v-for="t in OBS_TYPES" :key="t.value" :value="t.value">
                {{ t.label }}
              </option>
            </select>
          </td>
          <td>
            <select v-model="o.station">
              <option v-for="p in points" :key="p.id" :value="p.id">{{ p.id }}</option>
            </select>
          </td>
          <td>
            <select v-model="o.target">
              <option v-for="p in points" :key="p.id" :value="p.id">{{ p.id }}</option>
            </select>
          </td>
          <td>
            <input type="number" :step="stepFor(o.type)" v-model.number="o.value" />
            <span class="unit">{{ unitFor(o.type) }}</span>
          </td>
          <td>
            <input type="number" :step="stepFor(o.type)" v-model.number="o.std_dev" />
            <span class="unit">{{ unitFor(o.type) }}</span>
          </td>
          <td><input type="checkbox" v-model="o.enabled" /></td>
          <td><button @click="removeObservation(i)" title="Löschen">✕</button></td>
        </tr>
      </tbody>
    </table>
    <button @click="addObservation" :disabled="points.length < 2">+ Beobachtung</button>
    <p v-if="points.length < 2" class="hint">
      Lege zuerst mindestens zwei Punkte an.
    </p>
  </div>
</template>


<style scoped>
table { border-collapse: collapse; margin: .5rem 0; }
th, td { border: 1px solid #ccc; padding: .2rem .4rem; text-align: center; }
input[type="number"] { width: 6rem; }
input.id { width: 4rem; }
select { min-width: 6rem; }
.hint { color: #b8860b; font-size: .85rem; }
.unit { margin-left: .25rem; color: #666; font-size: .8rem; }
</style>
