import React, { Component, type ReactNode } from 'react';
import { Button, Result, Spin } from 'antd';
import { withTranslation, WithTranslation } from 'react-i18next';

interface Props extends WithTranslation {
  children: ReactNode;
  standaloneUrl?: string;
  appName?: string;
  loading?: boolean;
}

interface State {
  error: Error | null;
  retrying: boolean;
}

class RemoteAppBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { error: null, retrying: false };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { error };
  }

  handleRetry = (): void => {
    this.setState({ error: null, retrying: false });
  };

  render() {
    const { error, retrying } = this.state;
    const { children, standaloneUrl, appName, loading } = this.props;

    if (loading || retrying) {
      return (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            padding: 120,
          }}
        >
          <Spin size="large" tip={this.props.t('shell.loadingApp')} />
        </div>
      );
    }

    if (error) {
      return (
        <Result
          status="warning"
          title={this.props.t('shell.loadAppFailed')}
          subTitle={appName ? this.props.t('shell.cannotLoadApp', { appName }) : this.props.t('shell.cannotLoadSubApp')}
          extra={[
            <Button key="retry" type="primary" onClick={this.handleRetry}>
              {this.props.t('common.retry')}
            </Button>,
            standaloneUrl ? (
              <Button
                key="standalone"
                onClick={() => {
                  window.open(standaloneUrl, '_self');
                }}
              >
                {this.props.t('shell.openInNewWindow')}
              </Button>
            ) : null,
          ].filter(Boolean)}
        />
      );
    }

    return children;
  }
}

export default withTranslation()(RemoteAppBoundary);
