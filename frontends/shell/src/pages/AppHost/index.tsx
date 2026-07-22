import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Alert, Spin, Result, Button } from 'antd'
import { fetchAppManifest } from '../../api/manifest'
import { getAccessToken, getUser, logout } from '../../api/auth'
import { loadRemoteApp } from '../../app-registry/loadRemoteApp'
import type { AppManifestEntry, ShellUser } from '@jonex/shell-sdk'

type MountFn = (container: HTMLElement, context: unknown) => () => void

interface RemoteLifecycle {
  appId: string
  mountNode: HTMLDivElement
  unmount: () => void
  disposed: boolean
}

const safeRemoveMountNode = (mountNode: HTMLDivElement) => {
  if (mountNode.parentNode) {
    mountNode.parentNode.removeChild(mountNode)
  }
}

export default function AppHost() {
  const { appId } = useParams<{ appId: string }>()
  const navigate = useNavigate()

  const containerRef = useRef<HTMLDivElement>(null)
  const lifecycleRef = useRef<RemoteLifecycle | null>(null)

  const [manifest, setManifest] = useState<{ apps: AppManifestEntry[] } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [remoteLoading, setRemoteLoading] = useState(false)
  const [remoteError, setRemoteError] = useState<string | null>(null)

  useEffect(() => {
    fetchAppManifest()
      .then(setManifest)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const appConfig = useMemo(() => {
    if (!manifest?.apps) return null
    return manifest.apps.find((a) => a.id === appId) ?? null
  }, [manifest, appId])

  const user = getUser()
  const userRoles: string[] = user?.roles ?? []
  const appRoles: string[] = appConfig?.roles ?? []
  const hasAppAccess = appRoles.length === 0 || appRoles.some((r) => userRoles.includes(r))

  const disposeLifecycle = useCallback((lifecycle: RemoteLifecycle | null) => {
    if (!lifecycle) return
    if (lifecycle.disposed) return

    lifecycle.disposed = true
    if (lifecycleRef.current === lifecycle) {
      lifecycleRef.current = null
    }

    try {
      lifecycle.unmount()
    } catch (err) {
      console.error(`[shell] Failed to unmount remote app "${lifecycle.appId}":`, err)
    } finally {
      safeRemoveMountNode(lifecycle.mountNode)
    }
  }, [])

  const disposeCurrentRemote = useCallback(() => {
    disposeLifecycle(lifecycleRef.current)
  }, [disposeLifecycle])

  useEffect(() => {
    return () => {
      disposeCurrentRemote()
    }
  }, [disposeCurrentRemote])

  useEffect(() => {
    if (!appConfig?.entry || !appConfig.enabled || !hasAppAccess || !containerRef.current) {
      disposeCurrentRemote()
      setRemoteLoading(false)
      setRemoteError(null)
      return
    }

    let cancelled = false
    let localLifecycle: RemoteLifecycle | null = null
    const hostNode = containerRef.current
    const mountNode = document.createElement('div')
    mountNode.dataset.remoteApp = appConfig.id
    mountNode.style.minHeight = '100%'

    disposeCurrentRemote()
    hostNode.appendChild(mountNode)

    setRemoteLoading(true)
    setRemoteError(null)

    const shellContext = {
      appId: appConfig.id,
      mode: 'hosted' as const,
      basePath: appConfig.basePath,
      token: getAccessToken(),
      user: getUser(),
      locale: localStorage.getItem('locale') || 'zh',
      theme: {},
      navigate: (to: string) => {
        const target = to.startsWith('/') ? to : `/${to}`
        navigate(`${appConfig.basePath}${target}`)
      },
      logout: () => logout(),
      getToken: () => getAccessToken(),
      getCurrentUser: () => getUser(),
      emitEvent: () => {},
      onEvent: () => () => {},
      reportError: (error: unknown) => console.error('[shell] Sub-app error:', error),
      reportMetric: () => {},
    }

    loadRemoteApp<MountFn>({
      entry: appConfig.entry,
      scope: appConfig.scope,
      module: appConfig.module || './Mount',
    })
      .then((mountFn) => {
        if (cancelled) return
        if (typeof mountFn !== 'function') {
          throw new Error(`Remote module is not a function (got ${typeof mountFn})`)
        }

        const unmount = mountFn(mountNode, shellContext)
        const lifecycle: RemoteLifecycle = {
          appId: appConfig.id,
          mountNode,
          unmount: typeof unmount === 'function' ? unmount : () => {},
          disposed: false,
        }
        localLifecycle = lifecycle
        lifecycleRef.current = lifecycle

        if (cancelled) {
          disposeLifecycle(lifecycle)
          return
        }

        setRemoteLoading(false)
      })
      .catch((err: Error) => {
        if (cancelled) return
        safeRemoveMountNode(mountNode)
        setRemoteError(err.message)
        setRemoteLoading(false)
      })

    return () => {
      cancelled = true
      if (localLifecycle) {
        disposeLifecycle(localLifecycle)
      } else {
        safeRemoveMountNode(mountNode)
      }
    }
  }, [appConfig, disposeCurrentRemote, disposeLifecycle, hasAppAccess, navigate])

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 120 }}><Spin size="large" /></div>
  }

  if (error) {
    return <Alert type="error" message="加载应用清单失败" description={error} showIcon />
  }

  if (!appConfig) {
    return <Result status="404" title="应用未找到" subTitle={`未找到应用 "${appId}"`} />
  }

  if (!appConfig.enabled) {
    return <Result status="warning" title="应用已停用" subTitle={`「${appConfig.name}」已被管理员停用`} />
  }

  if (!hasAppAccess) {
    return <Result status="403" title="无访问权限" subTitle={`你没有权限访问「${appConfig.name}」`} />
  }

  if (remoteError) {
    return (
      <Result
        status="warning"
        title="加载失败"
        subTitle={`无法加载「${appConfig.name}」: ${remoteError}`}
        extra={[
          <Button key="retry" type="primary" onClick={() => window.location.reload()}>重试</Button>,
          appConfig.standaloneUrl ? (
            <Button key="standalone" onClick={() => window.open(appConfig.standaloneUrl, '_self')}>独立打开</Button>
          ) : null,
        ].filter(Boolean)}
      />
    )
  }

  return (
    <div style={{ minHeight: '100%', position: 'relative' }}>
      <div ref={containerRef} style={{ minHeight: '100%' }} />
      {remoteLoading && (
        <div style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          background: 'rgba(245, 247, 250, 0.72)',
        }}>
          <Spin size="large" tip="正在加载应用..." />
        </div>
      )}
    </div>
  )
}
