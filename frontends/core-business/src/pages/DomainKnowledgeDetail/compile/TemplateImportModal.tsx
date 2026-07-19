import React, { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Modal, Select, Table, message } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import type { SaveOntologyObjectPayload, SaveOntologyRelationPayload } from '@/types/domainKnowledge'
import {
  fetchTemplateDomains,
  fetchTemplateScenarios,
  fetchTemplateObjects,
  fetchTemplateRelations,
  type TemplateDomain,
  type TemplateScenario,
  type TemplateObject,
  type TemplateRelation,
} from '@/api/templateImport'
import { importOntologyObjectsFromTemplate, importOntologyRelationsFromTemplate } from '@/api/domainKnowledge'
import { normalizeAttrType, normalizeRelationType } from './constants'

interface Props {
  open: boolean
  mode: 'object' | 'relation'
  kbId: string
  onClose: () => void
  onImported: () => void
}

interface ObjectRow extends TemplateObject {
  scenarioName: string
}

interface RelationRow extends TemplateRelation {
  scenarioName: string
}

export default function TemplateImportModal({ open, mode, kbId, onClose, onImported }: Props) {
  const { t } = useTranslation()
  const [domains, setDomains] = useState<TemplateDomain[]>([])
  const [scenarios, setScenarios] = useState<TemplateScenario[]>([])
  const [domainId, setDomainId] = useState<string | undefined>()
  const [scenarioIds, setScenarioIds] = useState<string[]>([])
  const [objectRows, setObjectRows] = useState<ObjectRow[]>([])
  const [relationRows, setRelationRows] = useState<RelationRow[]>([])
  const [selectedKeys, setSelectedKeys] = useState<React.Key[]>([])
  const [loadingDomains, setLoadingDomains] = useState(false)
  const [loadingScenarios, setLoadingScenarios] = useState(false)
  const [loadingRows, setLoadingRows] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const scenarioNameMap = useMemo(() => new Map(scenarios.map((s) => [s.id, s.name])), [scenarios])

  useEffect(() => {
    if (!open) return
    setDomainId(undefined)
    setScenarios([])
    setScenarioIds([])
    setObjectRows([])
    setRelationRows([])
    setSelectedKeys([])
    setLoadingDomains(true)
    fetchTemplateDomains()
      .then((r) => setDomains(r.items || []))
      .catch((e) => message.error(e?.message || t('compile.templateDomainLoadFailed')))
      .finally(() => setLoadingDomains(false))
  }, [open])

  useEffect(() => {
    if (!open) return
    setScenarioIds([])
    setObjectRows([])
    setRelationRows([])
    setSelectedKeys([])
    if (!domainId) {
      setScenarios([])
      return
    }
    setLoadingScenarios(true)
    fetchTemplateScenarios(domainId)
      .then((r) => setScenarios(r.items || []))
      .catch((e) => message.error(e?.message || t('compile.templateScenarioLoadFailed')))
      .finally(() => setLoadingScenarios(false))
  }, [open, domainId])

  useEffect(() => {
    if (!open) return
    setSelectedKeys([])
    if (scenarioIds.length === 0) {
      setObjectRows([])
      setRelationRows([])
      return
    }
    setLoadingRows(true)
    if (mode === 'object') {
      Promise.all(
        scenarioIds.map((sid) =>
          fetchTemplateObjects(sid).then((r) => (r.items || []).map((o) => ({ ...o, scenarioName: scenarioNameMap.get(sid) || sid }))),
        ),
      )
        .then((lists) => setObjectRows(lists.flat()))
        .catch((e) => message.error(e?.message || t('compile.templateObjectLoadFailed')))
        .finally(() => setLoadingRows(false))
    } else {
      Promise.all(
        scenarioIds.map((sid) =>
          fetchTemplateRelations(sid).then((r) => (r.items || []).map((rel) => ({ ...rel, scenarioName: scenarioNameMap.get(sid) || sid }))),
        ),
      )
        .then((lists) => setRelationRows(lists.flat()))
        .catch((e) => message.error(e?.message || t('compile.templateRelationLoadFailed')))
        .finally(() => setLoadingRows(false))
    }
  }, [open, mode, scenarioIds, scenarioNameMap])

  const objectColumns: ColumnsType<ObjectRow> = [
    { title: 'Name', dataIndex: 'name', key: 'name', render: (v) => <strong>{v}</strong> },
    { title: t('domainService.description'), dataIndex: 'description', key: 'description', render: (v) => v || '—' },
    { title: 'Attributes', key: 'attrCount', width: 90, render: (_, r) => r.attributes?.length || 0 },
    { title: 'Source Scenario', dataIndex: 'scenarioName', key: 'scenarioName', width: 140 },
  ]

  const relationColumns: ColumnsType<RelationRow> = [
    { title: 'Source Object', key: 'src', width: 120, render: (_, r) => r.source_object_name || '—' },
    { title: t('ontology.relationName'), dataIndex: 'name', key: 'name', render: (v) => <strong>{v}</strong> },
    { title: 'Target Object', key: 'tgt', width: 120, render: (_, r) => r.target_object_name || '—' },
    { title: t('ontology.relation'), dataIndex: 'relation_type', key: 'relation_type', width: 90 },
    { title: 'Source Scenario', dataIndex: 'scenarioName', key: 'scenarioName', width: 140 },
  ]

  const handleImport = async () => {
    setSubmitting(true)
    try {
      if (mode === 'object') {
        const picked = objectRows.filter((r) => selectedKeys.includes(r.id))
        const payloads: SaveOntologyObjectPayload[] = picked.map((o) => ({
          name: o.name,
          description: o.description || '',
          requirement: '',
          status: 'active',
          attributes: (o.attributes || []).map((a) => ({
            id: '',
            name: a.attr_name,
            description: a.description || '',
            type: normalizeAttrType(a.attr_type),
            isPrimaryKey: a.is_primary_key === true || a.is_primary_key === 1,
          })),
        }))
        const { created, skipped } = await importOntologyObjectsFromTemplate(kbId, payloads)
        message.success(t('compile.importObjectSuccess', { created: created.length, skippedText: skipped ? `, ${skipped} existing items skipped` : '' }))
      } else {
        const picked = relationRows.filter((r) => selectedKeys.includes(r.id))
        const payloads: SaveOntologyRelationPayload[] = picked.map((r) => ({
          sourceObject: r.source_object_name || '(Unknown Source Object)',
          name: r.name,
          targetObject: r.target_object_name || '(Unknown Target Object)',
          description: r.description || '',
          relationType: normalizeRelationType(r.relation_type),
          status: 'active',
        }))
        const { created, skipped } = await importOntologyRelationsFromTemplate(kbId, payloads)
        message.success(t('compile.importRelationSuccess', { created: created.length, skippedText: skipped ? `, ${skipped} existing items skipped` : '' }))
      }
      onImported()
      onClose()
    } catch (e: any) {
      message.error(e?.message || t('compile.importFailed'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal
      title={mode === 'object' ? 'Import Objects from Template Scenario' : 'Import Relations from Template Scenario'}
      open={open}
      onCancel={onClose}
      onOk={handleImport}
      okText={t('compile.importObjects')}
      cancelText={t('dataSource.cancel')}
      confirmLoading={submitting}
      okButtonProps={{ disabled: selectedKeys.length === 0 }}
      width={760}
      destroyOnHidden
    >
      <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
        <Select
          style={{ width: 220 }}
          placeholder={t('compile.selectDomain')}
          loading={loadingDomains}
          allowClear
          value={domainId}
          onChange={(v) => setDomainId(v)}
          options={domains.map((d) => ({ label: d.name, value: d.id }))}
        />
        <Select
          style={{ flex: 1 }}
          mode="multiple"
          placeholder={t('compile.selectScenario')}
          loading={loadingScenarios}
          value={scenarioIds}
          onChange={(v) => setScenarioIds(v)}
          disabled={!domainId}
          options={scenarios.map((s) => ({ label: s.name, value: s.id }))}
        />
      </div>
      {mode === 'object' ? (
        <Table
          rowKey="id"
          size="small"
          loading={loadingRows}
          pagination={false}
          columns={objectColumns}
          dataSource={objectRows}
          rowSelection={{ selectedRowKeys: selectedKeys, onChange: setSelectedKeys }}
          locale={{ emptyText: t('compile.selectObjects') }}
          scroll={{ y: 320 }}
        />
      ) : (
        <Table
          rowKey="id"
          size="small"
          loading={loadingRows}
          pagination={false}
          columns={relationColumns}
          dataSource={relationRows}
          rowSelection={{ selectedRowKeys: selectedKeys, onChange: setSelectedKeys }}
          locale={{ emptyText: t('compile.selectRelations') }}
          scroll={{ y: 320 }}
        />
      )}
    </Modal>
  )
}
