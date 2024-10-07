"use client"

import React, { ReactNode, useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { ChevronDown, ChevronUp, ChevronRight, Home, User, Settings, LogOut, BarChart2, FileText, Users } from 'lucide-react'

interface DashboardLayoutProps {
  children: ReactNode
}

export default function Component({ children }: DashboardLayoutProps) {
  const router = useRouter()
  const [openDropdown, setOpenDropdown] = useState<string | null>(null)
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const sidebarRef = useRef<HTMLDivElement>(null)
  const toggleButtonRef = useRef<HTMLButtonElement>(null)

  const handleLogout = () => {
    localStorage.removeItem('accessToken')
    router.push('/')
  }

  const toggleDropdown = (key: string) => {
    setOpenDropdown(openDropdown === key ? null : key)
  }

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen)
  }

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        sidebarRef.current &&
        !sidebarRef.current.contains(event.target as Node) &&
        toggleButtonRef.current &&
        !toggleButtonRef.current.contains(event.target as Node)
      ) {
        setIsSidebarOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  const menuItems = [
    { key: 'home', label: 'Home', icon: Home, href: '/dashboard' },
    {
      key: 'analytics',
      label: 'Analytics',
      icon: BarChart2,
      subItems: [
        { label: 'Overview', href: '/dashboard/analytics/overview' },
        { label: 'Reports', href: '/dashboard/analytics/reports' },
      ],
    },
    {
      key: 'management',
      label: 'Management',
      icon: Users,
      subItems: [
        { label: 'Team', href: '/dashboard/management/team' },
        { label: 'Projects', href: '/dashboard/management/projects' },
      ],
    },
    { key: 'documents', label: 'Documents', icon: FileText, href: '/dashboard/documents' },
    { key: 'profile', label: 'Profile', icon: User, href: '/dashboard/profile' },
    { key: 'settings', label: 'Settings', icon: Settings, href: '/dashboard/settings' },
  ]

  return (
    <div className="flex h-screen bg-black p-4">
      {/* Elegant sidebar toggle button AI was here*/}
      <button
        ref={toggleButtonRef}
        className={`lg:hidden fixed left-0 top-1/2 -translate-y-1/2 z-20 bg-blue-900 text-white p-2 rounded-r-md transition-all duration-300 ease-in-out ${
          isSidebarOpen ? 'translate-x-64' : 'translate-x-0'
        }`}
        onClick={toggleSidebar}
        aria-label="Toggle sidebar"
      >
        <ChevronRight className={`h-6 w-6 transition-transform duration-300 ${isSidebarOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Blur overlay */}
      <div
        className={`fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity duration-300 lg:hidden ${
          isSidebarOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
        onClick={() => setIsSidebarOpen(false)}
      ></div>

      {/* Sidebar - bottom layer */}
      <div
        ref={sidebarRef}
        className={`fixed inset-y-0 left-0 z-30 w-64 bg-blue-900 text-white rounded-r-lg shadow-lg overflow-hidden transition-transform duration-300 ease-in-out ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:translate-x-0 lg:static lg:rounded-lg flex flex-col`}
      >
        <div className="p-6">
          <h2 className="text-2xl font-semibold">Falcon Panel</h2>
        </div>
        <nav className="mt-6 flex-grow overflow-y-auto">
          {menuItems.map((item) => (
            <div key={item.key}>
              {item.subItems ? (
                <div>
                  <button
                    onClick={() => toggleDropdown(item.key)}
                    className="flex items-center justify-between w-full py-2 px-4 text-gray-300 hover:bg-blue-800 transition-colors duration-200"
                  >
                    <span className="flex items-center">
                      <item.icon className="mr-2 h-5 w-5" />
                      {item.label}
                    </span>
                    {openDropdown === item.key ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  </button>
                  {openDropdown === item.key && (
                    <div className="bg-blue-950">
                      {item.subItems.map((subItem) => (
                        <Link
                          key={subItem.href}
                          href={subItem.href}
                          className="block py-2 px-8 text-gray-400 hover:text-white hover:bg-blue-800 transition-colors duration-200"
                        >
                          {subItem.label}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <Link
                  href={item.href}
                  className="flex items-center py-2 px-4 text-gray-300 hover:bg-blue-800 transition-colors duration-200"
                >
                  <item.icon className="mr-2 h-5 w-5" />
                  {item.label}
                </Link>
              )}
            </div>
          ))}
        </nav>
        <button
          onClick={handleLogout}
          className="flex items-center w-full py-2 px-4 text-white bg-red-600 hover:bg-red-700 transition-colors duration-200 mt-auto"
        >
          <LogOut className="mr-2 h-5 w-5" />
          Logout
        </button>
      </div>

      {/* Main content - top layer */}
      <div className="flex-1 ml-0 lg:ml-4">
        <div className="bg-blue-100 h-full rounded-3xl shadow-2xl overflow-hidden relative">
          {/* Content wrapper */}
          <div className="absolute inset-2 bg-white rounded-2xl shadow-inner overflow-auto">
            <div className="p-8">
              {children}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}