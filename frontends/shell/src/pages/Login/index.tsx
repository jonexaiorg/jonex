import React, { useState } from 'react'
import { Form, Input, Button, Card, message } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { login, setTokens, setUser, apiClient } from '../../api/auth'
import type { ShellUser } from '@jonex/shell-sdk'
import { isAllowedRedirect } from '@jonex/shell-sdk'
import { colors, radius } from '@jonex/platform-theme/tokens'

function getRedirectParam(): string | null {
  const params = new URLSearchParams(window.location.search)
  const raw = params.get('redirect')
  if (!raw) return null
  try {
    return decodeURIComponent(raw)
  } catch {
    return null
  }
}

function getAppIdParam(): string | null {
  const params = new URLSearchParams(window.location.search)
  return params.get('appId')
}

function createState(): string {
  const arr = new Uint8Array(16)
  crypto.getRandomValues(arr)
  return Array.from(arr, (b) => b.toString(16).padStart(2, '0')).join('')
}

function getDevAllowedOrigins(): string[] {
  try {
    const raw = (import.meta as any).env?.VITE_ALLOWED_REDIRECT_ORIGINS || ''
    return raw ? raw.split(',').map((s: string) => s.trim()).filter(Boolean) : []
  } catch {
    return []
  }
}

async function createLoginTicket(appId: string, redirectUri: string, state: string): Promise<string | null> {
  try {
    const resp = await apiClient.post<{ ticket: string }>('/api/v1/auth/login-ticket', {
      appId,
      redirectUri,
      state,
    })
    return resp.data?.ticket || null
  } catch {
    console.warn('[Login] 创建 login ticket 失败，后端接口可能尚未就绪')
    return null
  }
}

interface LoginValues {
  username: string
  password: string
}

interface LoginResult {
  access_token: string
  refresh_token: string
  user: ShellUser
}

function LoginPage() {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const onFinish = async (values: LoginValues) => {
    setLoading(true)
    try {
      const result: LoginResult = await login(values.username, values.password)
      setTokens(result.access_token, result.refresh_token)
      setUser(result.user as unknown as Record<string, unknown>)
      message.success(`欢迎，${result.user.displayName || result.user.username}`)
      const redirectTo = getRedirectParam()
      if (redirectTo) {
        await handleRedirect(redirectTo)
      } else {
        navigate('/')
      }
    } catch (err: unknown) {
      const messageText =
        (err as { response?: { data?: { message?: string } } }).response?.data?.message ||
        (err as Error).message ||
        '未知错误'
      message.error('登录失败：' + messageText)
    } finally {
      setLoading(false)
    }
  }

  async function handleRedirect(redirectTo: string) {
    const redirectUrl = new URL(redirectTo)

    // 真正同源：共享 localStorage，直接跳转
    if (redirectUrl.origin === window.location.origin) {
      window.location.href = redirectTo
      return
    }

    const isAllowed = isAllowedRedirect(redirectUrl, getDevAllowedOrigins())
    if (!isAllowed) {
      message.error('登录成功，但回跳地址不在允许范围内')
      return
    }

    const appId = getAppIdParam()
    if (!appId) {
      message.error('登录成功，但缺少回跳应用标识')
      return
    }

    const state = createState()
    const ticket = await createLoginTicket(appId, redirectUrl.origin + redirectUrl.pathname, state)

    if (!ticket) {
      message.error('登录成功，但登录态同步失败，请稍后重试')
      return
    }

    redirectUrl.searchParams.set('ticket', ticket)
    redirectUrl.searchParams.set('state', state)
    window.location.href = redirectUrl.toString()
  }

  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      background: colors.bg,
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif',
    }}>
      <Card
        style={{
          width: 400,
          boxShadow: '0 4px 24px rgba(11, 43, 92, 0.08)',
          borderRadius: radius.card,
          border: `1px solid ${colors.borderLight}`,
          textAlign: 'center',
          paddingTop: 12,
        }}
        styles={{ body: { padding: '32px 40px' } }}
      >
        {/* Brand Logo */}
        <div style={{ marginBottom: 24 }}>
          <div style={{
            width: 56, height: 56, borderRadius: 14,
            background: `linear-gradient(135deg, ${colors.accentSoft}, ${colors.accent})`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 28, fontWeight: 700, color: '#fff',
            boxShadow: '0 4px 12px rgba(59,130,246,0.3)',
            margin: '0 auto 16px',
          }}>
            悦
          </div>
          <h2 style={{
            fontSize: 22, fontWeight: 700, color: colors.brandDark,
            marginBottom: 4, letterSpacing: 2,
          }}>
            悦<span style={{ color: colors.accent }}>溪</span>平台
          </h2>
          <p style={{ fontSize: 13, color: colors.textMuted, margin: 0 }}>
            知识数据平台 · 登录
          </p>
        </div>

        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input
              prefix={<UserOutlined style={{ color: colors.textMuted }} />}
              placeholder="用户名"
              style={{ borderRadius: radius.btn, height: 44 }}
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined style={{ color: colors.textMuted }} />}
              placeholder="密码"
              style={{ borderRadius: radius.btn, height: 44 }}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 12 }}>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              style={{
                height: 44,
                borderRadius: radius.btn,
                fontSize: 15,
                fontWeight: 500,
                background: colors.accent,
                borderColor: colors.accent,
              }}
            >
              登录
            </Button>
          </Form.Item>
        </Form>

        <div style={{
          padding: '10px 14px',
          background: colors.rowHover,
          borderRadius: 8,
          fontSize: 12,
          color: colors.textSecondary,
        }}>
          测试账号：admin / admin123
        </div>
      </Card>
    </div>
  )
}

export default LoginPage
