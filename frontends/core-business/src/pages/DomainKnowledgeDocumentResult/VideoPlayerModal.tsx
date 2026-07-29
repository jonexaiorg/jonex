import React, { useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Modal } from 'antd';

interface VideoPlayerModalProps {
  open: boolean;
  videoUrl: string;
  onClose: () => void;
}

export default function VideoPlayerModal({ open, videoUrl, onClose }: VideoPlayerModalProps) {
  const { t } = useTranslation();
  const videoRef = useRef<HTMLVideoElement>(null);

  return (
    <Modal
      title={t('domainKnowledge.videoPreview')}
      open={open}
      onCancel={onClose}
      footer={null}
      width={800}
      destroyOnClose
      styles={{ body: { padding: 0 } }}
    >
      <video
        ref={videoRef}
        controls
        autoPlay
        style={{
          width: '100%',
          height: 400,
          maxHeight: '85vh',
          display: 'block',
        }}
      >
        <source src={videoUrl} />
      </video>
    </Modal>
  );
}
