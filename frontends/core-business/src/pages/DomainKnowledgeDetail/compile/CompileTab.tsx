import React, { useCallback, useEffect, useState } from 'react'
import { Modal, Tabs, message } from 'antd'
import { useTranslation } from 'react-i18next'
import type {
  OntologyObjectDef,
  OntologyRelationDef,
  OntologyConstraint,
  CompileStep,
  EngineSetting,
  SaveOntologyObjectPayload,
  SaveOntologyRelationPayload,
  SaveOntologyConstraintPayload,
  SaveCompileStepPayload,
} from '@/types/domainKnowledge'
import {
  getOntologyObjects,
  createOntologyObject,
  updateOntologyObject,
  deleteOntologyObject,
  getOntologyRelations,
  createOntologyRelation,
  updateOntologyRelation,
  deleteOntologyRelation,
  getOntologyConstraints,
  createOntologyConstraint,
  updateOntologyConstraint,
  deleteOntologyConstraint,
  getConstraintTargetOptions,
  type ConstraintTargetOptions,
  getCompileSteps,
  createCompileStep,
  updateCompileStep,
  deleteCompileStep,
  getEngineSetting,
  saveEngineSetting,
} from '@/api/domainKnowledge'
import OntologyObjectSection from './OntologyObjectSection'
import OntologyRelationSection from './OntologyRelationSection'
import OntologyConstraintSection from './OntologyConstraintSection'
import CompileStepSection from './CompileStepSection'
import EngineBasicSection from './EngineBasicSection'
import ObjectFormModal from './ObjectFormModal'
import RelationFormModal from './RelationFormModal'
import ConstraintFormModal from './ConstraintFormModal'
import StepFormModal from './StepFormModal'
import PromptViewModal from './PromptViewModal'
import TemplateImportModal from './TemplateImportModal'

interface Props {
  kbId: string
}

const EMPTY_TARGET_OPTIONS: ConstraintTargetOptions = { entity: [], attribute: [], relation: [] }
const PROMPT_STATUS_TEXT = { active: 'Enabled', inactive: 'Disabled' } as const

function buildObjectPrompt(o: OntologyObjectDef): string {
  let t = `You are a domain ontology extraction expert. Extract entity instances matching the “${o.name}” ontology definition from the following document.\n\n`
  t += `Ontology Name: ${o.name}\n`
  t += `Ontology Description: ${o.description || 'None'}\n`
  t += `Attribute Definitions:\n`
  o.attributes.forEach((a, i) => {
    t += `${i + 1}. ${a.name} (${a.type})${a.isPrimaryKey ? ' [Primary Key]' : ''}\n`
  })
  t += `\nAdditional Requirements: ${o.requirement || 'None'}\n`
  t += `Status: ${PROMPT_STATUS_TEXT[o.status]}`
  return t
}

function buildRelationPrompt(r: OntologyRelationDef): string {
  let t = `You are a domain ontology relation extraction expert. Extract relation instances matching the “${r.name}” definition from the following document.\n\n`
  t += `Source Object: ${r.sourceObject}\n`
  t += `Relation Name: ${r.name}\n`
  t += `Target Object: ${r.targetObject}\n`
  t += `Relation Description: ${r.description || 'None'}\n`
  t += `Relation Type: ${r.relationType}\n`
  t += `Status: ${PROMPT_STATUS_TEXT[r.status]}`
  return t
}

export default function CompileTab({ kbId }: Props) {
  const { t } = useTranslation()
  const [activeSubTab, setActiveSubTab] = useState('obj')
  const [objects, setObjects] = useState<OntologyObjectDef[]>([])
  const [relations, setRelations] = useState<OntologyRelationDef[]>([])
  const [constraints, setConstraints] = useState<OntologyConstraint[]>([])
  const [targetOptions, setTargetOptions] = useState<ConstraintTargetOptions>(EMPTY_TARGET_OPTIONS)
  const [steps, setSteps] = useState<CompileStep[]>([])
  const [engine, setEngine] = useState<EngineSetting | null>(null)
  const [loadingObjects, setLoadingObjects] = useState(false)
  const [loadingRelations, setLoadingRelations] = useState(false)
  const [loadingConstraints, setLoadingConstraints] = useState(false)
  const [loadingSteps, setLoadingSteps] = useState(false)
  const [loadingEngine, setLoadingEngine] = useState(false)

  const [objectModal, setObjectModal] = useState<{ open: boolean; editing: OntologyObjectDef | null }>({ open: false, editing: null })
  const [relationModal, setRelationModal] = useState<{ open: boolean; editing: OntologyRelationDef | null }>({ open: false, editing: null })
  const [constraintModal, setConstraintModal] = useState<{ open: boolean; editing: OntologyConstraint | null }>({ open: false, editing: null })
  const [stepModal, setStepModal] = useState<{ open: boolean; editing: CompileStep | null }>({ open: false, editing: null })
  const [promptModal, setPromptModal] = useState<{ open: boolean; title: string; desc: string; content: string }>({ open: false, title: '', desc: '', content: '' })
  const [importModal, setImportModal] = useState<{ open: boolean; mode: 'object' | 'relation' }>({ open: false, mode: 'object' })
  const [submitting, setSubmitting] = useState(false)

  const loadObjects = useCallback(() => {
    setLoadingObjects(true)
    getOntologyObjects(kbId).then(setObjects).catch((e) => message.error(e?.message || t('common.loadFailed'))).finally(() => setLoadingObjects(false))
  }, [kbId])

  const loadRelations = useCallback(() => {
    setLoadingRelations(true)
    getOntologyRelations(kbId).then(setRelations).catch((e) => message.error(e?.message || t('common.loadFailed'))).finally(() => setLoadingRelations(false))
  }, [kbId])

  const loadConstraints = useCallback(() => {
    setLoadingConstraints(true)
    getOntologyConstraints(kbId).then(setConstraints).catch((e) => message.error(e?.message || t('common.loadFailed'))).finally(() => setLoadingConstraints(false))
  }, [kbId])

  const loadTargetOptions = useCallback(() => {
    getConstraintTargetOptions(kbId).then(setTargetOptions).catch(() => setTargetOptions(EMPTY_TARGET_OPTIONS))
  }, [kbId])

  const loadSteps = useCallback(() => {
    setLoadingSteps(true)
    getCompileSteps(kbId).then(setSteps).catch((e) => message.error(e?.message || t('common.loadFailed'))).finally(() => setLoadingSteps(false))
  }, [kbId])

  const loadEngine = useCallback(() => {
    setLoadingEngine(true)
    getEngineSetting(kbId).then(setEngine).catch((e) => message.error(e?.message || t('common.loadFailed'))).finally(() => setLoadingEngine(false))
  }, [kbId])

  useEffect(() => {
    loadObjects()
    loadRelations()
    loadConstraints()
    loadTargetOptions()
    loadSteps()
    loadEngine()
  }, [loadObjects, loadRelations, loadConstraints, loadTargetOptions, loadSteps, loadEngine])


  const reloadCompiledSchema = useCallback(() => {
    loadObjects()
    loadRelations()
    loadConstraints()
    loadTargetOptions()
  }, [loadObjects, loadRelations, loadConstraints, loadTargetOptions])

  const handleSaveError = (e: any, fallback: string) => {
    const msg = e?.message || fallback
    message.error(msg)

    if (typeof msg === 'string' && msg.includes('已被更新')) {
      reloadCompiledSchema()
    }
  }

  const submitObject = async (payload: SaveOntologyObjectPayload) => {
    setSubmitting(true)
    try {
      if (objectModal.editing) {
        await updateOntologyObject(kbId, objectModal.editing.id, payload)
        message.success(t('compile.objectUpdated'))
      } else {
        await createOntologyObject(kbId, payload)
        message.success(t('compile.objectCreated'))
      }
      setObjectModal({ open: false, editing: null })
      reloadCompiledSchema()
    } catch (e: any) {
      handleSaveError(e, t('compile.objectLoadFailed'))
    } finally {
      setSubmitting(false)
    }
  }

  const removeObject = (o: OntologyObjectDef) => {
    Modal.confirm({
      title: t('compile.objects'),
      content: `Delete object “${o.name}”? This cannot be undone. Related relations and constraints will also be removed.`,
      okText: 'Delete',
      cancelText: 'Cancel',
      okButtonProps: { danger: true },
      onOk: async () => {
        try {
          await deleteOntologyObject(kbId, o.id)
          message.success(t('compile.objectDeleted'))
          reloadCompiledSchema()
        } catch (e: any) {
          handleSaveError(e, t('compile.objectLoadFailed'))
        }
      },
    })
  }

  const submitRelation = async (payload: SaveOntologyRelationPayload) => {
    setSubmitting(true)
    try {
      if (relationModal.editing) {
        await updateOntologyRelation(kbId, relationModal.editing.id, payload)
        message.success(t('compile.relationUpdated'))
      } else {
        await createOntologyRelation(kbId, payload)
        message.success(t('compile.relationCreated'))
      }
      setRelationModal({ open: false, editing: null })
      reloadCompiledSchema()
    } catch (e: any) {
      handleSaveError(e, t('compile.relationLoadFailed'))
    } finally {
      setSubmitting(false)
    }
  }

  const removeRelation = (r: OntologyRelationDef) => {
    Modal.confirm({
      title: t('compile.relations'),
      content: `Delete relation “${r.name}”? This cannot be undone. Related constraints will also be removed.`,
      okText: 'Delete',
      cancelText: 'Cancel',
      okButtonProps: { danger: true },
      onOk: async () => {
        try {
          await deleteOntologyRelation(kbId, r.id)
          message.success(t('compile.relationDeleted'))
          reloadCompiledSchema()
        } catch (e: any) {
          handleSaveError(e, t('compile.relationLoadFailed'))
        }
      },
    })
  }

  const submitConstraint = async (payload: SaveOntologyConstraintPayload) => {
    setSubmitting(true)
    try {
      if (constraintModal.editing) {
        await updateOntologyConstraint(kbId, constraintModal.editing.id, payload)
        message.success(t('compile.constraintUpdated'))
      } else {
        await createOntologyConstraint(kbId, payload)
        message.success(t('compile.constraintCreated'))
      }
      setConstraintModal({ open: false, editing: null })
      loadConstraints()
    } catch (e: any) {
      handleSaveError(e, 'Failed to save constraint')
    } finally {
      setSubmitting(false)
    }
  }

  const removeConstraint = (c: OntologyConstraint) => {
    Modal.confirm({
      title: t('compile.constraints'),
      content: `Delete constraint “${c.name}”? This action cannot be undone.`,
      okText: 'Delete',
      cancelText: 'Cancel',
      okButtonProps: { danger: true },
      onOk: async () => {
        try {
          await deleteOntologyConstraint(kbId, c.id)
          message.success(t('compile.constraintDeleted'))
          loadConstraints()
        } catch (e: any) {
          handleSaveError(e, 'Failed to delete constraint')
        }
      },
    })
  }

  const submitStep = async (payload: SaveCompileStepPayload) => {
    setSubmitting(true)
    try {
      if (stepModal.editing) {
        await updateCompileStep(kbId, stepModal.editing.id, payload)
        message.success(t('compile.stepUpdated'))
      } else {
        await createCompileStep(kbId, payload)
        message.success(t('compile.stepCreated'))
      }
      setStepModal({ open: false, editing: null })
      loadSteps()
    } catch (e: any) {
      message.error(e?.message || t('compile.stepSaveFailed'))
    } finally {
      setSubmitting(false)
    }
  }

  const removeStep = (s: CompileStep) => {
    Modal.confirm({
      title: t('compile.stepDeleted'),
      content: `Delete step “${s.name}”? This action cannot be undone.`,
      okText: t('validation.confirmDelete'),
      cancelText: 'Cancel',
      okButtonProps: { danger: true },
      onOk: async () => {
        await deleteCompileStep(kbId, s.id)
        message.success(t('compile.stepDeleted'))
        loadSteps()
      },
    })
  }

  const handleSaveEngine = async (model: string) => {
    try {
      const next = await saveEngineSetting(kbId, model)
      setEngine(next)
      message.success(t('compile.engineSaved'))
    } catch (e: any) {
      message.error(e?.message || t('common.saveFailed'))
    }
  }

  const tabItems = [
    {
      key: 'obj',
      label: 'Ontology Objects',
      children: (
        <OntologyObjectSection
          data={objects}
          loading={loadingObjects}
          onCreate={() => setObjectModal({ open: true, editing: null })}
          onImport={() => setImportModal({ open: true, mode: 'object' })}
          onEdit={(o) => setObjectModal({ open: true, editing: o })}
          onDelete={removeObject}
          onPrompt={(o) => setPromptModal({ open: true, title: `Prompt - Ontology Object: ${o.name}`, desc: `System prompt used to extract “${o.name}” entity instances from documents:`, content: buildObjectPrompt(o) })}
        />
      ),
    },
    {
      key: 'rel',
      label: 'Ontology Relations',
      children: (
        <OntologyRelationSection
          data={relations}
          loading={loadingRelations}
          onCreate={() => setRelationModal({ open: true, editing: null })}
          onImport={() => setImportModal({ open: true, mode: 'relation' })}
          onEdit={(r) => setRelationModal({ open: true, editing: r })}
          onDelete={removeRelation}
          onPrompt={(r) => setPromptModal({ open: true, title: `Prompt - Ontology Relation: ${r.name}`, desc: `System prompt used to extract “${r.name}” relation instances from documents:`, content: buildRelationPrompt(r) })}
        />
      ),
    },
    {
      key: 'constraint',
      label: 'Ontology Constraints',
      children: (
        <OntologyConstraintSection
          data={constraints}
          loading={loadingConstraints}
          onCreate={() => setConstraintModal({ open: true, editing: null })}
          onEdit={(c) => setConstraintModal({ open: true, editing: c })}
          onDelete={removeConstraint}
        />
      ),
    },
  ]

  return (
    <div>
      <Tabs activeKey={activeSubTab} onChange={setActiveSubTab} items={tabItems} />

      { }
      {false && (
        <>
          <CompileStepSection
            data={steps}
            loading={loadingSteps}
            onCreate={() => setStepModal({ open: true, editing: null })}
            onEdit={(s) => setStepModal({ open: true, editing: s })}
            onDelete={removeStep}
          />
          <EngineBasicSection engine={engine} loading={loadingEngine} onSave={handleSaveEngine} />
        </>
      )}

      <ObjectFormModal
        open={objectModal.open}
        editing={objectModal.editing}
        submitting={submitting}
        onCancel={() => setObjectModal({ open: false, editing: null })}
        onSubmit={submitObject}
      />
      <RelationFormModal
        open={relationModal.open}
        editing={relationModal.editing}
        objectNames={objects.map((o) => o.name)}
        submitting={submitting}
        onCancel={() => setRelationModal({ open: false, editing: null })}
        onSubmit={submitRelation}
      />
      <ConstraintFormModal
        open={constraintModal.open}
        editing={constraintModal.editing}
        targetOptions={targetOptions}
        existingNames={constraints.map((c) => c.name)}
        submitting={submitting}
        onCancel={() => setConstraintModal({ open: false, editing: null })}
        onSubmit={submitConstraint}
      />
      <StepFormModal
        open={stepModal.open}
        editing={stepModal.editing}
        submitting={submitting}
        onCancel={() => setStepModal({ open: false, editing: null })}
        onSubmit={submitStep}
      />
      <PromptViewModal
        open={promptModal.open}
        title={promptModal.title}
        desc={promptModal.desc}
        content={promptModal.content}
        onClose={() => setPromptModal((s) => ({ ...s, open: false }))}
      />
      <TemplateImportModal
        open={importModal.open}
        mode={importModal.mode}
        kbId={kbId}
        onClose={() => setImportModal((s) => ({ ...s, open: false }))}
        onImported={() => {
          if (importModal.mode === 'object') loadObjects()
          else loadRelations()
          loadTargetOptions()
        }}
      />
    </div>
  )
}
