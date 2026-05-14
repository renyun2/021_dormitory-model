import {
  createRouter,
  createWebHistory,
  type RouteRecordRaw,
} from 'vue-router'
import Layout from '../views/Layout.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: Layout,
    children: [
      { path: '', name: 'home', component: () => import('../views/Home.vue') },
      { path: 'dorms', name: 'dorms', component: () => import('../views/Dorms.vue') },
      { path: 'checkin', name: 'checkin', component: () => import('../views/Checkin.vue') },
      { path: 'swap', name: 'swap', component: () => import('../views/Swap.vue') },
      {
        path: 'checkout',
        name: 'checkout',
        component: () => import('../views/Checkout.vue'),
      },
      { path: 'fees', name: 'fees', component: () => import('../views/Fees.vue') },
      { path: 'repairs', name: 'repairs', component: () => import('../views/Repairs.vue') },
    ],
  },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})
