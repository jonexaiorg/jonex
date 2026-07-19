import React, { useState, useEffect, useCallback } from 'react'
import { Input, Button, Table, Tag, Select, Space, Spin, Result, Modal, DatePicker } from 'antd'
import { useTranslation } from 'react-i18next'
import { SearchOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { listAuditLogs, getAuditLog, type AuditLogItem } from '../../api/auditLogs'

const { RangePicker } = DatePicker

const ACTION_LABELS: Record<string, { label: string; color: string }> = {
  create: { label: 'operationLog.create', color: 'green' }, update: { label: 'operationLog.update', color: 'blue' },
  delete: { label: 'operationLog.delete', color: 'red' }, login: { label: 'operationLog.login', color: 'cyan' },
  logout: { label: 'operationLog.logout', color: 'default' }, search: { label: 'operationLog.search', color: 'blue' },
  upload: { label: 'operationLog.upload', color: 'purple' }, connect: { label: 'operationLog.connect', color: 'green' },
  disconnect: { label: 'operationLog.disconnect', color: 'orange' },
}

export default function OperationLog() {
  const { t } = useTranslation()
  const [logs, setLogs] = useState<AuditLogItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [keyword, setKeyword] = useState('')
  const [action, setAction] = useState<string | undefined>()
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null)
  const [detailItem, setDetailItem] = useState<AuditLogItem | null>(null)

  const load = useCallback(async (p = 1) => {
    setLoading(true); setError(null)
    try {
      const r = await listAuditLogs({
        page: p, page_size: 15, action: action || undefined,
        start_time: dateRange?.[0]?.startOf('day').toISOString(),
        end_time: dateRange?.[1]?.endOf('day').toISOString(),
      })
      setLogs(r.items); setTotal(r.total); setPage(p)
    } catch (e: unknown) { setError(e instanceof Error ? e.message : t('common.loadFailed')) }
    finally { setLoading(false) }
  }, [action, dateRange, t])

  useEffect(() => { load(1) }, [load])

  const filtered = keyword
    ? logs.filter(l => (l.action || '').includes(keyword) || (l.username || '').includes(keyword) || (l.resource || '').includes(keyword))
    : logs

  const showDetail = async (id: number) => {
    try { const d = await getAuditLog(id); setDetailItem(d) } catch {   }
  }

  const columns = [
    { title: t('operationLog.createdAt'), dataIndex: 'created_at', key: 'created_at', width: 170, render: (v: string | null) => v || '--' },
    { title: t('operationLog.action'), dataIndex: 'action', key: 'action', width: 90, render: (v: string) => { const a = ACTION_LABELS[v] || { label: v, color: 'default' }; return <Tag color={a.color}>{t(a.label)}</Tag> } },
    { title: t('operationLog.target'), dataIndex: 'resource', key: 'resource', width: 100 },
    { title: t('operationLog.operator'), dataIndex: 'username', key: 'username', width: 90 },
    { title: t('operationLog.ip'), dataIndex: 'ip', key: 'ip', width: 120 },
    { title: t('operationLog.duration', '耗时'), dataIndex: 'duration_ms', key: 'duration_ms', width: 70, render: (v: number | null) => v ? `${v}ms` : '--' },
    { title: t('operationLog.actions'), key: 'detail', width: 60, render: (_: unknown, r: AuditLogItem) => <a className="yx-table-action" onClick={() => showDetail(r.id)}>{t('operationLog.detail')}</a> },
  ]

  if (error) return <Result status="error" title={t('common.loadFailed')} subTitle={error} extra={<Button type="primary" onClick={() => load(1)}>{t('common.retry', '重试')}</Button>} />

  return (
    <div>
      <div className="yx-page-title"><h1>{t('operationLog.title')}</h1></div>
      <div className="yx-card">
        <Space style={{ marginBottom: 16 }} wrap>
          <Input prefix={<SearchOutlined />} placeholder={t('operationLog.searchPlaceholder', '搜索用户/资源...')} style={{ width: 180 }} value={keyword} onChange={e => setKeyword(e.target.value)} allowClear />
          <Select placeholder={t('status.allStatus')} style={{ width: 110 }} value={action} onChange={v => setAction(v)} allowClear
            options={Object.entries(ACTION_LABELS).map(([k, v]) => ({ label: t(v.label), value: k }))} />
          <RangePicker value={dateRange} onChange={v => setDateRange(v as [dayjs.Dayjs, dayjs.Dayjs] | null)} allowClear style={{ width: 240 }} />
          <Button onClick={() => load(1)}>{t('common.refresh', '刷新')}</Button>
        </Space>
        <Table columns={columns} dataSource={filtered} rowKey="id" loading={loading}
          pagination={{ current: page, total, pageSize: 15, onChange: (p) => load(p), showTotal: (n) => t('common.totalPage', { total: n }) }} size="small" />
      </div>

      <Modal title={t('operationLog.detail')} open={!!detailItem} onCancel={() => setDetailItem(null)} footer={null} width={600}>
        {detailItem && (
          <div>
            <p><strong>{t('operationLog.action')}：</strong>{t(ACTION_LABELS[detailItem.action]?.label || detailItem.action)} · <strong>{t('operationLog.target')}：</strong>{detailItem.resource}/{detailItem.resource_id}</p>
            <p><strong>{t('operationLog.operator')}：</strong>{detailItem.username || '--'} · <strong>{t('operationLog.ip')}：</strong>{detailItem.ip || '--'} · <strong>{t('operationLog.duration', '耗时')}：</strong>{detailItem.duration_ms ? `${detailItem.duration_ms}ms` : '--'}</p>
            <p><strong>Trace ID：</strong>{detailItem.trace_id || '--'}</p>
            <p><strong>{t('operationLog.createdAt')}：</strong>{detailItem.created_at}</p>
            {detailItem.detail && <pre style={{ background: '#f8fafc', padding: 12, borderRadius: 8, fontSize: 12, maxHeight: 300, overflow: 'auto' }}>
              {typeof detailItem.detail === 'string' ? detailItem.detail : JSON.stringify(detailItem.detail, null, 2)}
            </pre>}
          </div>
        )}
      </Modal>
    </div>
  )
}