import React, { useEffect, useState } from 'react'
import { Modal, Form, Input, Select, InputNumber, Typography, message, Alert } from 'antd'
import { useTranslation } from 'react-i18next'
import { listAccessMethods, createDataSource } from '@/api/dataSource'
import type { AccessMethodItem, DataSourceInstance } from '@/types/dataSource'

interface Props {
  open: boolean
  kbId: string

  existingTypes: string[]
  onClose: () => void
  onCreated: (ds: DataSourceInstance) => void
}

const RAG_ANYTHING_EXTS = 'pdf,doc,docx,ppt,pptx,xls,xlsx,txt,md,jpg,jpeg,png,gif,bmp,tiff,tif,webp,mp3,wav,flac,aac,m4a,ogg,wma,opus,amr,mp4,avi,mov,mkv,flv,wmv,webm,m4v,mpg,mpeg,3gp'

export default function AddDataSourceModal({ open, kbId, existingTypes, onClose, onCreated }: Props) {
  const { t } = useTranslation()
  const [methods, setMethods] = useState<AccessMethodItem[]>([])
  const [loading, setLoading] = useState(false)
  const [showApiHelp, setShowApiHelp] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [selected, setSelected] = useState<AccessMethodItem | null>(null)
  const [created, setCreated] = useState<DataSourceInstance | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    if (!open) return
    setSelected(null)
    setCreated(null)
    setShowApiHelp(false)
    form.resetFields()
    setLoading(true)
    listAccessMethods()
      .then(setMethods)
      .catch((e: any) => message.error(e?.message || t('dataSource.methodLoadFailed')))
      .finally(() => setLoading(false))
  }, [open, form])


  useEffect(() => {
    if (selected) {
      form.setFieldsValue({ name: selected.name })
    }
  }, [selected, form])


  const existingSet = new Set(existingTypes)
  const availableMethods = methods.filter((m) => !existingSet.has(m.accessType))

  const accessType = selected?.accessType

  function buildConfig(v: any): Record<string, any> {
    if (accessType === 'api') {
      return {
        endpoint: v.endpoint,
        method: v.method || 'GET',
        auth: { type: v.authType || 'none', token: v.token || undefined, header_name: v.headerName || undefined },
        list_path: v.listPath || '$.data.items',
        file_url_field: v.fileUrlField || 'url',
        file_name_field: v.fileNameField || 'name',
      }
    }
    if (accessType === 'storage') {
      return {
        backend: v.backend || 'minio',
        endpoint: v.endpoint || undefined,
        bucket: v.bucket,
        prefix: v.prefix || '',
        region: v.region || undefined,
        credential: v.credential || undefined,
        include_ext: (v.includeExt || '').split(',').map((s: string) => s.trim()).filter(Boolean),
      }
    }
    if (accessType === 'api_push') {
      return {
        allowed_ext: (v.allowedExt || 'pdf,docx,md,txt').split(',').map((s: string) => s.trim()).filter(Boolean),
        max_file_mb: v.maxFileMb || 50,
      }
    }
    if (accessType === 'file') {
      return {}
    }
    return {}
  }

  async function handleCreate() {
    if (!selected) {
      message.warning(t('dataSource.selectMethod'))
      return
    }
    const v = await form.validateFields()
    setSubmitting(true)
    try {
      const ds = await createDataSource({
        knowledge_base_id: kbId,
        access_method_id: selected.id,
        access_type: selected.accessType,
        name: v.name,
        config_json: buildConfig(v),
      })
      if (ds.accessType === 'api_push' && ds.ingestKey) {
        setCreated(ds)
      } else {
        message.success(t('dataSource.methodCreateSuccess'))
        onCreated(ds)
        onClose()
      }
    } catch (e: any) {
      message.error(e?.message || t('dataSource.methodCreateFailed'))
    } finally {
      setSubmitting(false)
    }
  }

  function handleOk() {
    if (created) {
      onCreated(created)
      onClose()
    } else {
      void handleCreate()
    }
  }

  return (
    <Modal
      title={t('dataSource.addDataSource')}
      open={open}
      onCancel={onClose}
      onOk={handleOk}
      okText={created ? t('common.operationSuccessful') : t('domainSpace.create')}
      confirmLoading={submitting}
      width={640}
      destroyOnHidden
    >
      <Select
        style={{ width: '100%', marginBottom: 16 }}
        loading={loading}
        placeholder={t('dataSource.selectMethod')}
        value={selected?.id}
        disabled={!!created}
        notFoundContent={loading ? t('dataSource.loading') : t('dataSource.noMethod')}
        onChange={(id) => setSelected(methods.find((m) => m.id === id) || null)}
        options={availableMethods.map((m) => ({
          label: `${m.name}`,
          value: m.id,
        }))}
      />

      {!created && selected && (
        <Form form={form} layout="vertical">
          <Form.Item label={t('dataSource.name')} name="name" rules={[{ required: true, whitespace: true, message: t('validation.nameRequired') }]}>
            <Input placeholder="For example: Financial Products API" />
          </Form.Item>

          {accessType === 'api' && (
            <>
              <div
                onClick={() => setShowApiHelp((prev) => !prev)}
                style={{
                  cursor: 'pointer', color: '#3b82f6', fontSize: 13,
                  marginBottom: showApiHelp ? 8 : 16,
                  userSelect: 'none',
                }}
              >
                {showApiHelp ? '▼' : '▶'} {t('dataSource.apiSync')}{t('common.config')}
              </div>
              {showApiHelp && (
                <Alert
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                  description={
                    <div style={{ fontSize: 13 }}>
                      <p style={{ margin: '4px 0' }}>
                        Jonex periodically calls the configured endpoint to retrieve and ingest documents.
                      </p>
                      <p style={{ margin: '4px 0' }}>
                        The endpoint must return a <strong>JSON array</strong> whose items include a download URL and file name.
                      </p>
                      <p style={{ margin: '4px 0', color: '#94a3b8' }}>
                        Example response: {`{"code":0,"data":{"items":[{"url":"https://...","name":"report.pdf"},{"url":"https://...","name":"contract.docx"}]}}`}
                      </p>
                    </div>
                  }
                />
              )}
              <Form.Item label={t('dataSource.endpoint')} name="endpoint" rules={[{ required: true, message: t('validation.nameRequired') }]}
                tooltip="Document list endpoint URL. HTTP GET and POST are supported.">
                <Input placeholder="https://api.example.com/documents" />
              </Form.Item>
              <Form.Item label="HTTP Method" name="method" initialValue="GET"
                tooltip="Use GET for most endpoints, or POST when request parameters are required.">
                <Select options={[{ value: 'GET', label: 'GET' }, { value: 'POST', label: 'POST' }]} />
              </Form.Item>
              <Form.Item label={t('dataSource.authType')} name="authType" initialValue="none"
                tooltip="Select the authentication method required by the external endpoint.">
                <Select
                  options={[
                    { value: 'none', label: t('dataSource.noAuth') },
                    { value: 'bearer', label: t('dataSource.bearerAuth') },
                    { value: 'api_key', label: t('dataSource.apiKeyAuth') },
                    { value: 'basic', label: t('dataSource.basicAuth') },
                  ]}
                />
              </Form.Item>
              <Form.Item label="Credential / Token" name="token"
                tooltip="For Bearer use a JWT, for API Key enter the key, and for Basic use user:pass. Credentials are encrypted.">
                <Input.Password placeholder="Enter a credential when required; leave blank for no authentication" />
              </Form.Item>
              <Form.Item label="API Key Header Name" name="headerName"
                tooltip="Required only for API Key authentication. Enter the header expected by the endpoint.">
                <Input placeholder="X-API-Key" />
              </Form.Item>
              <Form.Item label="Document List Path (JSONPath)" name="listPath" initialValue="$.data.items"
                tooltip="Path to the document array in the response. The default $.data.items selects data.items.">
                <Input placeholder="$.data.items" />
              </Form.Item>
              <Form.Item label="Download URL Field" name="fileUrlField" initialValue="url"
                tooltip="Field containing the file download URL.">
                <Input placeholder="url" />
              </Form.Item>
              <Form.Item label="File Name Field" name="fileNameField" initialValue="name"
                tooltip="Field containing the file name and extension.">
                <Input placeholder="name" />
              </Form.Item>
            </>
          )}

          {accessType === 'storage' && (
            <>
              <Form.Item label={t('dataSource.storageType')} name="backend" initialValue="minio">
                <Select options={[
                    { value: 'minio', label: 'MinIO' },
                    { value: 's3', label: 'AWS S3' },
                    { value: 'cos', label: t('dataSource.cos') },
                    { value: 'oss', label: t('dataSource.oss') },
                  ]} />
              </Form.Item>
              <Form.Item label="Endpoint" name="endpoint" tooltip="For MinIO enter http(s)://host:9000. Leave blank for AWS S3.">
                <Input placeholder="http://minio:9000" />
              </Form.Item>
              <Form.Item label={t('dataSource.bucket')} name="bucket" rules={[{ required: true, message: t('validation.nameRequired') }]}>
                <Input placeholder="product-files" />
              </Form.Item>
              <Form.Item label="Prefix" name="prefix">
                <Input placeholder="kb/finance/" />
              </Form.Item>
              <Form.Item label="Region" name="region">
                <Input placeholder={t('domainKnowledge.noSpace')} />
              </Form.Item>
              <Form.Item label={t('dataSource.credential')} name="credential" rules={[{ required: true, message: t('validation.nameRequired') }]}>
                <Input.Password placeholder="accessKey:secretKey" />
              </Form.Item>
              <Form.Item label="Included Extensions (comma-separated)" name="includeExt" initialValue={RAG_ANYTHING_EXTS}>
                <Input.TextArea rows={2} placeholder={RAG_ANYTHING_EXTS} />
              </Form.Item>
            </>
          )}

          {accessType === 'file' && (
            <Alert
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
              description={
                <div style={{ fontSize: 13 }}>
                  <p style={{ margin: '0 0 8px' }}>File upload supports the following formats, detected automatically by the parser:</p>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <tbody>
                      <tr>
                        <td style={{ padding: '2px 8px 2px 0', color: '#64748b', whiteSpace: 'nowrap', verticalAlign: 'top' }}>Documents</td>
                        <td style={{ padding: '2px 0', fontFamily: 'monospace', fontSize: 12 }}>PDF · DOC · DOCX · PPT · PPTX · XLS · XLSX · TXT · MD</td>
                      </tr>
                      <tr>
                        <td style={{ padding: '2px 8px 2px 0', color: '#64748b', whiteSpace: 'nowrap', verticalAlign: 'top' }}>Images</td>
                        <td style={{ padding: '2px 0', fontFamily: 'monospace', fontSize: 12 }}>JPG · JPEG · PNG · GIF · BMP · TIFF · TIF · WEBP</td>
                      </tr>
                      <tr>
                        <td style={{ padding: '2px 8px 2px 0', color: '#64748b', whiteSpace: 'nowrap', verticalAlign: 'top' }}>Audio</td>
                        <td style={{ padding: '2px 0', fontFamily: 'monospace', fontSize: 12 }}>MP3 · WAV · FLAC · AAC · M4A · OGG · WMA · OPUS · AMR</td>
                      </tr>
                      <tr>
                        <td style={{ padding: '2px 8px 2px 0', color: '#64748b', whiteSpace: 'nowrap', verticalAlign: 'top' }}>Video</td>
                        <td style={{ padding: '2px 0', fontFamily: 'monospace', fontSize: 12 }}>MP4 · AVI · MOV · MKV · FLV · WMV · WEBM · M4V · MPG · MPEG · 3GP</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              }
            />
          )}

          {accessType === 'api_push' && (
            <>
              <Form.Item label="Allowed File Types (comma-separated)" name="allowedExt" initialValue={RAG_ANYTHING_EXTS}>
                <Input.TextArea rows={2} placeholder={RAG_ANYTHING_EXTS} />
              </Form.Item>
              <Form.Item label="Maximum File Size (MB)" name="maxFileMb" initialValue={50}>
                <InputNumber min={1} max={500} style={{ width: '100%' }} />
              </Form.Item>
            </>
          )}
        </Form>
      )}

      {created && (
        <Alert
          type="success"
          showIcon
          title={t('dataSource.methodCreateSuccess')}
          description={
            <div>
              <div style={{ marginBottom: 8 }}>
                {t('dataSource.endpoint')}：
                <Typography.Text copyable>{created.ingestUrl}</Typography.Text>
              </div>
              <div>
                {t('dataSource.keyValueDisplay')}：
                <Typography.Text copyable code>
                  {created.ingestKey}
                </Typography.Text>
              </div>
            </div>
          }
        />
      )}
    </Modal>
  )
}
