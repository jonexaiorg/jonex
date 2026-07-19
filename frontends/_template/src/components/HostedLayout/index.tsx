import { Layout } from 'antd'
import { Outlet } from 'react-router-dom'
import useDocumentTitle from '@/hooks/useDocumentTitle'

const { Content } = Layout

export default function HostedLayout() {
  useDocumentTitle()
  return (
    <Content style={{ padding: 0, minHeight: '100%' }}>
      <Outlet />
    </Content>
  )
}
