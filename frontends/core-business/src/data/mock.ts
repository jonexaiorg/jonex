export interface DomainSpace {
  id: string
  name: string
  description: string
  status: 'active' | 'inactive'
  docCount: number
  knowledgeCount: number
  createdAt: string
  icon?: string
}

export interface KnowledgeItem {
  id: string
  title: string
  domain: string
  sourceType: string
  status: 'published' | 'draft' | 'processing' | 'error'
  author: string
  updatedAt: string
  tags: string[]
  viewCount: number
}

export interface Domain {
  id: string
  name: string
  code: string
  description: string
  serviceCount: number
  knowledgeCount: number
  searchEnabled: boolean
  status: 'active' | 'inactive'
  createdAt: string
}

export interface KnowledgeSearchResult {
  id: string
  title: string
  domain: string
  snippet: string
  source: string
  relevance: number
  updatedAt: string
}

export interface DomainPermission {
  id: string
  username: string
  displayName: string
  role: 'admin' | 'editor' | 'viewer'
  avatar?: string
}

export const MOCK_DOMAIN_SPACES: DomainSpace[] = [
  { id: '1', name: '医疗健康知识空间', description: '涵盖临床医学、药物研发、公共卫生等领域的知识体系', status: 'active', docCount: 1248, knowledgeCount: 3456, createdAt: '2025-08-15' },
  { id: '2', name: '金融科技知识空间', description: '风控模型、量化交易、监管合规等金融领域知识', status: 'active', docCount: 892, knowledgeCount: 2340, createdAt: '2025-09-01' },
  { id: '3', name: '智能制造知识空间', description: '工业4.0、预测性维护、数字孪生等领域知识', status: 'active', docCount: 567, knowledgeCount: 1823, createdAt: '2025-10-12' },
  { id: '4', name: '教育培训知识空间', description: '自适应学习、教育资源推荐、学情分析', status: 'active', docCount: 1023, knowledgeCount: 2891, createdAt: '2025-08-28' },
  { id: '5', name: '零售电商知识空间', description: '用户画像、推荐系统、供应链优化', status: 'active', docCount: 756, knowledgeCount: 1654, createdAt: '2025-11-05' },
  { id: '6', name: '能源环保知识空间', description: '碳排放管理、新能源技术、环境监测', status: 'inactive', docCount: 234, knowledgeCount: 678, createdAt: '2025-07-20' },
]

export const MOCK_KNOWLEDGE_ITEMS: KnowledgeItem[] = [
  { id: '1', title: '心血管疾病诊断专家共识2025版', domain: '医疗健康', sourceType: 'PDF文档', status: 'published', author: '张明远', updatedAt: '2026-05-15', tags: ['心血管', '诊断', '专家共识'], viewCount: 2345 },
  { id: '2', title: '金融风控模型训练数据预处理规范', domain: '金融科技', sourceType: 'Word文档', status: 'published', author: '李芳', updatedAt: '2026-05-14', tags: ['风控', '数据预处理'], viewCount: 1876 },
  { id: '3', title: '智能制造设备故障诊断算法对比研究', domain: '智能制造', sourceType: 'PDF文档', status: 'processing', author: '王建国', updatedAt: '2026-05-13', tags: ['故障诊断', '算法'], viewCount: 956 },
  { id: '4', title: '基于知识图谱的个性化学习路径推荐', domain: '教育培训', sourceType: 'API接入', status: 'published', author: '陈思雨', updatedAt: '2026-05-12', tags: ['知识图谱', '推荐算法'], viewCount: 3210 },
  { id: '5', title: '零售客户行为分析与RFM模型应用', domain: '零售电商', sourceType: 'CSV数据', status: 'draft', author: '赵阳', updatedAt: '2026-05-11', tags: ['行为分析', 'RFM'], viewCount: 654 },
  { id: '6', title: '新能源碳排放核算方法学指南', domain: '能源环保', sourceType: 'PDF文档', status: 'error', author: '刘浩然', updatedAt: '2026-05-10', tags: ['碳排放', '方法学'], viewCount: 432 },
  { id: '7', title: '深度学习在药物发现中的应用综述', domain: '医疗健康', sourceType: 'PDF文档', status: 'published', author: '周文博', updatedAt: '2026-05-09', tags: ['深度学习', '药物发现'], viewCount: 1876 },
  { id: '8', title: '监管科技在反洗钱中的应用实践', domain: '金融科技', sourceType: 'API接入', status: 'published', author: '吴婷婷', updatedAt: '2026-05-08', tags: ['监管科技', '反洗钱'], viewCount: 1456 },
]

export const MOCK_DOMAINS: Domain[] = [
  { id: '1', name: '医疗健康', code: 'medical', description: '临床医学、药物研发、公共卫生', serviceCount: 12, knowledgeCount: 3456, searchEnabled: true, status: 'active', createdAt: '2025-06-01' },
  { id: '2', name: '金融科技', code: 'finance', description: '风控、量化交易、监管合规', serviceCount: 8, knowledgeCount: 2340, searchEnabled: true, status: 'active', createdAt: '2025-06-15' },
  { id: '3', name: '智能制造', code: 'manufacture', description: '工业4.0、预测性维护、数字孪生', serviceCount: 6, knowledgeCount: 1823, searchEnabled: true, status: 'active', createdAt: '2025-07-01' },
  { id: '4', name: '教育培训', code: 'education', description: '自适应学习、资源推荐、学情分析', serviceCount: 10, knowledgeCount: 2891, searchEnabled: true, status: 'active', createdAt: '2025-07-15' },
  { id: '5', name: '零售电商', code: 'retail', description: '用户画像、推荐系统、供应链', serviceCount: 5, knowledgeCount: 1654, searchEnabled: false, status: 'active', createdAt: '2025-08-01' },
  { id: '6', name: '能源环保', code: 'energy', description: '碳排放、新能源、环境监测', serviceCount: 4, knowledgeCount: 678, searchEnabled: false, status: 'inactive', createdAt: '2025-08-15' },
]

export const MOCK_DOMAIN_PERMISSIONS: DomainPermission[] = [
  { id: '1', username: 'zhangming', displayName: '张明远', role: 'admin' },
  { id: '2', username: 'lifang', displayName: '李芳', role: 'editor' },
  { id: '3', username: 'wangjianguo', displayName: '王建国', role: 'editor' },
  { id: '4', username: 'chensiyu', displayName: '陈思雨', role: 'viewer' },
  { id: '5', username: 'zhaoyang', displayName: '赵阳', role: 'viewer' },
  { id: '6', username: 'liuhaoran', displayName: '刘浩然', role: 'editor' },
]

export interface GraphInstance {
  id: string
  name: string
  type: string
  properties: { key: string; value: string }[]
  relations: { id: string; name: string; target: string }[]
  sourceDocs: string[]
}

export interface GraphRelation {
  id: string
  name: string
  sourceEntity: string
  targetEntity: string
  type: string
  properties: { key: string; value: string }[]
  sourceSnippets: string[]
}

export const MOCK_GRAPH_INSTANCES: GraphInstance[] = [
  {
    id: 'inst-001',
    name: '企业数字化转型',
    type: '概念',
    properties: [
      { key: '别名', value: '数字转型、数字化变革' },
      { key: '定义', value: '企业运用数字技术对业务流程、组织架构和企业文化进行系统性重塑的过程' },
      { key: '来源', value: '《企业数字化转型白皮书》' },
      { key: '置信度', value: '0.95' },
    ],
    relations: [
      { id: 'rel-001', name: '包含', target: '云计算技术' },
      { id: 'rel-002', name: '依赖', target: '数据治理体系' },
      { id: 'rel-003', name: '驱动', target: '业务创新' },
    ],
    sourceDocs: ['企业数字化转型白皮书.pdf', '数字化转型案例集.docx'],
  },
  {
    id: 'inst-002',
    name: '知识图谱',
    type: '技术',
    properties: [
      { key: '英文名', value: 'Knowledge Graph' },
      { key: '提出者', value: 'Google, 2012' },
      { key: '应用领域', value: '语义搜索、智能问答、推荐系统' },
    ],
    relations: [
      { id: 'rel-004', name: '属于', target: '人工智能技术' },
      { id: 'rel-005', name: '使用', target: '图数据库' },
    ],
    sourceDocs: ['知识图谱技术综述.pdf'],
  },
]

export const MOCK_GRAPH_RELATIONS: GraphRelation[] = [
  {
    id: 'rel-001',
    name: '包含',
    sourceEntity: '企业数字化转型',
    targetEntity: '云计算技术',
    type: '组成关系',
    properties: [
      { key: '权重', value: '0.85' },
      { key: '来源', value: '自动抽取' },
    ],
    sourceSnippets: ['企业数字化转型包含云计算、大数据、人工智能等关键技术...', '其中云计算作为基础支撑平台...'],
  },
  {
    id: 'rel-002',
    name: '依赖',
    sourceEntity: '企业数字化转型',
    targetEntity: '数据治理体系',
    type: '依赖关系',
    properties: [
      { key: '权重', value: '0.78' },
      { key: '来源', value: '专家标注' },
    ],
    sourceSnippets: ['数字化转型依赖于完善的数据治理体系...'],
  },
]
