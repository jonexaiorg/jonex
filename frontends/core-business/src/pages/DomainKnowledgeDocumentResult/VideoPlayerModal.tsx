import React, { useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Modal } from 'antd';

interface VideoPlayerModalProps {
  open: boolean;
  videoUrl: string;
  timeStart?: number | null;
  onClose: () => void;
}

export default function VideoPlayerModal({ open, videoUrl, timeStart, onClose }: VideoPlayerModalProps) {
  const { t } = useTranslation();
  const videoRef = useRef<HTMLVideoElement>(null);

  // 视频加载后将 currentTime 定位到 timeStart，null 则从头开始
  const handleMetadataLoaded = () => {
    if (videoRef.current) {
      videoRef.current.currentTime = timeStart ?? 0;
    }
  };

  // 用 #t= 片段让浏览器原生支持定位（CDN/proxy 兼容时最可靠）
  const srcUrl = timeStart != null ? `${videoUrl}#t=${timeStart}` : videoUrl;

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
        onLoadedMetadata={handleMetadataLoaded}
        style={{
          width: '100%',
          height: 400,
          maxHeight: '85vh',
          display: 'block',
        }}
      >
        <source src={srcUrl} />
      </video>
    </Modal>
  );
}
