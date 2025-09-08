<template>
    <DiagramEditor v-model="graph"></DiagramEditor>
</template>
<script>
import { DiagramEditor } from "diagram-vue";
import "diagram-vue/dist/diagram.css";
export default {
  name: "HelloWorld",
  components: {
    DiagramEditor
  },
  data() {
    return {
      graph: {
        width: 800,
        height: 600,
        background: "#f0f0f0",
        nodes: [],
        links: []
      }
    };
  }
};
</script>
<style>
</style>