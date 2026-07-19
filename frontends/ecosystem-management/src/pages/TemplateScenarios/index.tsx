import { useCallback, useEffect, useMemo, useState } from 'react'
import type { MouseEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { Button, Checkbox, Form, Input, Modal, Select, Table, Tag, message } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  ArrowLeftOutlined,
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ProfileOutlined,
  ReloadOutlined,
  SafetyOutlined,
  ShareAltOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import {
  createTemplateConstraint,
  createTemplateObject,
  createTemplateRelation,
  createTemplateScenario,
  deleteTemplateConstraint,
  deleteTemplateObject,
  deleteTemplateRelation,
  deleteTemplateScenario,
  fetchTemplateConstraints,
  fetchTemplateDomains,
  fetchTemplateObjects,
  fetchTemplateRelations,
  fetchTemplateScenarios,
  updateTemplateConstraint,
  updateTemplateObject,
  updateTemplateRelation,
  updateTemplateScenario,
} from '../../api/templateScenarios'
import type {
  TemplateAttribute,
  TemplateConstraint,
  TemplateDomain,
  TemplateObject,
  TemplateRelation,
  TemplateScenario,
} from '../../api/templateScenarios'
import './index.css'

type AttributeFormItem = {
  id?: string
  name?: string
  desc?: string
  type?: string
  isPrimary?: boolean
}

type SceneFormValues = {
  name: string
  desc?: string
  domainId: string
}

type ObjectFormValues = {
  name: string
  desc?: string
  attrs?: AttributeFormItem[]
}

type RelationFormValues = {
  sourceObjectId?: string
  relation: string
  targetObjectId?: string
  desc?: string
  type: string
}

type DeletingItem =
  | { type: 'scene'; item: TemplateScenario }
  | { type: 'object'; item: TemplateObject }
  | { type: 'relation'; item: TemplateRelation }
  | { type: 'constraint'; item: TemplateConstraint }

const ATTRIBUTE_TYPE_OPTIONS = [
  { label: 'templateScenario.attributeTypeString', value: '字符串' },
  { label: 'templateScenario.attributeTypeNumber', value: '数值' },
  { label: 'templateScenario.attributeTypeDate', value: '日期' },
  { label: 'templateScenario.attributeTypeEnum', value: '枚举' },
  { label: 'templateScenario.attributeTypeBoolean', value: '布尔' },
  { label: 'templateScenario.attributeTypeText', value: '文本' },
]

const RELATION_TYPE_OPTIONS = [
  { label: 'templateScenario.relationTypeOneToOne', value: '一对一' },
  { label: 'templateScenario.relationTypeOneToMany', value: '一对多' },
  { label: 'templateScenario.relationTypeManyToOne', value: '多对一' },
  { label: 'templateScenario.relationTypeManyToMany', value: '多对多' },
]

function formatTime(value?: string | null) {
  if (!value) return '-'
  const parsed = dayjs(value)
  return parsed.isValid() ? parsed.format('YYYY-MM-DD HH:mm') : value
}

function createDraftId(prefix: string) {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`
}

function isPrimaryKey(value: TemplateAttribute['is_primary_key']) {
  return value === true || value === 1
}

function getErrorMessage(error: unknown, fallback: string) {
  const err = error as { response?: { data?: { message?: string } }; message?: string }
  return err.response?.data?.message || err.message || fallback
}

export default function TemplateScenarios() {
  const { t } = useTranslation()
  const [domains, setDomains] = useState<TemplateDomain[]>([])
  const [scenes, setScenes] = useState<TemplateScenario[]>([])
  const [objects, setObjects] = useState<TemplateObject[]>([])
  const [relations, setRelations] = useState<TemplateRelation[]>([])
  const [constraints, setConstraints] = useState<TemplateConstraint[]>([])
  const navigate = useNavigate()
  const [domainFilter, setDomainFilter] = useState('')
  const [selectedSceneId, setSelectedSceneId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'objects' | 'relations' | 'constraints'>('objects')

  const [loadingDomains, setLoadingDomains] = useState(false)
  const [loadingScenes, setLoadingScenes] = useState(false)
  const [loadingDetails, setLoadingDetails] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const [sceneModalOpen, setSceneModalOpen] = useState(false)
  const [objectModalOpen, setObjectModalOpen] = useState(false)
  const [relationModalOpen, setRelationModalOpen] = useState(false)
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [editingScene, setEditingScene] = useState<TemplateScenario | null>(null)
  const [editingObject, setEditingObject] = useState<TemplateObject | null>(null)
  const [editingRelation, setEditingRelation] = useState<TemplateRelation | null>(null)
  const [deletingItem, setDeletingItem] = useState<DeletingItem | null>(null)

  const [sceneForm] = Form.useForm<SceneFormValues>()
  const [objectForm] = Form.useForm<ObjectFormValues>()
  const [relationForm] = Form.useForm<RelationFormValues>()

  const domainNameMap = useMemo(() => {
    return new Map(domains.map((domain) => [domain.id, domain.name]))
  }, [domains])

  const domainOptions = useMemo(() => {
    return domains.map((domain) => ({ label: domain.name, value: domain.id }))
  }, [domains])

  const selectedScene = useMemo(() => {
    return scenes.find((scene) => scene.id === selectedSceneId) ?? null
  }, [scenes, selectedSceneId])

  const objectSelectOptions = useMemo(() => {
    return objects.map((item) => ({ label: item.name, value: item.id }))
  }, [objects])

  const getDomainName = useCallback(
    (domainId: string) => domainNameMap.get(domainId) || domainId || '-',
    [domainNameMap],
  )

  const getObjectName = useCallback(
    (objectId?: string | null) => objects.find((item) => item.id === objectId)?.name || objectId || '-',
    [objects],
  )

  const refreshScenarios = useCallback(async (nextDomainId = '', preferredSceneId?: string | null) => {
    setLoadingScenes(true)
    try {
      const result = await fetchTemplateScenarios(nextDomainId || undefined)
      const items = result.items ?? []
      const nextSelected =
        preferredSceneId && items.some((scene) => scene.id === preferredSceneId)
          ? preferredSceneId
          : items[0]?.id ?? null
      setScenes(items)
      setSelectedSceneId(nextSelected)
      if (!nextSelected) {
        setObjects([])
        setRelations([])
      }
      return nextSelected
    } catch (error) {
      message.error(getErrorMessage(error, t('templateScenario.loadFailed')))
      setScenes([])
      setSelectedSceneId(null)
      setObjects([])
      setRelations([])
      return null
    } finally {
      setLoadingScenes(false)
    }
  }, [])

  const refreshTemplateDetails = useCallback(async (sceneId: string | null) => {
    if (!sceneId) {
      setObjects([])
      setRelations([])
      setConstraints([])
      return
    }

    setLoadingDetails(true)
    try {
      const [objectResult, relationResult, constraintResult] = await Promise.all([
        fetchTemplateObjects(sceneId),
        fetchTemplateRelations(sceneId),
        fetchTemplateConstraints(sceneId),
      ])
      setObjects(objectResult.items ?? [])
      setRelations(relationResult.items ?? [])
      setConstraints(constraintResult.items ?? [])
    } catch (error) {
      message.error(getErrorMessage(error, t('common.loadFailed')))
      setObjects([])
      setRelations([])
    } finally {
      setLoadingDetails(false)
    }
  }, [])

  useEffect(() => {
    setLoadingDomains(true)
    fetchTemplateDomains()
      .then((result) => setDomains(result.items ?? []))
      .catch((error) => message.error(getErrorMessage(error, t('common.loadFailed'))))
      .finally(() => setLoadingDomains(false))

    void refreshScenarios('')
  }, [refreshScenarios])

  useEffect(() => {
    void refreshTemplateDetails(selectedSceneId)
  }, [refreshTemplateDetails, selectedSceneId])

  const objectColumns: ColumnsType<TemplateObject> = [
    {
      title: t('templateScenario.name'),
      dataIndex: 'name',
      key: 'name',
      width: 160,
      render: (text) => <strong>{text}</strong>,
    },
    {
      title: t('templateScenario.description'),
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text) => text || <span className="template-scenarios-muted">{t('templateScenario.noDescription')}</span>,
    },
    {
      title: t('templateScenario.attributes'),
      dataIndex: 'attributes',
      key: 'attributes',
      width: 340,
      render: (attrs: TemplateAttribute[]) =>
        attrs.length > 0 ? (
          <table className="template-scenarios-attr-inline">
            <thead>
              <tr>
                <th>{t('templateScenario.attrName')}</th>
                <th>{t('templateScenario.attrType')}</th>
                <th>{t('templateScenario.attrPrimaryKey')}</th>
              </tr>
            </thead>
            <tbody>
              {attrs.map((attr) => (
                <tr key={attr.id}>
                  <td>{attr.attr_name}</td>
                  <td>{attr.attr_type}</td>
                  <td>{isPrimaryKey(attr.is_primary_key) ? <span className="template-scenarios-key-mark">✓</span> : null}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <span className="template-scenarios-muted">{t('templateScenario.noAttributes')}</span>
        ),
    },
    {
      title: t('templateScenario.createdAt'),
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: formatTime,
    },
    {
      title: t('templateScenario.actions'),
      key: 'action',
      width: 170,
      render: (_, record) => (
        <span className="template-scenarios-table-actions">
          <a className="yx-table-action" onClick={() => openEditObject(record)}>
            <EditOutlined /> {t('templateScenario.edit')}
          </a>
          <a className="yx-table-action template-scenarios-danger-link" onClick={() => openDeleteObject(record)}>
            <DeleteOutlined /> {t('templateScenario.delete')}
          </a>
        </span>
      ),
    },
  ]

  const relationColumns: ColumnsType<TemplateRelation> = [
    {
      title: t('templateScenario.source'),
      dataIndex: 'source_object_name',
      key: 'source_object_name',
      width: 140,
      render: (text, record) => <Tag color="processing">{text || getObjectName(record.source_object_id)}</Tag>,
    },
    {
      title: t('templateScenario.relationName'),
      dataIndex: 'name',
      key: 'name',
      width: 130,
      render: (text) => <strong>{text}</strong>,
    },
    {
      title: t('templateScenario.target'),
      dataIndex: 'target_object_name',
      key: 'target_object_name',
      width: 140,
      render: (text, record) => <Tag color="success">{text || getObjectName(record.target_object_id)}</Tag>,
    },
    {
      title: t('templateScenario.description'),
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text) => text || <span className="template-scenarios-muted">{t('templateScenario.noDescription')}</span>,
    },
    {
      title: t('templateScenario.relationType'),
      dataIndex: 'relation_type',
      key: 'relation_type',
      width: 110,
      render: (text) => <Tag>{text}</Tag>,
    },
    {
      title: t('templateScenario.actions'),
      key: 'action',
      width: 170,
      render: (_, record) => (
        <span className="template-scenarios-table-actions">
          <a className="yx-table-action" onClick={() => openEditRelation(record)}>
            <EditOutlined /> {t('templateScenario.edit')}
          </a>
          <a className="yx-table-action template-scenarios-danger-link" onClick={() => openDeleteRelation(record)}>
            <DeleteOutlined /> {t('templateScenario.delete')}
          </a>
        </span>
      ),
    },
  ]


  const [constraintModalOpen, setConstraintModalOpen] = useState(false)
  const [editingConstraint, setEditingConstraint] = useState<TemplateConstraint | null>(null)
  const [constraintForm, setConstraintForm] = useState({
    name: '',
    target_type: 'object' as string,
    target_id: '',
    constraint_type: 'unique' as string,
    expression: '',
    suggestion: '',
  })

  const CONSTRAINT_TARGET_TYPE_OPTIONS = [
    { label: t('templateScenario.constraintTargetObject'), value: 'object' },
    { label: t('templateScenario.constraintTargetAttribute'), value: 'attribute' },
    { label: t('templateScenario.constraintTargetRelation'), value: 'relation' },
  ]
  const CONSTRAINT_TYPE_OPTIONS = [
    { label: t('templateScenario.constraintTypeUnique'), value: 'unique' },
    { label: t('templateScenario.constraintTypeExists'), value: 'exists' },
    { label: t('templateScenario.constraintTypeConditional'), value: 'conditional' },
    { label: t('templateScenario.constraintTypeRange'), value: 'range' },
  ]

  const constraintTargetOptions = useMemo(() => {
    if (constraintForm.target_type === 'object') {
      return objects.map((o) => ({ label: o.name, value: o.id }))
    }
    if (constraintForm.target_type === 'relation') {
      return relations.map((r) => ({
        label: `${r.source_object_name || r.source_object_id} → ${r.target_object_name || r.target_object_id} (${r.name})`,
        value: r.id,
      }))
    }
    if (constraintForm.target_type === 'attribute') {
      const flat: Array<{ label: string; value: string }> = []
      objects.forEach((o) => {
        o.attributes?.forEach((a) => {
          flat.push({ label: `${o.name}.${a.attr_name}`, value: a.id })
        })
      })
      return flat
    }
    return []
  }, [constraintForm.target_type, objects, relations])

  const constraintColumns: ColumnsType<TemplateConstraint> = [
    { title: t('templateScenario.constraintName'), dataIndex: 'name', key: 'name', width: 160 },
    {
      title: t('templateScenario.constraintTargetType'), dataIndex: 'target_type', key: 'target_type', width: 120,
      render: (type: string) => {
        const labelMap: Record<string, string> = { object: t('templateScenario.constraintTargetObject'), attribute: t('templateScenario.constraintTargetAttribute'), relation: t('templateScenario.constraintTargetRelation') }
        return <Tag>{labelMap[type] || type}</Tag>
      },
    },
    { title: t('templateScenario.targetObject'), dataIndex: 'target_label', key: 'target_label', width: 160 },
    {
      title: t('templateScenario.constraintType'), dataIndex: 'constraint_type', key: 'constraint_type', width: 100,
      render: (type: string) => {
        const labelMap: Record<string, string> = { unique: t('templateScenario.constraintTypeUnique'), exists: t('templateScenario.constraintTypeExists'), conditional: t('templateScenario.constraintTypeConditional'), range: t('templateScenario.constraintTypeRange') }
        return <Tag color="blue">{labelMap[type] || type}</Tag>
      },
    },
    {
      title: t('templateScenario.constraintExpression'), dataIndex: 'expression', key: 'expression', width: 160,
      render: (text) => text ? <code style={{ fontSize: 12 }}>{text}</code> : '-',
    },
    {
      title: t('templateScenario.constraintSuggestion'), dataIndex: 'suggestion', key: 'suggestion',
      ellipsis: true,
      render: (text) => text || '-',
    },
    {
      title: t('templateScenario.actions'), key: 'action', width: 140,
      render: (_, record) => (
        <span className="template-scenarios-table-actions">
          <a className="yx-table-action" onClick={() => openEditConstraint(record)}>
            <EditOutlined /> {t('templateScenario.edit')}
          </a>
          <a className="yx-table-action template-scenarios-danger-link" onClick={() => openDeleteConstraint(record)}>
            <DeleteOutlined /> {t('templateScenario.delete')}
          </a>
        </span>
      ),
    },
  ]

  function openCreateConstraint() {
    setEditingConstraint(null)
    setConstraintForm({ name: '', target_type: 'object', target_id: '', constraint_type: 'unique', expression: '', suggestion: '' })
    setConstraintModalOpen(true)
  }

  function openEditConstraint(c: TemplateConstraint) {
    setEditingConstraint(c)
    setConstraintForm({
      name: c.name,
      target_type: c.target_type,
      target_id: c.target_id,
      constraint_type: c.constraint_type,
      expression: c.expression || '',
      suggestion: c.suggestion || '',
    })
    setConstraintModalOpen(true)
  }

  async function saveConstraint() {
    if (!constraintForm.name.trim()) { message.warning(t('templateScenario.constraintNameRequired')); return }
    if (!constraintForm.target_id) { message.warning(t('templateScenario.constraintTargetRequired')); return }
    setSubmitting(true)
    try {
      const payload = {
        name: constraintForm.name.trim(),
        target_type: constraintForm.target_type,
        target_id: constraintForm.target_id,
        constraint_type: constraintForm.constraint_type,
        expression: constraintForm.expression || undefined,
        suggestion: constraintForm.suggestion || undefined,
      }
      if (editingConstraint) {
        await updateTemplateConstraint(editingConstraint.id, payload)
        message.success(t('templateScenario.updateConstraintSuccess'))
      } else {
        await createTemplateConstraint(selectedSceneId!, payload)
        message.success(t('templateScenario.createConstraintSuccess'))
      }
      setConstraintModalOpen(false)
      await refreshTemplateDetails(selectedSceneId)
    } catch (error) {
      message.error(getErrorMessage(error, t('templateScenario.saveFailed', { type: t('templateScenario.constraint') })))
    } finally {
      setSubmitting(false)
    }
  }

  function openDeleteConstraint(c: TemplateConstraint) {
    setDeletingItem({ type: 'constraint', item: c })
    setDeleteModalOpen(true)
  }



  async function handleDomainFilterChange(value?: string) {
    const nextFilter = value ?? ''
    setDomainFilter(nextFilter)
    setActiveTab('objects')
    await refreshScenarios(nextFilter)
  }

  function openCreateScene() {
    if (domainOptions.length === 0) {
      message.warning(t('templateScenario.waitCreateDomain'))
      return
    }
    setEditingScene(null)
    sceneForm.setFieldsValue({
      name: '',
      desc: '',
      domainId: domainFilter || domainOptions[0].value,
    })
    setSceneModalOpen(true)
  }

  function openEditScene(scene: TemplateScenario, event?: MouseEvent) {
    event?.stopPropagation()
    setEditingScene(scene)
    sceneForm.setFieldsValue({
      name: scene.name,
      desc: scene.description || '',
      domainId: scene.domain_id,
    })
    setSceneModalOpen(true)
  }

  async function saveScene() {
    const values = await sceneForm.validateFields()
    const payload = {
      name: values.name.trim(),
      description: values.desc?.trim() || '',
      domain_id: values.domainId,
    }

    setSubmitting(true)
    try {
      if (editingScene) {
        const saved = await updateTemplateScenario(editingScene.id, payload)
        const nextFilter = domainFilter && saved.domain_id !== domainFilter ? '' : domainFilter
        if (nextFilter !== domainFilter) {
          setDomainFilter(nextFilter)
        }
        await refreshScenarios(nextFilter, saved.id)
        message.success(t('templateScenario.updateSuccess'))
      } else {
        const created = await createTemplateScenario(payload)
        setDomainFilter(created.domain_id)
        await refreshScenarios(created.domain_id, created.id)
        message.success(t('templateScenario.createSuccess'))
      }
      setSceneModalOpen(false)
    } catch (error) {
      message.error(getErrorMessage(error, t('common.operationFailed')))
    } finally {
      setSubmitting(false)
    }
  }

  function openDeleteScene(scene: TemplateScenario, event?: MouseEvent) {
    event?.stopPropagation()
    setDeletingItem({ type: 'scene', item: scene })
    setDeleteModalOpen(true)
  }

  function openCreateObject() {
    if (!selectedSceneId) return
    setEditingObject(null)
    objectForm.setFieldsValue({
      name: '',
      desc: '',
      attrs: [{ id: createDraftId('attr'), name: '', desc: '', type: '字符串', isPrimary: false }],
    })
    setObjectModalOpen(true)
  }

  function openEditObject(item: TemplateObject) {
    setEditingObject(item)
    objectForm.setFieldsValue({
      name: item.name,
      desc: item.description || '',
      attrs: item.attributes.map((attr) => ({
        id: attr.id,
        name: attr.attr_name,
        desc: attr.description || '',
        type: attr.attr_type,
        isPrimary: isPrimaryKey(attr.is_primary_key),
      })),
    })
    setObjectModalOpen(true)
  }

  async function saveObject() {
    if (!selectedSceneId) return
    const values = await objectForm.validateFields()
    const attributes = (values.attrs || []).map((attr, index) => ({
      attr_name: attr.name?.trim() || '',
      description: attr.desc?.trim() || '',
      attr_type: attr.type || '字符串',
      is_primary_key: Boolean(attr.isPrimary),
      sort_order: index,
    }))

    setSubmitting(true)
    try {
      if (editingObject) {
        await updateTemplateObject(editingObject.id, {
          name: values.name.trim(),
          description: values.desc?.trim() || '',
          attributes,
        })
        message.success(t('templateScenario.updateObjectSuccess'))
      } else {
        await createTemplateObject(selectedSceneId, {
          name: values.name.trim(),
          description: values.desc?.trim() || '',
          attributes,
        })
        message.success(t('templateScenario.createObjectSuccess'))
      }
      await refreshTemplateDetails(selectedSceneId)
      setObjectModalOpen(false)
    } catch (error) {
      message.error(getErrorMessage(error, t('common.operationFailed')))
    } finally {
      setSubmitting(false)
    }
  }

  function openDeleteObject(item: TemplateObject) {
    setDeletingItem({ type: 'object', item })
    setDeleteModalOpen(true)
  }

  function openCreateRelation() {
    if (!selectedSceneId) return
    if (objects.length === 0) {
      message.warning(t('templateScenario.waitCreateObject'))
      return
    }
    setEditingRelation(null)
    relationForm.setFieldsValue({
      sourceObjectId: undefined,
      relation: '',
      targetObjectId: undefined,
      desc: '',
      type: RELATION_TYPE_OPTIONS[1].value,
    })
    setRelationModalOpen(true)
  }

  function openEditRelation(item: TemplateRelation) {
    setEditingRelation(item)
    relationForm.setFieldsValue({
      sourceObjectId: item.source_object_id,
      relation: item.name,
      targetObjectId: item.target_object_id,
      desc: item.description || '',
      type: item.relation_type,
    })
    setRelationModalOpen(true)
  }

  async function saveRelation() {
    if (!selectedSceneId) return
    const values = await relationForm.validateFields()
    if (!values.sourceObjectId || !values.targetObjectId) return

    setSubmitting(true)
    try {
      const payload = {
        source_object_id: values.sourceObjectId,
        target_object_id: values.targetObjectId,
        name: values.relation.trim(),
        description: values.desc?.trim() || '',
        relation_type: values.type,
      }
      if (editingRelation) {
        await updateTemplateRelation(editingRelation.id, payload)
        message.success(t('templateScenario.updateRelationSuccess'))
      } else {
        await createTemplateRelation(selectedSceneId, payload)
        message.success(t('templateScenario.createRelationSuccess'))
      }
      await refreshTemplateDetails(selectedSceneId)
      setRelationModalOpen(false)
    } catch (error) {
      message.error(getErrorMessage(error, t('common.operationFailed')))
    } finally {
      setSubmitting(false)
    }
  }

  function openDeleteRelation(item: TemplateRelation) {
    setDeletingItem({ type: 'relation', item })
    setDeleteModalOpen(true)
  }

  async function confirmDelete() {
    if (!deletingItem) return

    setSubmitting(true)
    try {
      if (deletingItem.type === 'scene') {
        await deleteTemplateScenario(deletingItem.item.id)
        await refreshScenarios(domainFilter, selectedSceneId === deletingItem.item.id ? null : selectedSceneId)
        message.success(t('templateScenario.deleteSceneSuccess'))
      }

      if (deletingItem.type === 'object') {
        await deleteTemplateObject(deletingItem.item.id)
        await refreshTemplateDetails(selectedSceneId)
        message.success(t('templateScenario.deleteObjectMsg'))
      }

      if (deletingItem.type === 'relation') {
        await deleteTemplateRelation(deletingItem.item.id)
        await refreshTemplateDetails(selectedSceneId)
        message.success(t('templateScenario.deleteRelationMsg'))
      }

      if (deletingItem.type === 'constraint') {
        await deleteTemplateConstraint(deletingItem.item.id)
        await refreshTemplateDetails(selectedSceneId)
        message.success(t('templateScenario.deleteConstraintMsg'))
      }

      setDeleteModalOpen(false)
      setDeletingItem(null)
    } catch (error) {
      message.error(getErrorMessage(error, t('common.deleteFailed')))
    } finally {
      setSubmitting(false)
    }
  }

  async function refreshCurrentView() {
    const nextSelected = await refreshScenarios(domainFilter, selectedSceneId)
    if (nextSelected) {
      await refreshTemplateDetails(nextSelected)
    }
  }

  const deleteTitle =
    deletingItem?.type === 'scene'
      ? t('templateScenario.delete')
      : deletingItem?.type === 'object'
        ? t('templateObject.delete')
        : deletingItem?.type === 'constraint'
          ? t('templateScenario.delete')
          : t('templateRelation.delete')
  const deleteName =
    deletingItem?.type === 'scene'
      ? deletingItem.item.name
      : deletingItem?.type === 'object'
        ? deletingItem.item.name
        : deletingItem?.item.name

  return (
    <div className="template-scenarios-page">
      <div className="yx-page-title">
        <Button
          type="link"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/template-domains')}
          style={{ paddingLeft: 0, marginBottom: 4 }}
        >
          {t('templateScenario.backToDomains')}
        </Button>
        <h1>{t('templateScenario.title')}</h1>
        <p className="yx-page-subtitle">{t('templateScenario.subtitle')}</p>
      </div>

      <div className="yx-card template-scenarios-card">
        <div className="template-scenarios-split">
          <aside className="template-scenarios-left">
            <div className="template-scenarios-left-title">
              <h2>{t('templateScenario.scenes')}</h2>
              <span>{t('templateScenario.sceneCount', { count: scenes.length })}</span>
            </div>

            <Select
              className="template-scenarios-domain-filter"
              placeholder={t('templateScenario.allDomains')}
              value={domainFilter || undefined}
              onChange={handleDomainFilterChange}
              allowClear
              loading={loadingDomains}
              options={domainOptions}
            />

            <ul className="template-scenarios-list">
              {loadingScenes ? <li className="template-scenarios-no-scene">{t('templateScenario.loadingScenes')}</li> : null}
              {!loadingScenes && scenes.length === 0 ? (
                <li className="template-scenarios-no-scene">{t('templateScenario.noMatchingScenes')}</li>
              ) : null}
              {!loadingScenes &&
                scenes.map((scene) => (
                  <li
                    key={scene.id}
                    className={scene.id === selectedSceneId ? 'active' : ''}
                    onClick={() => {
                      setSelectedSceneId(scene.id)
                      setActiveTab('objects')
                    }}
                  >
                    <div className="template-scenarios-item-main">
                      <div className="template-scenarios-item-name">{scene.name}</div>
                      <div className="template-scenarios-item-meta">{formatTime(scene.created_at)}</div>
                      <Tag className="template-scenarios-domain-tag">{getDomainName(scene.domain_id)}</Tag>
                    </div>
                    <div className="template-scenarios-item-actions">
                      <Button
                        type="text"
                        size="small"
                        icon={<EditOutlined />}
                        aria-label={t('templateScenario.edit')}
                        onClick={(event) => openEditScene(scene, event)}
                      />
                      <Button
                        type="text"
                        danger
                        size="small"
                        icon={<DeleteOutlined />}
                        aria-label={t('templateScenario.delete')}
                        onClick={(event) => openDeleteScene(scene, event)}
                      />
                    </div>
                  </li>
                ))}
            </ul>

            <Button
              className="template-scenarios-create-scene"
              type="primary"
              icon={<PlusOutlined />}
              block
              onClick={openCreateScene}
            >
              {t('templateScenario.createScene')}
            </Button>
          </aside>

          <section className="template-scenarios-right">
            {!selectedScene ? (
              <>
                <div className="template-scenarios-right-header">
                  <h2>{t('templateScenario.selectScene')}</h2>
                  <Button icon={<ReloadOutlined />} onClick={refreshCurrentView} loading={loadingScenes}>
                    {t('common.refresh')}
                  </Button>
                </div>
                <div className="yx-empty-state template-scenarios-empty">{t('templateScenario.selectSceneHint')}</div>
              </>
            ) : (
              <>
                <div className="template-scenarios-right-header">
                  <div>
                    <h2>{selectedScene.name}</h2>
                    <p className="yx-page-subtitle">{selectedScene.description || t('templateScenario.noSceneDescription')}</p>
                  </div>
                  <Button icon={<ReloadOutlined />} onClick={refreshCurrentView} loading={loadingScenes || loadingDetails}>
                    {t('common.refresh')}
                  </Button>
                </div>

                <div className="yx-tabs template-scenarios-tabs">
                  <button
                    type="button"
                    className={`yx-tab ${activeTab === 'objects' ? 'active' : ''}`}
                    onClick={() => setActiveTab('objects')}
                  >
                    <ProfileOutlined />
                    {t('templateScenario.objectTemplates')}
                  </button>
                  <button
                    type="button"
                    className={`yx-tab ${activeTab === 'relations' ? 'active' : ''}`}
                    onClick={() => setActiveTab('relations')}
                  >
                    <ShareAltOutlined />
                    {t('templateScenario.relationTemplates')}
                  </button>
                  <button
                    type="button"
                    className={`yx-tab ${activeTab === 'constraints' ? 'active' : ''}`}
                    onClick={() => setActiveTab('constraints')}
                  >
                    <SafetyOutlined />
                    {t('templateScenario.constraintTemplates')}
                  </button>
                </div>

                <p className="template-scenarios-tab-note" style={{ color: '#94a3b8', fontSize: 12, marginTop: 8 }}>
                  {activeTab === 'constraints'
                    ? t('templateScenario.constraintNote')
                    : t('templateScenario.detailNote')}
                </p>

                {activeTab === 'objects' && (
                  <div>
                    <div className="template-scenarios-tab-toolbar">
                      <Button type="primary" icon={<PlusOutlined />} onClick={openCreateObject}>
                        {t('templateScenario.createObject')}
                      </Button>
                    </div>
                    <Table
                      className="yx-data-table"
                      dataSource={objects}
                      columns={objectColumns}
                      rowKey="id"
                      loading={loadingDetails}
                      pagination={false}
                      locale={{ emptyText: t('templateScenario.noObjects') }}
                    />
                  </div>
                )}
                {activeTab === 'relations' && (
                  <div>
                    <div className="template-scenarios-tab-toolbar">
                      <Button type="primary" icon={<PlusOutlined />} onClick={openCreateRelation}>
                        {t('templateScenario.createRelation')}
                      </Button>
                    </div>
                    <Table
                      className="yx-data-table"
                      dataSource={relations}
                      columns={relationColumns}
                      rowKey="id"
                      loading={loadingDetails}
                      pagination={false}
                      locale={{ emptyText: t('templateScenario.noRelations') }}
                    />
                  </div>
                )}
                {activeTab === 'constraints' && (
                  <div>
                    <div className="template-scenarios-tab-toolbar">
                      <Button type="primary" icon={<PlusOutlined />} onClick={openCreateConstraint}>
                        {t('templateScenario.createConstraint')}
                      </Button>
                    </div>
                    <Table
                      dataSource={constraints}
                      columns={constraintColumns}
                      rowKey="id"
                      loading={loadingDetails}
                      pagination={false}
                      locale={{ emptyText: t('templateScenario.noConstraints') }}
                    />
                  </div>
                )}
              </>
            )}
          </section>
        </div>
      </div>

      <Modal
        title={editingScene ? t('templateScenario.edit') : t('templateScenario.create')}
        open={sceneModalOpen}
        onCancel={() => setSceneModalOpen(false)}
        onOk={saveScene}
        okText={t('common.save')}
        cancelText={t('common.cancel')}
        confirmLoading={submitting}
        width={560}
      >
        <Form form={sceneForm} layout="vertical" className="template-scenarios-form">
          <Form.Item label={t('templateScenario.name')} name="name" rules={[{ required: true, whitespace: true, message: t('templateScenario.nameRequired') }]}>
            <Input placeholder={t('templateScenario.name')} />
          </Form.Item>
          <Form.Item label={t('templateScenario.description')} name="desc">
            <Input.TextArea placeholder={t('templateScenario.description')} rows={3} />
          </Form.Item>
          <Form.Item label={t('templateScenario.domainLabel')} name="domainId" rules={[{ required: true, message: t('templateScenario.pleaseSelectDomain') }]}>
            <Select placeholder={t('templateScenario.selectDomain')} loading={loadingDomains} options={domainOptions} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={editingObject ? t('templateScenario.editObject') : t('templateScenario.createObject')}
        open={objectModalOpen}
        onCancel={() => setObjectModalOpen(false)}
        onOk={saveObject}
        okText={t('common.save')}
        cancelText={t('common.cancel')}
        confirmLoading={submitting}
        width={820}
      >
        <Form form={objectForm} layout="vertical" className="template-scenarios-form">
          <Form.Item label={t('templateScenario.name')} name="name" rules={[{ required: true, whitespace: true, message: t('templateScenario.nameRequired') }]}>
            <Input placeholder={t('templateScenario.name')} />
          </Form.Item>
          <Form.Item label={t('templateScenario.description')} name="desc">
            <Input.TextArea placeholder={t('templateScenario.description')} rows={3} />
          </Form.Item>
          <Form.List name="attrs">
            {(fields, { add, remove }) => (
              <div className="template-scenarios-attr-editor">
                <div className="template-scenarios-attr-editor-head">
                  <label>{t('templateScenario.attributes')}</label>
                  <Button
                    type="dashed"
                    size="small"
                    icon={<PlusOutlined />}
                    onClick={() =>
                      add({ id: createDraftId('attr'), name: '', desc: '', type: '字符串', isPrimary: false })
                    }
                  >
                    {t('templateScenario.addAttribute')}
                  </Button>
                </div>
                {fields.map((field) => (
                  <div className="template-scenarios-attr-row" key={field.key}>
                    <Form.Item name={[field.name, 'id']} hidden>
                      <Input />
                    </Form.Item>
                    <Form.Item
                      name={[field.name, 'name']}
                      rules={[{ required: true, whitespace: true, message: t('templateScenario.attrNameRequired') }]}
                    >
                      <Input placeholder={t('templateScenario.attrName')} />
                    </Form.Item>
                    <Form.Item name={[field.name, 'desc']}>
                      <Input placeholder={t('templateScenario.description')} />
                    </Form.Item>
                    <Form.Item name={[field.name, 'type']}>
                      <Select options={ATTRIBUTE_TYPE_OPTIONS.map(o => ({ ...o, label: t(o.label) }))} />
                    </Form.Item>
                    <Form.Item name={[field.name, 'isPrimary']} valuePropName="checked">
                      <Checkbox>{t('templateScenario.attrPrimaryKey')}</Checkbox>
                    </Form.Item>
                    <Button danger type="text" icon={<DeleteOutlined />} onClick={() => remove(field.name)} />
                  </div>
                ))}
              </div>
            )}
          </Form.List>
        </Form>
      </Modal>

      <Modal
        title={editingRelation ? t('templateScenario.edit') : t('templateScenario.create')}
        open={relationModalOpen}
        onCancel={() => setRelationModalOpen(false)}
        onOk={saveRelation}
        okText={t('common.save')}
        cancelText={t('common.cancel')}
        confirmLoading={submitting}
        width={640}
      >
        <Form form={relationForm} layout="vertical" className="template-scenarios-form">
          <div className="template-scenarios-relation-grid">
            <Form.Item label={t('templateScenario.source')} name="sourceObjectId" rules={[{ required: true, message: t('templateScenario.sourceRequired') }]}>
              <Select placeholder={t('templateScenario.source')} options={objectSelectOptions} />
            </Form.Item>
            <Form.Item label={t('templateScenario.target')} name="targetObjectId" rules={[{ required: true, message: t('templateScenario.targetRequired') }]}>
              <Select placeholder={t('templateScenario.target')} options={objectSelectOptions} />
            </Form.Item>
          </div>
          <Form.Item
            label={t('templateScenario.relationName')}
            name="relation"
            rules={[{ required: true, whitespace: true, message: t('templateScenario.nameRequired') }]}
          >
            <Input placeholder={t('templateScenario.relationName')} />
          </Form.Item>
          <Form.Item label={t('templateScenario.description')} name="desc">
            <Input.TextArea placeholder={t('templateScenario.description')} rows={3} />
          </Form.Item>
          <Form.Item label={t('templateScenario.relationType')} name="type" rules={[{ required: true, message: t('templateScenario.typeRequired') }]}>
            <Select placeholder={t('templateScenario.relationType')} options={RELATION_TYPE_OPTIONS.map(o => ({ ...o, label: t(o.label) }))} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={editingConstraint ? t('templateScenario.edit') : t('templateScenario.create')}
        open={constraintModalOpen}
        onCancel={() => setConstraintModalOpen(false)}
        onOk={saveConstraint}
        okText={t('common.save')}
        cancelText={t('common.cancel')}
        confirmLoading={submitting}
        width={640}
      >
        <Form layout="vertical" className="template-scenarios-form">
          <Form.Item label={t('templateScenario.constraintName')} required>
            <Input
              placeholder={t('templateScenario.constraintName')}
              value={constraintForm.name}
              onChange={(e) => setConstraintForm({ ...constraintForm, name: e.target.value })}
            />
          </Form.Item>
          <div className="template-scenarios-relation-grid">
            <Form.Item label={t('templateScenario.constraintTargetType')} required>
              <Select
                value={constraintForm.target_type}
                onChange={(v) => setConstraintForm({ ...constraintForm, target_type: v, target_id: '' })}
                options={CONSTRAINT_TARGET_TYPE_OPTIONS}
              />
            </Form.Item>
            <Form.Item label={t('templateScenario.targetObject')} required>
              <Select
                placeholder={t('templateScenario.targetObject')}
                value={constraintForm.target_id || undefined}
                onChange={(v) => setConstraintForm({ ...constraintForm, target_id: v || '' })}
                options={constraintTargetOptions}
                showSearch
                filterOption={(input, option) =>
                  (option?.label as string)?.toLowerCase().includes(input.toLowerCase())
                }
              />
            </Form.Item>
          </div>
          <Form.Item label={t('templateScenario.constraintType')} required>
            <Select
              value={constraintForm.constraint_type}
              onChange={(v) => setConstraintForm({ ...constraintForm, constraint_type: v })}
              options={CONSTRAINT_TYPE_OPTIONS}
            />
          </Form.Item>
          <Form.Item
            label={t('templateScenario.constraintExpression')}
            required={constraintForm.constraint_type === 'conditional' || constraintForm.constraint_type === 'range'}
          >
            <Input.TextArea
              placeholder={t('templateScenario.constraintExpression')}
              value={constraintForm.expression}
              onChange={(e) => setConstraintForm({ ...constraintForm, expression: e.target.value })}
              rows={3}
            />
          </Form.Item>
          <Form.Item label={t('templateScenario.constraintSuggestion')}>
            <Input.TextArea
              placeholder={t('templateScenario.constraintSuggestionPlaceholder')}
              value={constraintForm.suggestion}
              onChange={(e) => setConstraintForm({ ...constraintForm, suggestion: e.target.value })}
              rows={2}
            />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={deleteTitle}
        open={deleteModalOpen}
        onCancel={() => setDeleteModalOpen(false)}
        onOk={confirmDelete}
        okText={t('common.confirmDelete')}
        cancelText={t('common.cancel')}
        confirmLoading={submitting}
        okButtonProps={{ danger: true }}
        width={420}
      >
        <div className="template-scenarios-delete-content">
          {t('templateScenario.confirmDeleteItem', { name: deleteName })}
        </div>
      </Modal>
    </div>
  )
}
