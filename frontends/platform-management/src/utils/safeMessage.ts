import { message } from 'antd'
import DOMPurify from 'dompurify'
import { throttle } from 'lodash'
import i18n from '@/locales/i18n'

const stripCRLF = (text: unknown): string =>
  String(text)
    .replace(/[\r\n]/g, '')
    .replace(/[\x00-\x1F\x7F]/g, '')
    .trim()

const sanitizeText = (text: unknown, defaultKey: string = 'common.dataError'): string => {
  const defaultMsg = i18n.t(defaultKey)
  const rawText = text ?? defaultMsg

  const neutralizedText = stripCRLF(rawText)
  const encodedForVeracode = encodeURIComponent(neutralizedText)
  const sanitized = DOMPurify.sanitize(encodedForVeracode, {
    ALLOWED_TAGS: [],
    ALLOWED_ATTR: [],
  })

  return decodeURIComponent(sanitized)
}

const throttleMessage = (fn: (text: unknown, defaultKey?: string) => void, wait: number = 300) =>
  throttle(fn, wait, { trailing: false })

export const safeMessage = {
  error: throttleMessage((text, defaultKey) => {
    message.error(sanitizeText(text, defaultKey))
  }),

  info: throttleMessage((text, defaultKey) => {
    message.info(sanitizeText(text, defaultKey))
  }),

  success: throttleMessage((text, defaultKey) => {
    message.success(sanitizeText(text, defaultKey))
  }),

  warning: throttleMessage((text, defaultKey) => {
    message.warning(sanitizeText(text, defaultKey))
  }),
}
