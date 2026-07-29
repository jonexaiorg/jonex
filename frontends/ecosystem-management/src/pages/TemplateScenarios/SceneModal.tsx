import React, { useState, useCallback, forwardRef, useImperativeHandle } from 'react';
import { useTranslation } from 'react-i18next';
import { Form, Input, Modal, Select, message } from 'antd';
import { createTemplateScenario, updateTemplateScenario } from '../../api/templateScenarios';
import type { TemplateScenario } from '../../api/templateScenarios';

type SceneFormValues = {
  name: string;
  desc?: string;
  domainId: string;
};

export interface SceneModalHandle {
  openCreate: (initialDomainId: string) => void;
  openEdit: (scene: TemplateScenario) => void;
}

interface SceneModalProps {
  domainOptions: Array<{ label: string; value: string }>;
  loadingDomains: boolean;
  onSaved: () => void;
}

function getErrorMessage(error: unknown, fallback: string) {
  const err = error as { response?: { data?: { message?: string } }; message?: string };
  return err.response?.data?.message || err.message || fallback;
}

const SceneModal = forwardRef<SceneModalHandle, SceneModalProps>(function SceneModal(
  { domainOptions, loadingDomains, onSaved },
  ref,
) {
  const { t } = useTranslation();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingScene, setEditingScene] = useState<TemplateScenario | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [sceneForm] = Form.useForm<SceneFormValues>();

  useImperativeHandle(
    ref,
    () => ({
      openCreate: (initialDomainId: string) => {
        setEditingScene(null);
        sceneForm.setFieldsValue({
          name: '',
          desc: '',
          domainId: initialDomainId || domainOptions[0]?.value || '',
        });
        setModalOpen(true);
      },
      openEdit: (scene: TemplateScenario) => {
        setEditingScene(scene);
        sceneForm.setFieldsValue({
          name: scene.name,
          desc: scene.description || '',
          domainId: scene.domain_id,
        });
        setModalOpen(true);
      },
    }),
    [domainOptions, sceneForm],
  );

  const handleSave = useCallback(async () => {
    const values = await sceneForm.validateFields();
    const payload = {
      name: values.name.trim(),
      description: values.desc?.trim() || '',
      domain_id: values.domainId,
    };

    setSubmitting(true);
    try {
      if (editingScene) {
        await updateTemplateScenario(editingScene.id, payload);
        message.success(t('templateScenarios.sceneUpdated'));
      } else {
        await createTemplateScenario(payload);
        message.success(t('templateScenarios.sceneCreated'));
      }
      setModalOpen(false);
      onSaved();
    } catch (error) {
      message.error(
        getErrorMessage(
          error,
          editingScene ? t('templateScenarios.updateSceneFailed') : t('templateScenarios.createSceneFailed'),
        ),
      );
    } finally {
      setSubmitting(false);
    }
  }, [editingScene, sceneForm, onSaved, t]);

  return (
    <Modal
      title={editingScene ? t('templateScenarios.editScene') : t('templateScenarios.createSceneTitle')}
      open={modalOpen}
      onCancel={() => setModalOpen(false)}
      onOk={handleSave}
      okText={t('common.save')}
      cancelText={t('common.cancel')}
      confirmLoading={submitting}
      width={560}
    >
      <Form form={sceneForm} layout="vertical" className="template-scenarios-form">
        <Form.Item
          label={t('templateScenarios.sceneName')}
          name="name"
          rules={[{ required: true, whitespace: true, message: t('templateScenarios.sceneNameInput') }]}
        >
          <Input placeholder={t('templateScenarios.sceneNameInput')} />
        </Form.Item>
        <Form.Item label={t('common.description')} name="desc">
          <Input.TextArea placeholder={t('templateScenarios.sceneDescPlaceholder')} rows={3} />
        </Form.Item>
        <Form.Item
          label={t('templateScenarios.domainLabel')}
          name="domainId"
          rules={[{ required: true, message: t('templateScenarios.selectDomain') }]}
        >
          <Select placeholder={t('templateScenarios.selectDomain')} loading={loadingDomains} options={domainOptions} />
        </Form.Item>
      </Form>
    </Modal>
  );
});

export default SceneModal;
