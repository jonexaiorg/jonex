import { Tag } from 'antd';
import { useTranslation } from 'react-i18next';
import { FILTER_PHASES, PHASE_DISPLAY, type DocPhase } from '@/utils/docPhase';

const { CheckableTag } = Tag;

export interface DocumentStatusFilterProps {
  /** 当前选中的 phase 列表；空数组表示「全部」。 */
  value: DocPhase[];
  onChange: (phases: DocPhase[]) => void;
}

/**
 * 线性状态筛选器（多选 chip）。选中的 phase 直接作为后端 `phase` 参数（多值 OR）。
 * 「全部」重置为空；点某 phase 切换其选中态。与 utils/docPhase 同源。
 */
export default function DocumentStatusFilter({ value, onChange }: DocumentStatusFilterProps) {
  const { t } = useTranslation();
  const toggle = (phase: DocPhase, checked: boolean) => {
    if (checked) {
      onChange([...value, phase]);
    } else {
      onChange(value.filter((p) => p !== phase));
    }
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
      <CheckableTag
        checked={value.length === 0}
        onChange={() => onChange([])}
        style={{ fontSize: 12, padding: '2px 10px', borderRadius: 6 }}
      >
        {t('common.all')}
      </CheckableTag>
      {FILTER_PHASES.map((phase) => {
        const d = PHASE_DISPLAY[phase];
        const checked = value.includes(phase);
        return (
          <CheckableTag
            key={phase}
            checked={checked}
            onChange={(c) => toggle(phase, c)}
            style={{
              fontSize: 12,
              padding: '2px 10px',
              borderRadius: 6,
              // 选中时用该 phase 主题色，未选中走 antd 默认
              ...(checked ? { background: d.color, color: '#fff' } : {}),
            }}
          >
            {t(d.label)}
          </CheckableTag>
        );
      })}
    </div>
  );
}
