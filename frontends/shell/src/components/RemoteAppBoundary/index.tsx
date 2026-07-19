import React, { Component, type ReactNode } from 'react'
import { Button, Result, Spin } from 'antd'
import i18n from '../../locales/i18n'

interface Props {
  children: ReactNode
  standaloneUrl?: string
  appName?: string
  loading?: boolean
}

interface State {
  error: Error | null
  retrying: boolean
}

export default class RemoteAppBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { error: null, retrying: false }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { error }
  }

  handleRetry = (): void => {
    this.setState({ error: null, retrying: false })
  }

  render() {
    const t = i18n.t.bind(i18n)
    const { error, retrying } = this.state
    const { children, standaloneUrl, appName, loading } = this.props

    if (loading || retrying) {
      return (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          padding: 120,
        }}>
          <Spin size="large" tip={t('common.loading')} />
        </div>
      )
    }

    if (error) {
      return (
        <Result
          status="warning"
          title={t('error.requestFailed')}
          subTitle={appName ? `${t('error.requestFailed')}「${appName}」` : t('error.notFound')}
          extra={[
            <Button key="retry" type="primary" onClick={this.handleRetry}>
              {t('common.retry')}
            </Button>,
            standaloneUrl ? (
              <Button key="standalone" onClick={() => { window.open(standaloneUrl, '_self') }}>
                {t('common.detail')}
              </Button>
            ) : null,
          ].filter(Boolean)}
        />
      )
    }

    return children
  }
}
