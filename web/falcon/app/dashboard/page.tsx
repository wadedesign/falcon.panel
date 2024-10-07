// web/falcon/app/dashboard/page.tsx

"use client"

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import DashboardLayout from '../components/DashboardLayout'

// Define a type for the user object
interface User {
  email: string;
  // Add other user properties here as needed
}

export default function Dashboard() {
  const [user, setUser] = useState<User | null>(null)
  const router = useRouter()

  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem('accessToken')
      if (!token) {
        router.push('/')
        return
      }

      try {
        const response = await fetch('http://0.0.0.0:3232/api/v1/auth/users/me', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          const userData: User = await response.json()
          setUser(userData)
        } else {
          // Token might be expired, redirect to sign in
          router.push('/')
        }
      } catch (error) {
        console.error('Error fetching user data:', error)
        router.push('/')
      }
    }

    fetchUser()
  }, [router])

  if (!user) {
    return <div>Loading...</div>
  }

  return (
    <DashboardLayout>
      <div className="p-8">
        <h1 className="text-3xl font-bold mb-4">Welcome to your Dashboard</h1>
        <p>Email: {user.email}</p>
        {/* Add more dashboard content here */}
      </div>
    </DashboardLayout>
  )
}
