import { Outlet } from 'react-router-dom';
import useDocumentTitle from '@/hooks/useDocumentTitle';
import RouteSync from '@/components/RouteSync';

const AppLayout = () => {
  useDocumentTitle();
  return (
    <>
      <RouteSync />
      <Outlet />
    </>
  );
};

export default AppLayout;
