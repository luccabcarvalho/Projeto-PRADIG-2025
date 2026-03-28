<script setup>
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { ref, onMounted, onBeforeUnmount } from 'vue'

const user = ref(null);
function loadUser() {
  try {
    const raw = localStorage.getItem('samg_user');
    user.value = raw ? JSON.parse(raw) : null;
  } catch (e) {
    user.value = null;
  }
}
loadUser();

const router = useRouter();
function logout() {
  localStorage.removeItem('samg_user');
  user.value = null;
  
  window.dispatchEvent(new CustomEvent('samg_user_changed', { detail: null }));
  router.push('/');
}

function onStorage(e) {
  if (e.key === 'samg_user') loadUser();
}
function onCustom(e) {
  loadUser();
}

onMounted(() => {
  window.addEventListener('storage', onStorage);
  window.addEventListener('samg_user_changed', onCustom);
});
onBeforeUnmount(() => {
  window.removeEventListener('storage', onStorage);
  window.removeEventListener('samg_user_changed', onCustom);
});
</script>

<template>
  <v-layout>
    <v-app-bar class="pl-4 app-bar">
      <ul class="d-flex ma-0 navigation">
        <li>
          <RouterLink to="/migracao">Migração</RouterLink>
        </li>
        <li class="ml-4">
          <RouterLink to="/progresso">Progresso</RouterLink>
        </li>
        <li v-if="user && user.tipoUsuario === 'adm'" class="ml-4">
          <RouterLink to="/admin">Administração</RouterLink>
        </li>
        <li v-if="!user" class="ml-4"><RouterLink to="/">Entrar / Cadastrar</RouterLink></li>
        <li v-if="user" class="ml-4">
            <RouterLink :to="{ name: 'perfil' }" class="mr-2">{{ user.name }}</RouterLink>   
        </li>
        <li v-if="user" class="ml-4">
          <v-btn text small color="red" @click="logout">Sair</v-btn>
        </li>
      </ul>
      <v-spacer></v-spacer>
      
      <v-card-title class="non-mobile">Sistema de Apoio à Migração de Grade de BSI (SAMG BSI)</v-card-title>
      <v-card-title class="mobile">SAMG BSI</v-card-title>
      <v-spacer></v-spacer>
    </v-app-bar>
    <v-main>
      <RouterView />
    </v-main>
  </v-layout>
</template>

<style scoped>
header {
  line-height: 1;
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
  height: 100%;
  align-items: center;
  display: flex;
}

.navigation li {
  padding: 16px 14px 0 14px;
  height: 100%;
  display: flex;
  align-items: center;
}

.navigation li + li {
  border-left: 1px solid black;
}

.navigation a:hover {
  background-color: transparent;
  color: black;
}

.navigation a{
  color: black;
  font-size: 13px;
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

.app-bar { position: relative; }

@media (min-width: 768px) {
  .non-mobile {
    display: block !important;
    position: absolute !important;
    right: 16px;
    top: 8px;
    z-index: 10;
  }

  .mobile {
    display: none;
  }
}


@media (max-width: 767px) {
  .non-mobile {
    display: none;
  }
}

</style>
