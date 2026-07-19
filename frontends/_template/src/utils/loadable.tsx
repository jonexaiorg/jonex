import React from 'react'
import loadable from '@loadable/component'
import { Spin } from 'antd'

const retryImport = (fn: () => Promise<unknown>, retries = 2, interval = 1000): Promise<unknown> =>
  new Promise((resolve, reject) => {
    fn()
      .then(resolve)
      .catch((err) => {
        if (retries <= 0) {
          reject(err)
          return
        }
        setTimeout(() => {
          retryImport(fn, retries - 1, interval).then(resolve, reject)
        }, interval)
      })
  })

const SpinnerFallback = () => (
  <Spin
    style={{
      position: 'absolute',
      left: '50%',
      top: '50%',
      transform: 'translate(-50%,-50%)',
    }}
    size="large"
  />
)

interface LoadableOptions {
  retries?: number
  interval?: number
  fallback?: React.ReactNode
}

const loadableComponent = (loader: () => Promise<unknown>, options: LoadableOptions = {}) =>
  (loadable as any)(
    () => retryImport(loader, options.retries ?? 2, options.interval ?? 1000),
    {
      fallback: options.fallback ?? <SpinnerFallback />,
    },
  )

declare global {
  interface Window {
    __CHUNK_LOAD_HANDLER_INSTALLED?: boolean
  }
}

if (typeof window !== 'undefined' && !window.__CHUNK_LOAD_HANDLER_INSTALLED) {
  window.__CHUNK_LOAD_HANDLER_INSTALLED = true

  window.addEventListener('error', (event) => {
    try {
      const message = event?.message || ''
      const isChunkLoadFailed =
        message.includes('Loading chunk') ||
        message.includes('Loading module') ||
        message.includes('Failed to fetch dynamically imported module')

      if (isChunkLoadFailed) {
        console.warn(
          '[loadable] chunk load failed, reloading page for latest assets',
          message,
        )
        setTimeout(() => {
          window.location.reload()
        }, 500)
      }
    } catch (e) {

    }
  })
}

export default loadableComponent
