import React, { useCallback, useState } from 'react';
import { Modal, message } from 'antd';
import { useTranslation } from 'react-i18next';
import { getDocumentViewTicket } from '@/api/domainKnowledge';

// 全平台统一的文档查看器：音视频/图片/PDF/文本全部在弹层内预览，
// 视频/音频支持按时间点定位（time_start）。底层统一走 getDocumentViewTicket
// → /documents/{id}/view-ticket → /documents/{id}/raw（cos 302 预签名 / local FileResponse Range）。

export type ViewerMediaType = 'text' | 'pdf' | 'audio' | 'video' | 'image' | 'other';

const VIDEO_EXTS = new Set(['mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'webm', 'm4v', 'mpg', 'mpeg', '3gp']);
const AUDIO_EXTS = new Set(['mp3', 'wav', 'flac', 'aac', 'm4a', 'ogg', 'wma', 'opus', 'amr']);
const IMAGE_EXTS = new Set(['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif', 'webp']);
const PDF_EXTS = new Set(['pdf']);
const TEXT_EXTS = new Set(['txt', 'md', 'markdown', 'json', 'csv', 'log', 'xml', 'yaml', 'yml']);

/** 由文件名扩展名推断媒体类型（未显式传入 mediaType 时使用）。 */
export function inferMediaType(fileNameOrType: string): ViewerMediaType {
  const raw = (fileNameOrType || '').toLowerCase();
  const ext = raw.includes('.') ? raw.split('.').pop()! : raw;
  if (VIDEO_EXTS.has(ext)) return 'video';
  if (AUDIO_EXTS.has(ext)) return 'audio';
  if (IMAGE_EXTS.has(ext)) return 'image';
  if (PDF_EXTS.has(ext)) return 'pdf';
  if (TEXT_EXTS.has(ext)) return 'text';
  return 'other';
}

interface OpenOptions {
  docId: string;
  fileName: string;
  /** 媒体类型；不传则按 fileName 扩展名推断 */
  mediaType?: ViewerMediaType;
  /** 视频/音频定位起点（秒） */
  timeStart?: number | null;
  /** 视频/音频定位终点（秒） */
  timeEnd?: number | null;
}

interface ViewerState {
  open: boolean;
  kind: ViewerMediaType;
  url: string;
  name: string;
  timeStart?: number | null;
  timeEnd?: number | null;
}

const INITIAL: ViewerState = { open: false, kind: 'other', url: '', name: '' };

/**
 * 统一文档查看 hook。返回 openDocument(打开查看) 和 viewer(需渲染到页面的弹层节点)。
 */
export function useDocumentViewer() {
  const { t } = useTranslation();
  const [state, setState] = useState<ViewerState>(INITIAL);

  const openDocument = useCallback((opts: OpenOptions) => {
    const kind = opts.mediaType ?? inferMediaType(opts.fileName);
    const timeStart = opts.timeStart ?? null;
    const timeEnd = opts.timeEnd ?? null;
    getDocumentViewTicket(opts.docId)
      .then(({ url }) => {
        const sep = url.includes('?') ? '&' : '?';
        let finalUrl = url;
        if (kind === 'video' || kind === 'audio') {
          // 音视频：直连 COS（Range 流式最优），带时间锚点 fragment 定位
          if (timeStart != null) {
            finalUrl = `${url}#t=${timeStart}${timeEnd != null ? `,${timeEnd}` : ''}`;
          }
        } else if (kind === 'pdf' || kind === 'text' || kind === 'other') {
          // iframe 内嵌：走同源代理，规避 COS 跨域 CSP(frame-src) / X-Frame-Options
          finalUrl = `${url}${sep}proxy=1`;
        }
        // image 直连即可
        setState({ open: true, kind, url: finalUrl, name: opts.fileName, timeStart, timeEnd });
      })
      .catch((err: any) => message.error(err?.message || t('common.openDocumentFailed')));
  }, []);

  const close = useCallback(() => setState((s) => ({ ...s, open: false })), []);

  const seekOnLoad = (el: HTMLVideoElement | HTMLAudioElement) => {
    if (state.timeStart != null) {
      try {
        el.currentTime = state.timeStart;
      } catch {
        /* ignore seek error */
      }
    }
  };

  const isFrame = state.kind === 'pdf' || state.kind === 'text' || state.kind === 'other';
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
        // pdf / text / other：iframe 内嵌预览（浏览器按 Content-Type 渲染）
        <iframe src={state.url} title={state.name} style={{ width: '100%', height: '80vh', border: 'none' }} />
      )}
    </Modal>
  );

  return { openDocument, viewer, close };
}
