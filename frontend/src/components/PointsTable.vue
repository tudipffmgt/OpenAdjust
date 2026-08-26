<script setup>
// Die Punkte kommen als v-model vom Elternteil (App.vue)
const points = defineModel({ type: Array, required: true })

function addPoint() {
  points.value.push({
    id: `P${points.value.length + 1}`,
    x: 0, y: 0, z: 0,
    fixed_x: false, fixed_y: false, fixed_z: true,
  })
}

function removePoint(index) {
  points.value.splice(index, 1)
}
</script>

<template>
  <div class="points-table">
    <h3>Punkte</h3>
    <table>
      <thead>
        <tr>
          <th>ID</th><th>X</th><th>Y</th><th>Z</th>
          <th>Fix X</th><th>Fix Y</th><th>Fix Z</th><th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(p, i) in points" :key="i">
          <td><input v-model="p.id" /></td>
          <td><input type="number" step="any" v-model.number="p.x" /></td>
          <td><input type="number" step="any" v-model.number="p.y" /></td>
          <td><input type="number" step="any" v-model.number="p.z" /></td>
          <td><input type="checkbox" v-model="p.fixed_x" /></td>
          <td><input type="checkbox" v-model="p.fixed_y" /></td>
          <td><input type="checkbox" v-model="p.fixed_z" /></td>
          <td><button @click="removePoint(i)" title="Löschen">✕</button></td>
        </tr>
      </tbody>
    </table>
    <button @click="addPoint">+ Punkt</button>
  </div>
</template>

<style scoped>
table { border-collapse: collapse; margin: .5rem 0; }
th, td { border: 1px solid #ccc; padding: .2rem .4rem; text-align: center; }
input[type="number"], input[type="text"] { width: 6rem; }
input:not([type]) { width: 4rem; }  /* die ID-Spalte */
</style>
