import React, { Component, type ReactNode } from 'react'
import { Button, Result, Spin } from 'antd'

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
          <Spin size="large" tip="正在加载应用..." />
        </div>
      )
    }

    if (error) {
      return (
        <Result
          status="warning"
          title="应用加载失败"
          subTitle={appName ? `无法加载「${appName}」` : '无法加载子应用'}
          extra={[
            <Button key="retry" type="primary" onClick={this.handleRetry}>
              重试
            </Button>,
            standaloneUrl ? (
              <Button key="standalone" onClick={() => { window.open(standaloneUrl, '_self') }}>
                在新窗口打开
              </Button>
            ) : null,
          ].filter(Boolean)}
        />
      )
    }

    return children
  }
}
