import React, { Component, type ReactNode } from 'react'
import { Result, Button, Space } from 'antd'
import i18n from '../../locales/i18n'

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
    const t = i18n.t.bind(i18n)
    if (this.state.hasError) {
      const { appName, standaloneUrl } = this.props
      return (
        <Result
          status="warning"
          title={t('error.serverError')}
          subTitle={appName ? `「${appName}」: ${this.state.error?.message}` : this.state.error?.message}
          extra={
            <Space>
              <Button type="primary" onClick={this.handleRetry}>{t('common.retry')}</Button>
              {standaloneUrl && (
                <Button onClick={() => window.open(standaloneUrl, '_self')}>{t('common.detail')}</Button>
              )}
            </Space>
          }
        />
      )
    }
    return this.props.children
  }
}
