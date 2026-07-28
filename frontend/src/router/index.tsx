import { createBrowserRouter } from 'react-router-dom'

import { Layout } from '../components/Layout'
import { HomePage } from '../pages/HomePage'
import { LoginPage } from '../pages/LoginPage'
import { RegisterPage } from '../pages/RegisterPage'
import { RestaurantDetailPage } from '../pages/RestaurantDetailPage'
import { RestaurantsPage } from '../pages/RestaurantsPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: 'restaurants',
        element: <RestaurantsPage />,
      },
      {
        path: 'restaurants/:id',
        element: <RestaurantDetailPage />,
      },
      {
        path: 'login',
        element: <LoginPage />,
      },
      {
        path: 'register',
        element: <RegisterPage />,
      },
    ],
  },
])
