const BUILT_IN_ACCESS_METHOD_IDS = new Set([
  'dam_demo_api',
  'dam_api_push_demo',
  'dam_demo_storage',
  'dam_demo_file',
  'dam_demo_mqtt',
])

const BUILT_IN_DATA_SOURCE_DEFAULT_NAMES: Record<string, Set<string>> = {
  ds_demo_internet_file: new Set(['文件上传', 'File Upload']),
  ds_demo_credit_file: new Set(['文件上传', 'File Upload']),
  ds_demo_medical_file: new Set(['文件上传', 'File Upload']),
  ds_demo_hwfin_file: new Set(['文件上传', 'File Upload']),
  ds_demo_llm_file: new Set(['文件上传', 'File Upload']),
}

const ACCESS_TYPE_KEY_SUFFIX: Record<string, string> = {
  api: 'api',
  api_push: 'apiPush',
  storage: 'storage',
  file: 'file',
  mqtt: 'mqtt',
}

type Translate = (key: string) => string

export function accessTypeDisplayName(accessType: string, t: Translate): string {
  const suffix = ACCESS_TYPE_KEY_SUFFIX[accessType]
  return suffix ? t(`domainKnowledge.dataSourceType.${suffix}`) : accessType
}

export function accessMethodDisplayName(
  method: { id: string; accessType: string; name: string },
  t: Translate,
): string {
  return BUILT_IN_ACCESS_METHOD_IDS.has(method.id)
    ? accessTypeDisplayName(method.accessType, t)
    : method.name
}

/**
 * Only localize the untouched names of product-owned seed instances.
 * A user-renamed instance—even when it retains a seed ID—must remain unchanged.
 */
export function dataSourceInstanceDisplayName(
  source: { id: string; accessType: string; name: string },
  t: Translate,
): string {
  const defaultNames = BUILT_IN_DATA_SOURCE_DEFAULT_NAMES[source.id]
  return defaultNames?.has(source.name)
    ? accessTypeDisplayName(source.accessType, t)
    : source.name
}
