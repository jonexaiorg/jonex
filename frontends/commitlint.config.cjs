module.exports = {
  extends: ['@commitlint/config-conventional'],
  // 可选：自定义规则
  rules: {
    'type-enum': [
      2,
      'always',
      [
        'feat',     // 新功能
        'fix',      // 修复
        'docs',     // 文档
        'style',    // 代码格式（不影响功能）
        'refactor', // 重构
        'perf',     // 性能优化
        'test',     // 测试
        'chore',    // 构建/工具变更
        'ci',       // CI 配置
        'revert',   // 回滚
      ],
    ],
    'subject-case': [0], // 关闭 subject 大小写限制
  },
};
