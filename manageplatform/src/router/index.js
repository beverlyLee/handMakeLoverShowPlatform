import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '数据概览', icon: 'DataLine' }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/users/index.vue'),
        meta: { title: '用户管理', icon: 'User' }
      },
      {
        path: 'teachers',
        name: 'Teachers',
        component: () => import('@/views/teachers/index.vue'),
        meta: { title: '老师管理', icon: 'Avatar' }
      },
      {
        path: 'teachers-verify',
        name: 'TeachersVerify',
        component: () => import('@/views/teachers/verify.vue'),
        meta: { title: '老师入驻审核', icon: 'DocumentChecked' }
      },
      {
        path: 'products',
        name: 'Products',
        component: () => import('@/views/products/index.vue'),
        meta: { title: '商品管理', icon: 'Goods' }
      },
      {
        path: 'products-verify',
        name: 'ProductsVerify',
        component: () => import('@/views/products/verify.vue'),
        meta: { title: '作品审核', icon: 'DocumentChecked' }
      },
      {
        path: 'orders',
        name: 'Orders',
        component: () => import('@/views/orders/index.vue'),
        meta: { title: '订单管理', icon: 'List' }
      },
      {
        path: 'messages',
        name: 'Messages',
        component: () => import('@/views/messages/index.vue'),
        meta: { title: '消息管理', icon: 'ChatDotRound' }
      },
      {
        path: 'refunds',
        name: 'Refunds',
        component: () => import('@/views/refunds/index.vue'),
        meta: { title: '退款管理', icon: 'Money' }
      },
      {
        path: 'activities',
        name: 'Activities',
        component: () => import('@/views/activities/index.vue'),
        meta: { title: '活动管理', icon: 'Calendar' }
      },
      {
        path: 'activities-verify',
        name: 'ActivitiesVerify',
        component: () => import('@/views/activities/verify.vue'),
        meta: { title: '活动审核', icon: 'DocumentChecked' }
      },
      {
        path: 'reviews',
        name: 'Reviews',
        component: () => import('@/views/reviews/index.vue'),
        meta: { title: '评价管理', icon: 'ChatDotRound' }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/index.vue'),
        meta: { title: '个人中心', icon: 'UserFilled' }
      },
      {
        path: 'basic-data/categories',
        name: 'Categories',
        component: () => import('@/views/basic-data/categories.vue'),
        meta: { title: '手工分类', icon: 'Collection' }
      },
      {
        path: 'basic-data/activity-types',
        name: 'ActivityTypes',
        component: () => import('@/views/basic-data/activityTypes.vue'),
        meta: { title: '活动类型', icon: 'Menu' }
      },
      {
        path: 'basic-data/system-config',
        name: 'SystemConfig',
        component: () => import('@/views/basic-data/systemConfig.vue'),
        meta: { title: '系统参数', icon: 'Setting' }
      },
      {
        path: 'stats/users',
        name: 'StatsUsers',
        component: () => import('@/views/stats/users.vue'),
        meta: { title: '用户统计', icon: 'User' }
      },
      {
        path: 'stats/teachers',
        name: 'StatsTeachers',
        component: () => import('@/views/stats/teachers.vue'),
        meta: { title: '老师统计', icon: 'Avatar' }
      },
      {
        path: 'stats/products',
        name: 'StatsProducts',
        component: () => import('@/views/stats/products.vue'),
        meta: { title: '作品统计', icon: 'Goods' }
      },
      {
        path: 'stats/orders',
        name: 'StatsOrders',
        component: () => import('@/views/stats/orders.vue'),
        meta: { title: '订单统计', icon: 'List' }
      },
      {
        path: 'stats/activities',
        name: 'StatsActivities',
        component: () => import('@/views/stats/activities.vue'),
        meta: { title: '活动统计', icon: 'Calendar' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const token = localStorage.getItem('token')
  
  document.title = to.meta.title ? `${to.meta.title} - 手作爱好者管理后台` : '手作爱好者管理后台'
  
  if (to.path === '/login') {
    if (token && userStore.userInfo) {
      next('/dashboard')
    } else {
      next()
    }
  } else {
    if (token) {
      if (!userStore.userInfo) {
        userStore.getUserInfo().then(() => {
          next()
        }).catch(() => {
          localStorage.removeItem('token')
          next('/login')
        })
      } else {
        next()
      }
    } else {
      next('/login')
    }
  }
})

export default router
