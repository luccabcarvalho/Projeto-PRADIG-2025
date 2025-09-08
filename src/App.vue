<script setup>
import { RouterLink, RouterView } from 'vue-router'

</script>

<template>
  <v-layout>
    <v-app-bar class="pl-4">
      <ul class="d-flex ma-0 navigation">
        <li><RouterLink to="/">Migração</RouterLink></li>
        <li class="ml-4"><RouterLink to="/progresso">Progresso</RouterLink></li>
      </ul>
      <v-spacer></v-spacer>
      <v-card-title class="non-mobile">Sistema de Apoio à Migração de Grade de BSI (SAMG BSI)</v-card-title>
      <v-card-title class="mobile">SAMG BSI</v-card-title>
    </v-app-bar>
    <v-main>
      <RouterView />
    </v-main>
    
  </v-layout>

</template>

<style scoped>
header {
  line-height: 1.5;
  max-height: 100vh;
}

.logo {
  display: block;
  margin: 0 auto 2rem;
}

nav {
  width: 100%;
  font-size: 12px;
  text-align: center;
  margin-top: 2rem;
}

nav a.router-link-exact-active {
  color: var(--color-text);
}

nav a.router-link-exact-active:hover {
  background-color: transparent;
}

nav a {
  display: inline-block;
  padding: 0 1rem;
  border-left: 1px solid var(--color-border);
}

nav a:first-of-type {
  border: 0;
}

.navigation {
  list-style-type: none;
  color: black;
  border-right: 1px solid black;
  height: 100%;
  align-items: center;
  
}

.navigation li:first-child {
  border-right: 1px solid black;
  
}

.navigation li {
  padding-right: 14px;
  height: 100%;
  padding-top: 16px;
}

.navigation a:hover {
  background-color: transparent;
  color: black;
}

.navigation a{
  color: black;
  font-size: 18px;
  font-weight: 400;
  text-decoration: underline;
}


@media (min-width: 1024px) {
  header {
    display: flex;
    place-items: center;
    padding-right: calc(var(--section-gap) / 2);
  }

  .logo {
    margin: 0 2rem 0 0;
  }

  header .wrapper {
    display: flex;
    place-items: flex-start;
    flex-wrap: wrap;
  }

  nav {
    text-align: left;
    margin-left: -1rem;
    font-size: 1rem;

    padding: 1rem 0;
    margin-top: 1rem;
  }
}
@media (min-width: 768px) {
  .non-mobile {
    display: contents !important;
  }

  .mobile {
    display: none;
  }
}
@media (min-width: 280px) {
  .non-mobile {
    display: none;
  }

}

</style>
