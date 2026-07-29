import React, { useState, useCallback, forwardRef, useImperativeHandle } from 'react';
import { useTranslation } from 'react-i18next';
import { Form, Input, Modal, Select, message } from 'antd';
import { createTemplateRelation, updateTemplateRelation } from '../../api/templateScenarios';
import type { TemplateRelation } from '../../api/templateScenarios';

const RELATION_TYPE_VALUES = ['一对一', '一对多', '多对一', '多对多'] as const;

type RelationFormValues = {
  sourceObjectId?: string;
  relation: string;
  targetObjectId?: string;
  desc?: string;
  type: string;
};

function getErrorMessage(error: unknown, fallback: string) {
  const err = error as { response?: { data?: { message?: string } }; message?: string };
  return err.response?.data?.message || err.message || fallback;
}

export interface RelationModalHandle {
  openCreate: () => void;
  openEdit: (item: TemplateRelation) => void;
}

interface RelationModalProps {
  selectedSceneId: string | null;
  objectSelectOptions: Array<{ label: string; value: string }>;
  relationTypeOptions: Array<{ label: string; value: string }>;
  onSaved: () => void;
}

const RelationModal = forwardRef<RelationModalHandle, RelationModalProps>(function RelationModal(
  { selectedSceneId, objectSelectOptions, relationTypeOptions, onSaved },
  ref,
) {
  const { t } = useTranslation();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingRelation, setEditingRelation] = useState<TemplateRelation | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [relationForm] = Form.useForm<RelationFormValues>();

  useImperativeHandle(
    ref,
    () => ({
      openCreate: () => {
        setEditingRelation(null);
        relationForm.setFieldsValue({
          sourceObjectId: undefined,
          relation: '',
          targetObjectId: undefined,
          desc: '',
          type: RELATION_TYPE_VALUES[1],
        });
        setModalOpen(true);
      },
      openEdit: (item: TemplateRelation) => {
        setEditingRelation(item);
        relationForm.setFieldsValue({
          sourceObjectId: item.source_object_id,
          relation: item.name,
          targetObjectId: item.target_object_id,
          desc: item.description || '',
          type: item.relation_type,
        });
        setModalOpen(true);
      },
    }),
    [relationForm],
  );

  const handleSave = useCallback(async () => {
    if (!selectedSceneId) return;
    const values = await relationForm.validateFields();
    if (!values.sourceObjectId || !values.targetObjectId) return;

    setSubmitting(true);
    try {
      const payload = {
        source_object_id: values.sourceObjectId,
        target_object_id: values.targetObjectId,
        name: values.relation.trim(),
        description: values.desc?.trim() || '',
        relation_type: values.type,
      };
      if (editingRelation) {
        await updateTemplateRelation(editingRelation.id, payload);
        message.success(t('templateScenarios.relationUpdated'));
      } else {
        await createTemplateRelation(selectedSceneId, payload);
        message.success(t('templateScenarios.relationCreated'));
      }
      setModalOpen(false);
      onSaved();
    } catch (error) {
      message.error(
        getErrorMessage(
          error,
          editingRelation ? t('templateScenarios.updateRelationFailed') : t('templateScenarios.createRelationFailed'),
        ),
      );
    } finally {
      setSubmitting(false);
    }
  }, [selectedSceneId, editingRelation, relationForm, onSaved, t]);

  return (
    <Modal
      title={editingRelation ? t('templateScenarios.editRelation') : t('templateScenarios.createRelationTitle')}
      open={modalOpen}
      onCancel={() => setModalOpen(false)}
      onOk={handleSave}
      okText={t('common.save')}
      cancelText={t('common.cancel')}
      confirmLoading={submitting}
      width={640}
    >
      <Form form={relationForm} layout="vertical" className="template-scenarios-form">
        <div className="template-scenarios-relation-grid">
          <Form.Item
            label={t('templateScenarios.sourceObjectSelect')}
            name="sourceObjectId"
            rules={[{ required: true, message: t('templateScenarios.selectSourceObject') }]}
          >
            <Select placeholder={t('templateScenarios.selectSourceObject')} options={objectSelectOptions} />
          </Form.Item>
          <Form.Item
            label={t('templateScenarios.targetObjectSelect')}
            name="targetObjectId"
            rules={[{ required: true, message: t('templateScenarios.selectTargetObject') }]}
          >
            <Select placeholder={t('templateScenarios.selectTargetObject')} options={objectSelectOptions} />
          </Form.Item>
        </div>
        <Form.Item
          label={t('templateScenarios.relationNameLabel')}
          name="relation"
          rules={[{ required: true, whitespace: true, message: t('templateScenarios.relationNameInput') }]}
        >
          <Input placeholder={t('templateScenarios.relationNameInput')} />
        </Form.Item>
        <Form.Item label={t('common.description')} name="desc">
          <Input.TextArea placeholder={t('templateScenarios.relationDescPlaceholder')} rows={3} />
        </Form.Item>
        <Form.Item
          label={t('templateScenarios.relationType')}
          name="type"
          rules={[{ required: true, message: t('templateScenarios.selectRelationType') }]}
        >
          <Select placeholder={t('templateScenarios.selectRelationType')} options={relationTypeOptions} />
        </Form.Item>
      </Form>
    </Modal>
  );
});

export default RelationModal;
