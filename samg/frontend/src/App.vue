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
    <v-app-bar
      flat="border"
      height="72"
      class="px-4"
      position: relative
      color="#2356a8"
    >
      <div class="d-flex align-center ga-2">
        <v-btn variant="text" to="/migracao">Migração</v-btn>
        <v-btn variant="text" to="/progresso">Progresso</v-btn>

        <v-btn
          v-if="user && user.tipoUsuario === 'adm'"
          variant="text"
          to="/admin"
        >
          Administração
        </v-btn>
      </div>

      <v-spacer />

      <div class="app-title">
        <span class="non-mobile">Sistema de Apoio ao Monitoramento de Graduação</span>
        <span class="mobile">SAMG</span>
      </div>

      <v-spacer />

      <div class="d-flex align-center ga-2">
        <v-btn
          v-if="!user"
          variant="text"
          class="auth-btn"
          to="/"
        >
          Entrar
        </v-btn>

        <v-menu v-if="user">
          <template #activator="{ props }">
            <v-btn
              v-bind="props"
              variant="text"
              prepend-icon="mdi-account-circle-outline"
            >
              {{ user.name }}
            </v-btn>
          </template>

          <v-list>
            <v-list-item :to="{ name: 'perfil' }" title="Meu perfil" />
            <v-list-item @click="logout" title="Sair" base-color="error" />
          </v-list>
        </v-menu>
      </div>
    </v-app-bar>

    <v-main>
      <RouterView />
    </v-main>
  </v-layout>
</template>


<style scoped>
.app-title {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 1rem;
  font-weight: 500;
  color: #fff;
  text-align: center;
  white-space: nowrap;
  min-width: 0;
  max-width: 44vw;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 0 auto;
  z-index: 2;
}

.mobile {
  display: none;
  position: relative;
}

.non-mobile {
  display: inline-block;
  text-align: center;
}

@media (max-width: 900px) {
  .mobile {
    display: inline;
  }

  .app-title {
    font-size: 1rem;
    max-width: 34vw;
  }

  .auth-btn {
    min-width: auto !important;
    padding-left: 8px !important;
    padding-right: 8px !important;
    font-size: 0.8rem !important;
  }
}
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
  flex-wrap: nowrap;
  min-width: 0;
}

.navigation li {
  padding: 16px 14px 0 14px;
  height: 100%;
  display: flex;
  align-items: center;
  white-space: nowrap;
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

@media (max-width: 950px) {
  .app-bar {
    padding-left: 8px !important;
    padding-right: 8px !important;
  }

  .navigation {
    overflow-x: auto;
    overflow-y: hidden;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: thin;
    max-width: 100%;
  }

  .navigation li {
    padding: 12px 8px 0 8px;
  }

  .navigation a {
    font-size: 12px;
  }

  .navigation li + li {
    border-left: 0;
  }

  .mobile {
    display: block !important;
    font-size: inherit !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 100%;
    padding: 0 8px;
  }

  .non-mobile {
    display: none;
  }

  
  .app-title {
    position: static !important;
    left: auto !important;
    transform: none !important;
    max-width: calc(100% - 160px) !important;
    padding: 0 80px !important;
    z-index: 1 !important;
    box-sizing: border-box;
  }

  .app-title {
    display: none !important;
  }
}

</style>
