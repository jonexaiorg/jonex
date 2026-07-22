import React from 'react'
import { Input, Button, Table, Tag, Select } from 'antd'
import { SearchOutlined } from '@ant-design/icons'

const logs = [
  { time: '2026-05-22 15:30:12', level: 'INFO', module: '知识编译', user: '张明远', message: '金融风控知识编译任务已完成', ip: '192.168.1.100' },
  { time: '2026-05-22 15:28:45', level: 'WARN', module: '数据解析', user: '系统', message: '设备传感器数据源连接超时，正在进行重试', ip: '--' },
  { time: '2026-05-22 15:25:30', level: 'ERROR', module: '知识编译', user: '系统', message: '法律法规知识库编译失败：图谱构建引擎异常退出', ip: '--' },
  { time: '2026-05-22 15:20:18', level: 'INFO', module: '用户管理', user: '张明远', message: '用户「陈伟」角色已变更为观察者', ip: '192.168.1.100' },
  { time: '2026-05-22 15:15:00', level: 'INFO', module: '数据解析', user: '系统', message: '医学文献知识库增量同步完成，新增 128 篇文档', ip: '--' },
  { time: '2026-05-22 15:00:00', level: 'DEBUG', module: '系统', user: '系统', message: '定时任务调度器健康检查通过', ip: '127.0.0.1' },
  { time: '2026-05-22 14:42:33', level: 'INFO', module: '模型适配', user: '张明远', message: 'GPT-4o 模型连接测试成功，延迟 1.2s', ip: '192.168.1.100' },
  { time: '2026-05-22 14:30:00', level: 'INFO', module: '知识编译', user: '系统', message: '医学文献知识库向量化任务启动', ip: '--' },
  { time: '2026-05-22 14:28:10', level: 'WARN', module: '系统', user: '系统', message: '存储使用量已达 127 GB（上限 500 GB）', ip: '--' },
  { time: '2026-05-22 14:25:00', level: 'ERROR', module: '数据解析', user: '系统', message: '法律法规文件存储连接失败：认证凭据已过期', ip: '--' },
]

const levelColor: Record<string, string> = {
  INFO: 'processing', WARN: 'warning', ERROR: 'error', DEBUG: 'success',
}

export default function OperationLog() {
  const columns = [
    { title: '时间', dataIndex: 'time', key: 'time', width: 170 },
    { title: '级别', dataIndex: 'level', key: 'level', width: 70, render: (v: string) => <Tag color={levelColor[v]}>{v}</Tag> },
    { title: '模块', dataIndex: 'module', key: 'module', width: 90 },
    { title: '用户', dataIndex: 'user', key: 'user', width: 80 },
    { title: '消息', dataIndex: 'message', key: 'message' },
    { title: 'IP', dataIndex: 'ip', key: 'ip', width: 130 },
  ]

  return (
    <div>
      <div className="yx-page-title"><h1>日志管理</h1></div>
      <div className="yx-card">
        <div className="yx-toolbar" style={{ flexWrap: 'wrap' }}>
          <Input prefix={<SearchOutlined />} placeholder="搜索日志..." style={{ width: 200 }} />
          <Input defaultValue="2026-05-22 ~ 2026-05-22" style={{ width: 200 }} />
          <Select defaultValue="全部级别" style={{ width: 110 }} options={['全部级别', 'INFO', 'WARN', 'ERROR', 'DEBUG'].map(s => ({ value: s, label: s }))} />
          <Select defaultValue="全部模块" style={{ width: 110 }} options={['全部模块', '知识编译', '数据解析', '用户管理'].map(s => ({ value: s, label: s }))} />
          <Button type="primary" icon={<SearchOutlined />}>查询</Button>
        </div>
        <Table columns={columns} dataSource={logs} rowKey="time" pagination={{ total: 256, pageSize: 10 }} size="small" />
      </div>
    </div>
  )
}
