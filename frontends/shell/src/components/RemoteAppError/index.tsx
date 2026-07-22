import React, { Component, type ReactNode } from 'react'
import { Result, Button, Space } from 'antd'

interface Props {
  children: ReactNode
  appName?: string
  standaloneUrl?: string
  onRetry?: () => void
}

interface State {
  hasError: boolean
  error: Error | null
}

export default class RemoteAppError extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[shell] Remote app render error:', error, info)
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null })
    this.props.onRetry?.()
  }

  render() {
    if (this.state.hasError) {
      const { appName, standaloneUrl } = this.props
      return (
        <Result
          status="warning"
          title="应用运行出错"
          subTitle={appName ? `「${appName}」运行时发生错误: ${this.state.error?.message}` : this.state.error?.message}
          extra={
            <Space>
              <Button type="primary" onClick={this.handleRetry}>重试</Button>
              {standaloneUrl && (
                <Button onClick={() => window.open(standaloneUrl, '_self')}>独立打开</Button>
              )}
            </Space>
          }
        />
      )
    }
    return this.props.children
  }
}
