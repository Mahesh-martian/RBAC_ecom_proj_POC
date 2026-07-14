import { Outlet } from 'react-router-dom'
import Header from './Header'
import Footer from './Footer'
import ChatBot from '../ChatBot'

export default function MainLayout() {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main className="flex-1 py-8">
        <Outlet />
      </main>
      <Footer />
      <ChatBot />
    </div>
  )
}
