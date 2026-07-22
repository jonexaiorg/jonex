import React from 'react'
import { Button, Card, Select, Switch, Space, Input } from 'antd'
import { FileTextOutlined, VideoCameraOutlined, AudioOutlined, PictureOutlined, SaveOutlined, UndoOutlined } from '@ant-design/icons'

export default function DomainKnowledgeParser() {
  return (
    <div>
      <div className="yx-page-title">
        <h1>解析配置</h1>
        <p style={{ color: '#64748b', margin: '4px 0 0', fontSize: 14 }}>配置各类型数据的解析参数</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 20 }}>
        <Card style={{ borderRadius: 12, border: '1px solid #e2e8f0' }} bodyStyle={{ padding: 24 }}>
          <h3 style={{ margin: '0 0 16px', fontSize: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <FileTextOutlined style={{ color: '#3b82f6' }} /> 文档解析
          </h3>
          <div className="yx-form-row">
            <label>解析引擎</label>
            <Select defaultValue="默认文档解析器 (v2.1)" style={{ width: '100%' }} options={[{ value: '默认文档解析器 (v2.1)', label: '默认文档解析器 (v2.1)' }, { value: '轻量解析器 (v1.5)', label: '轻量解析器 (v1.5)' }]} />
          </div>
          <div className="yx-form-row">
            <label>最大文件大小</label>
            <Input defaultValue="50 MB" />
          </div>
          <div className="yx-form-row">
            <label>支持格式</label>
            <Input defaultValue="PDF, DOCX, TXT, MD, HTML" />
          </div>
          <div className="yx-form-row">
            <label>OCR 识别</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Switch defaultChecked /> <span style={{ fontSize: 13 }}>启用 OCR</span></div>
            <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 4 }}>对扫描版 PDF 自动进行文字识别</div>
          </div>
        </Card>

        <Card style={{ borderRadius: 12, border: '1px solid #e2e8f0' }} bodyStyle={{ padding: 24 }}>
          <h3 style={{ margin: '0 0 16px', fontSize: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <VideoCameraOutlined style={{ color: '#3b82f6' }} /> 视频解析
          </h3>
          <div className="yx-form-row">
            <label>解析引擎</label>
            <Select defaultValue="智能视频解析器 (v1.8)" style={{ width: '100%' }} options={[{ value: '智能视频解析器 (v1.8)', label: '智能视频解析器 (v1.8)' }]} />
          </div>
          <div className="yx-form-row">
            <label>关键帧提取频率</label>
            <Select defaultValue="每 30 秒" style={{ width: '100%' }} options={['每 5 秒', '每 10 秒', '每 30 秒'].map((s) => ({ value: s, label: s }))} />
          </div>
          <div className="yx-form-row">
            <label>音频转录</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Switch defaultChecked /> <span style={{ fontSize: 13 }}>启用语音转文字</span></div>
          </div>
          <div className="yx-form-row">
            <label>最大时长</label>
            <Input defaultValue="120 分钟" />
          </div>
        </Card>

        <Card style={{ borderRadius: 12, border: '1px solid #e2e8f0' }} bodyStyle={{ padding: 24 }}>
          <h3 style={{ margin: '0 0 16px', fontSize: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <AudioOutlined style={{ color: '#3b82f6' }} /> 音频解析
          </h3>
          <div className="yx-form-row">
            <label>解析引擎</label>
            <Select defaultValue="智能音频解析器 (v2.0)" style={{ width: '100%' }} options={[{ value: '智能音频解析器 (v2.0)', label: '智能音频解析器 (v2.0)' }]} />
          </div>
          <div className="yx-form-row">
            <label>音频采样率</label>
            <Select defaultValue="44.1kHz" style={{ width: '100%' }} options={['16kHz', '44.1kHz', '48kHz'].map((s) => ({ value: s, label: s }))} />
          </div>
          <div className="yx-form-row">
            <label>语种检测</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Switch defaultChecked /> <span style={{ fontSize: 13 }}>自动检测语种</span></div>
          </div>
          <div className="yx-form-row">
            <label>说话人分离</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Switch /> <span style={{ fontSize: 13 }}>启用说话人分离</span></div>
            <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 4 }}>区分不同说话人的对话内容</div>
          </div>
        </Card>

        <Card style={{ borderRadius: 12, border: '1px solid #e2e8f0' }} bodyStyle={{ padding: 24 }}>
          <h3 style={{ margin: '0 0 16px', fontSize: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <PictureOutlined style={{ color: '#3b82f6' }} /> 图像解析
          </h3>
          <div className="yx-form-row">
            <label>解析引擎</label>
            <Select defaultValue="智能图像解析器 (v1.9)" style={{ width: '100%' }} options={[{ value: '智能图像解析器 (v1.9)', label: '智能图像解析器 (v1.9)' }]} />
          </div>
          <div className="yx-form-row">
            <label>文字提取</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Switch defaultChecked /> <span style={{ fontSize: 13 }}>启用图像文字提取</span></div>
          </div>
          <div className="yx-form-row">
            <label>图像描述</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Switch /> <span style={{ fontSize: 13 }}>生成图像描述</span></div>
          </div>
          <div className="yx-form-row">
            <label>支持格式</label>
            <Input defaultValue="JPG, PNG, GIF, BMP, TIFF" />
          </div>
        </Card>
      </div>

      <div style={{ marginTop: 20, display: 'flex', gap: 12 }}>
        <Button type="primary" icon={<SaveOutlined />}>保存配置</Button>
        <Button icon={<UndoOutlined />}>恢复默认</Button>
      </div>
    </div>
  )
}
