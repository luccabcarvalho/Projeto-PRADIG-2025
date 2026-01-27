import { createRouter, createWebHashHistory  } from 'vue-router'
import Migracao from '../views/Migracao.vue'
import Progresso from '../views/Progresso.vue'
import Auth from '../views/Auth.vue'
import Perfil from '../views/Perfil.vue'
const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      name: 'migracao',
      component: Migracao
    },
    {
      path: '/auth',
      name: 'auth',
      component: Auth
    },
    {
      path: '/progresso',
      name: 'progresso',
      component: Progresso
    },
    {
      path: '/perfil',
      name: 'perfil',
      component: Perfil
    },
    
  ]
})

export default router
