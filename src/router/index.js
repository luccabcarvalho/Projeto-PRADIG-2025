import { createRouter, createWebHashHistory  } from 'vue-router'
import Migracao from '../views/Migracao.vue'
import Progresso from '../views/Progresso.vue'
const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      name: 'migracao',
      component: Migracao
    },
    {
      path: '/progresso',
      name: 'progresso',
      component: Progresso
    },
    
  ]
})

export default router
