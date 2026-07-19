import React from 'react'
import { useTranslation } from 'react-i18next'
import { Card, Typography } from 'antd'

const { Title, Paragraph } = Typography

export default function Home() {
  const { t } = useTranslation()

  return (
    <Card>
      <Title level={2}>{'Welcome to {{APP_TITLE}}'}</Title>
      <Paragraph>
        This is a starter scaffold with:
      </Paragraph>
      <ul>
        <li>React 18</li>
        <li>Vite</li>
        <li>React Router v6</li>
        <li>MobX State Management</li>
        <li>Ant Design 6</li>
        <li>i18n Internationalization</li>
        <li>Axios with Interceptors</li>
      </ul>
      <Paragraph>
        Start building your application by adding pages to <code>src/pages/</code> and configure routes in <code>src/router/routes.config.js</code>.
      </Paragraph>
    </Card>
  )
}
