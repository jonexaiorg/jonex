import { Outlet } from 'react-router-dom'
import useDocumentTitle from '@/hooks/useDocumentTitle'

const AppLayout = () => {
  useDocumentTitle()
  return <Outlet />
}

export default AppLayout
