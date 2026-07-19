import React, { useCallback, useState } from 'react'
import { Modal, message } from 'antd'
import { useTranslation } from 'react-i18next'
import { getDocumentViewTicket } from '@/api/domainKnowledge'





export type ViewerMediaType = 'text' | 'pdf' | 'audio' | 'video' | 'image' | 'other'

const VIDEO_EXTS = new Set(['mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'webm', 'm4v', 'mpg', 'mpeg', '3gp'])
const AUDIO_EXTS = new Set(['mp3', 'wav', 'flac', 'aac', 'm4a', 'ogg', 'wma', 'opus', 'amr'])
const IMAGE_EXTS = new Set(['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif', 'webp'])
const PDF_EXTS = new Set(['pdf'])
const TEXT_EXTS = new Set(['txt', 'md', 'markdown', 'json', 'csv', 'log', 'xml', 'yaml', 'yml'])


export function inferMediaType(fileNameOrType: string): ViewerMediaType {
  const raw = (fileNameOrType || '').toLowerCase()
  const ext = raw.includes('.') ? raw.split('.').pop()! : raw
  if (VIDEO_EXTS.has(ext)) return 'video'
  if (AUDIO_EXTS.has(ext)) return 'audio'
  if (IMAGE_EXTS.has(ext)) return 'image'
  if (PDF_EXTS.has(ext)) return 'pdf'
  if (TEXT_EXTS.has(ext)) return 'text'
  return 'other'
}

interface OpenOptions {
  docId: string
  fileName: string

  mediaType?: ViewerMediaType

  timeStart?: number | null

  timeEnd?: number | null
}

interface ViewerState {
  open: boolean
  kind: ViewerMediaType
  url: string
  name: string
  timeStart?: number | null
  timeEnd?: number | null
}

const INITIAL: ViewerState = { open: false, kind: 'other', url: '', name: '' }




export function useDocumentViewer() {
  const { t } = useTranslation()
  const [state, setState] = useState<ViewerState>(INITIAL)

  const openDocument = useCallback((opts: OpenOptions) => {
    const kind = opts.mediaType ?? inferMediaType(opts.fileName)
    const timeStart = opts.timeStart ?? null
    const timeEnd = opts.timeEnd ?? null
    getDocumentViewTicket(opts.docId)
      .then(({ url }) => {
        const sep = url.includes('?') ? '&' : '?'
        let finalUrl = url
        if (kind === 'video' || kind === 'audio') {

          if (timeStart != null) {
            finalUrl = `${url}#t=${timeStart}${timeEnd != null ? `,${timeEnd}` : ''}`
          }
        } else if (kind === 'pdf' || kind === 'text' || kind === 'other') {

          finalUrl = `${url}${sep}proxy=1`
        }

        setState({ open: true, kind, url: finalUrl, name: opts.fileName, timeStart, timeEnd })
      })
      .catch((err: any) => message.error(err?.message || t('documentViewer.openFailed')))
  }, [])

  const close = useCallback(() => setState((s) => ({ ...s, open: false })), [])

  const seekOnLoad = (el: HTMLVideoElement | HTMLAudioElement) => {
    if (state.timeStart != null) {
      try {
        el.currentTime = state.timeStart
      } catch {

      }
    }
  }

  const isFrame = state.kind === 'pdf' || state.kind === 'text' || state.kind === 'other'
  const viewer = (
    <Modal
      open={state.open}
      title={state.name}
      footer={null}
      width={state.kind === 'audio' ? 520 : isFrame ? 960 : 820}
      onCancel={close}
      destroyOnHidden
      styles={{ body: { padding: isFrame ? 0 : 24 } }}
    >
      {state.kind === 'video' ? (
        <video
          src={state.url}
          controls
          autoPlay
          style={{ width: '100%', maxHeight: '70vh' }}
          onLoadedMetadata={(e) => seekOnLoad(e.currentTarget)}
        />
      ) : state.kind === 'audio' ? (
        <audio
          src={state.url}
          controls
          autoPlay
          style={{ width: '100%' }}
          onLoadedMetadata={(e) => seekOnLoad(e.currentTarget)}
        />
      ) : state.kind === 'image' ? (
        <div style={{ textAlign: 'center' }}>
          <img src={state.url} alt={state.name} style={{ maxWidth: '100%', maxHeight: '70vh' }} />
        </div>
      ) : (

        <iframe
          src={state.url}
          title={state.name}
          style={{ width: '100%', height: '80vh', border: 'none' }}
        />
      )}
    </Modal>
  )

  return { openDocument, viewer, close }
}
