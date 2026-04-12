import { createRouter, createWebHashHistory  } from 'vue-router'
import Auth from '../views/Auth.vue'
import Migracao from '../views/Migracao.vue'
import Progresso from '../views/Progresso.vue'
import Perfil from '../views/Perfil.vue'
import Admin from '../views/Admin.vue'
const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      name: 'auth',
      component: Auth
    },
    {
      path: '/migracao',
      name: 'migracao',
      component: Migracao
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
    {
      path: '/admin',
      name: 'admin',
      component: Admin
    },
    
  ]
})

export default router
