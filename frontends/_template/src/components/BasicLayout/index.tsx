import React from 'react'
import { Layout } from 'antd'
import { Outlet } from 'react-router-dom'
import { observer } from 'mobx-react-lite'
import usePageMeta from '@/hooks/usePageMeta'
import HeaderNav from '@/components/HeaderNav'
import styles from './index.module.scss'

const { Content } = Layout

const BasicLayout = observer(() => {
  const meta = usePageMeta() as Record<string, any>

  return (
    <div className={styles['page-layout']}>
      <Layout>
        <Layout>
          <HeaderNav
            type={meta.type as string | null | undefined}
            title={meta.title as string | undefined}
            previous={meta.previous as string | undefined}
            previousTitle={meta.previousTitle as string | undefined}
          />
          <Content className={styles['page-content']}>
            <Outlet />
          </Content>
        </Layout>
      </Layout>
    </div>
  )
})

export default BasicLayout
