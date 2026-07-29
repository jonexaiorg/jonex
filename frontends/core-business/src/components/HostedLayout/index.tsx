import { Layout } from 'antd';
import { Outlet } from 'react-router-dom';
import useDocumentTitle from '@/hooks/useDocumentTitle';
import RouteSync from '@/components/RouteSync';

const { Content } = Layout;

export default function HostedLayout() {
  useDocumentTitle();
  return (
    <Content style={{ padding: 0, minHeight: '100%' }}>
      <RouteSync />
      <Outlet />
    </Content>
  );
}
