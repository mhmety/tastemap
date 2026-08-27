import { createBrowserRouter, Navigate } from 'react-router-dom'

import { Layout } from '../components/Layout'
import { FavoritesPage } from '../pages/FavoritesPage'
import { LoginPage } from '../pages/LoginPage'
import { RegisterPage } from '../pages/RegisterPage'
import { RestaurantDetailPage } from '../pages/RestaurantDetailPage'
import { RestaurantsPage } from '../pages/RestaurantsPage'
import { ProtectedRoute } from './ProtectedRoute'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      {
        index: true,
        element: <RestaurantsPage />,
      },
      {
        path: 'restaurants',
        element: <Navigate to="/" replace />,
      },
      {
        path: 'restaurants/:id',
        element: <RestaurantDetailPage />,
      },
      {
        path: 'favorites',
        element: (
          <ProtectedRoute>
            <FavoritesPage />
          </ProtectedRoute>
        ),
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

