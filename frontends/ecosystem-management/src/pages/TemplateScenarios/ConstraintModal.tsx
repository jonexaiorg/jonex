import React, { useState, useCallback, useMemo, forwardRef, useImperativeHandle } from 'react';
import { useTranslation } from 'react-i18next';
import { Form, Input, Modal, Select, message } from 'antd';
import { createTemplateConstraint, updateTemplateConstraint } from '../../api/templateScenarios';
import type { TemplateConstraint, TemplateObject, TemplateRelation } from '../../api/templateScenarios';
import {
  getTemplateAttributeDisplay,
  getTemplateObjectDisplay,
  getTemplateRelationDisplay,
} from '../../utils/builtInTemplateDisplay';

function getErrorMessage(error: unknown, fallback: string) {
  const err = error as { response?: { data?: { message?: string } }; message?: string };
  return err.response?.data?.message || err.message || fallback;
}

export interface ConstraintModalHandle {
  openCreate: () => void;
  openEdit: (c: TemplateConstraint) => void;
}

interface ConstraintModalProps {
  selectedSceneId: string | null;
  objects: TemplateObject[];
  relations: TemplateRelation[];
  getObjectName: (id?: string | null) => string;
  english: boolean;
  onSaved: () => void;
}

const ConstraintModal = forwardRef<ConstraintModalHandle, ConstraintModalProps>(function ConstraintModal(
  { selectedSceneId, objects, relations, getObjectName, english, onSaved },
  ref,
) {
  const { t } = useTranslation();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingConstraint, setEditingConstraint] = useState<TemplateConstraint | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [constraintForm, setConstraintForm] = useState({
    name: '',
    target_type: 'object' as string,
    target_id: '',
    constraint_type: 'unique' as string,
    expression: '',
    suggestion: '',
  });

  const constraintTargetTypeOptions = useMemo(
    () => [
      { label: t('compile.constraintTargetType.object'), value: 'object' },
      { label: t('compile.constraintTargetType.attribute'), value: 'attribute' },
      { label: t('compile.constraintTargetType.relation'), value: 'relation' },
    ],
    [t],
  );

  const constraintTypeOptions = useMemo(
    () => [
      { label: t('compile.constraintType.unique'), value: 'unique' },
      { label: t('compile.constraintType.exists'), value: 'exists' },
      { label: t('compile.constraintType.conditional'), value: 'conditional' },
      { label: t('compile.constraintType.range'), value: 'range' },
    ],
    [t],
  );

  const constraintTargetOptions = useMemo(() => {
    if (constraintForm.target_type === 'object') {
      return objects.map((o) => ({ label: getTemplateObjectDisplay(o, english).name, value: o.id }));
    }
    if (constraintForm.target_type === 'relation') {
      return relations.map((r) => ({
        label: `${getObjectName(r.source_object_id)} → ${getObjectName(r.target_object_id)} (${getTemplateRelationDisplay(r, english).name})`,
        value: r.id,
      }));
    }
    if (constraintForm.target_type === 'attribute') {
      const flat: Array<{ label: string; value: string }> = [];
      objects.forEach((o) => {
        o.attributes?.forEach((a) => {
          flat.push({
            label: `${getTemplateObjectDisplay(o, english).name}.${getTemplateAttributeDisplay(a, english).name}`,
            value: a.id,
          });
        });
      });
      return flat;
    }
    return [];
  }, [constraintForm.target_type, english, getObjectName, objects, relations]);

  useImperativeHandle(
    ref,
    () => ({
      openCreate: () => {
        setEditingConstraint(null);
        setConstraintForm({
          name: '',
          target_type: 'object',
          target_id: '',
          constraint_type: 'unique',
          expression: '',
          suggestion: '',
        });
        setModalOpen(true);
      },
      openEdit: (c: TemplateConstraint) => {
        setEditingConstraint(c);
        setConstraintForm({
          name: c.name,
          target_type: c.target_type,
          target_id: c.target_id,
          constraint_type: c.constraint_type,
          expression: c.expression || '',
          suggestion: c.suggestion || '',
        });
        setModalOpen(true);
      },
    }),
    [],
  );

  const handleSave = useCallback(async () => {
    if (!constraintForm.name.trim()) {
      message.warning(t('templateScenarios.constraintNameWarning'));
      return;
    }
    if (!constraintForm.target_id) {
      message.warning(t('templateScenarios.constraintTargetWarning'));
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        name: constraintForm.name.trim(),
        target_type: constraintForm.target_type,
        target_id: constraintForm.target_id,
        constraint_type: constraintForm.constraint_type,
        expression: constraintForm.expression || undefined,
        suggestion: constraintForm.suggestion || undefined,
      };
      if (editingConstraint) {
        await updateTemplateConstraint(editingConstraint.id, payload);
        message.success(t('templateScenarios.constraintUpdated'));
      } else {
        await createTemplateConstraint(selectedSceneId!, payload);
        message.success(t('templateScenarios.constraintCreated'));
      }
      setModalOpen(false);
      onSaved();
    } catch (error) {
      message.error(getErrorMessage(error, t('templateScenarios.saveConstraintFailed')));
    } finally {
      setSubmitting(false);
    }
  }, [constraintForm, editingConstraint, selectedSceneId, onSaved, t]);

  return (
    <Modal
      title={editingConstraint ? t('templateScenarios.editConstraint') : t('templateScenarios.createConstraintTitle')}
      open={modalOpen}
      onCancel={() => setModalOpen(false)}
      onOk={handleSave}
      okText={t('common.save')}
      cancelText={t('common.cancel')}
      confirmLoading={submitting}
      width={640}
    >
      <Form layout="vertical" className="template-scenarios-form">
        <Form.Item label={t('templateScenarios.constraintName')} required>
          <Input
            placeholder={t('templateScenarios.constraintNameInput')}
            value={constraintForm.name}
            onChange={(e) => setConstraintForm({ ...constraintForm, name: e.target.value })}
          />
        </Form.Item>
        <div className="template-scenarios-relation-grid">
          <Form.Item label={t('templateScenarios.constraintTargetType')} required>
            <Select
              value={constraintForm.target_type}
              onChange={(v) => setConstraintForm({ ...constraintForm, target_type: v, target_id: '' })}
              options={constraintTargetTypeOptions}
            />
          </Form.Item>
          <Form.Item label={t('templateScenarios.constraintTargetObject')} required>
            <Select
              placeholder={t('templateScenarios.selectConstraintTarget')}
              value={constraintForm.target_id || undefined}
              onChange={(v) => setConstraintForm({ ...constraintForm, target_id: v || '' })}
              options={constraintTargetOptions}
              showSearch
              filterOption={(input, option) => (option?.label as string)?.toLowerCase().includes(input.toLowerCase())}
            />
          </Form.Item>
        </div>
        <Form.Item label={t('templateScenarios.constraintType')} required>
          <Select
            value={constraintForm.constraint_type}
            onChange={(v) => setConstraintForm({ ...constraintForm, constraint_type: v })}
            options={constraintTypeOptions}
          />
        </Form.Item>
        <Form.Item
          label={t('templateScenarios.constraintExpression')}
          required={constraintForm.constraint_type === 'conditional' || constraintForm.constraint_type === 'range'}
        >
          <Input.TextArea
            placeholder={t('templateScenarios.constraintExpressionInput')}
            value={constraintForm.expression}
            onChange={(e) => setConstraintForm({ ...constraintForm, expression: e.target.value })}
            rows={3}
          />
        </Form.Item>
        <Form.Item label={t('templateScenarios.suggestion')}>
          <Input.TextArea
            placeholder={t('templateScenarios.suggestionInput')}
            value={constraintForm.suggestion}
            onChange={(e) => setConstraintForm({ ...constraintForm, suggestion: e.target.value })}
            rows={2}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
});

export default ConstraintModal;
