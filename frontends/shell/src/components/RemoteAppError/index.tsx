import React, { Component, type ReactNode } from 'react';
import { Result, Button, Space } from 'antd';
import { withTranslation, WithTranslation } from 'react-i18next';

interface Props extends WithTranslation {
  children: ReactNode;
  appName?: string;
  standaloneUrl?: string;
  onRetry?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class RemoteAppError extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[shell] Remote app render error:', error, info);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
    this.props.onRetry?.();
  };

  render() {
    if (this.state.hasError) {
      const { appName, standaloneUrl } = this.props;
      return (
        <Result
          status="warning"
          title={this.props.t('shell.appRunError')}
          subTitle={
            appName
              ? this.props.t('shell.appRunErrorMessage', { appName, message: this.state.error?.message ?? '' })
              : this.state.error?.message
          }
          extra={
            <Space>
              <Button type="primary" onClick={this.handleRetry}>
                {this.props.t('common.retry')}
              </Button>
              {standaloneUrl && (
                <Button onClick={() => window.open(standaloneUrl, '_self')}>
                  {this.props.t('shell.openStandalone')}
                </Button>
              )}
            </Space>
          }
        />
      );
    }
    return this.props.children;
  }
}

export default withTranslation()(RemoteAppError);
