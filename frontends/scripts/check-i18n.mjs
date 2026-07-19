import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const workspaceRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const errors = []

const localeTargets = [
  { name: 'shared', dir: 'shared/i18n-resources/src/locales' },
  { name: '_template', dir: '_template/src/locales' },
  { name: 'core-business', dir: 'core-business/src/locales' },
  { name: 'platform-management', dir: 'platform-management/src/locales' },
  { name: 'ecosystem-management', dir: 'ecosystem-management/src/locales' },
]

const sourceTargets = [
  { name: 'shell', dir: 'shell/src', locale: null },
  { name: '_template', dir: '_template/src', locale: '_template' },
  { name: 'core-business', dir: 'core-business/src', locale: 'core-business' },
  { name: 'platform-management', dir: 'platform-management/src', locale: 'platform-management' },
  { name: 'ecosystem-management', dir: 'ecosystem-management/src', locale: 'ecosystem-management' },
]

function relative(file) {
  return path.relative(workspaceRoot, file).replaceAll('\\', '/')
}

function parseJsonWithDuplicateKeys(text, file) {
  let index = 0

  function fail(message) {
    throw new Error(`${relative(file)}:${index + 1}: ${message}`)
  }

  function skipWhitespace() {
    while (/\s/.test(text[index] || '')) index += 1
  }

  function parseString() {
    skipWhitespace()
    if (text[index] !== '"') fail('expected string')
    const start = index
    index += 1
    while (index < text.length) {
      if (text[index] === '\\') {
        index += 2
      } else if (text[index] === '"') {
        index += 1
        return JSON.parse(text.slice(start, index))
      } else {
        index += 1
      }
    }
    fail('unterminated string')
  }

  function parseValue(keyPath = []) {
    skipWhitespace()
    if (text[index] === '{') return parseObject(keyPath)
    if (text[index] === '[') return parseArray(keyPath)
    if (text[index] === '"') return parseString()

    const start = index
    while (index < text.length && !/[\s,}\]]/.test(text[index])) index += 1
    if (start === index) fail('expected value')
    return JSON.parse(text.slice(start, index))
  }

  function parseObject(keyPath) {
    const result = {}
    const keys = new Set()
    index += 1
    skipWhitespace()
    if (text[index] === '}') {
      index += 1
      return result
    }

    while (index < text.length) {
      const key = parseString()
      if (keys.has(key)) {
        errors.push(`${relative(file)}: duplicate key ${[...keyPath, key].join('.')}`)
      }
      keys.add(key)
      skipWhitespace()
      if (text[index] !== ':') fail('expected colon')
      index += 1
      result[key] = parseValue([...keyPath, key])
      skipWhitespace()
      if (text[index] === '}') {
        index += 1
        return result
      }
      if (text[index] !== ',') fail('expected comma')
      index += 1
    }
    fail('unterminated object')
  }

  function parseArray(keyPath) {
    const result = []
    index += 1
    skipWhitespace()
    if (text[index] === ']') {
      index += 1
      return result
    }
    while (index < text.length) {
      result.push(parseValue([...keyPath, String(result.length)]))
      skipWhitespace()
      if (text[index] === ']') {
        index += 1
        return result
      }
      if (text[index] !== ',') fail('expected comma')
      index += 1
    }
    fail('unterminated array')
  }

  const result = parseValue()
  skipWhitespace()
  if (index !== text.length) fail('unexpected trailing content')
  return result
}

function readLocale(file) {
  try {
    return parseJsonWithDuplicateKeys(fs.readFileSync(file, 'utf8'), file)
  } catch (error) {
    errors.push(error instanceof Error ? error.message : String(error))
    return {}
  }
}

function flatten(value, prefix = '', output = new Map(), file = '') {
  for (const [key, child] of Object.entries(value)) {
    const fullKey = prefix ? `${prefix}.${key}` : key
    if (typeof child === 'string') {
      output.set(fullKey, child)
    } else if (child && typeof child === 'object' && !Array.isArray(child)) {
      flatten(child, fullKey, output, file)
    } else {
      errors.push(`${file}: translation leaf ${fullKey} must be a string`)
    }
  }
  return output
}

function interpolationVariables(value) {
  const variables = new Set()
  const pattern = /{{\s*-?\s*([A-Za-z0-9_.]+)(?:\s*,[^}]*)?\s*}}/g
  for (const match of value.matchAll(pattern)) variables.add(match[1])
  return [...variables].sort()
}

function compareLocaleSet(target, localeSet, expectedLanguages) {
  const languages = [...localeSet.keys()].sort()
  if (expectedLanguages) {
    for (const language of expectedLanguages) {
      if (!localeSet.has(language)) errors.push(`${target}: missing locale file ${language}.json`)
    }
    for (const language of languages) {
      if (!expectedLanguages.includes(language)) errors.push(`${target}: unexpected locale ${language}; add it to shared locales first`)
    }
  }

  const baseLanguage = localeSet.has('en') ? 'en' : languages[0]
  const base = localeSet.get(baseLanguage) || new Map()
  const allKeys = new Set([...localeSet.values()].flatMap((locale) => [...locale.keys()]))
  for (const key of [...allKeys].sort()) {
    for (const language of languages) {
      if (!localeSet.get(language).has(key)) errors.push(`${target}: missing ${language} key ${key}`)
    }
    if (!base.has(key)) continue

    const baseVars = interpolationVariables(base.get(key))
    for (const language of languages) {
      const value = localeSet.get(language).get(key)
      if (value === undefined) continue
      const variables = interpolationVariables(value)
      if (baseVars.join('|') !== variables.join('|')) {
        errors.push(`${target}: interpolation mismatch ${key} (${baseLanguage}: ${baseVars.join(',') || '-'}; ${language}: ${variables.join(',') || '-'})`)
      }
      if (/(^|[^{]){[A-Za-z_][A-Za-z0-9_.]*}([^}]|$)/.test(value)) {
        errors.push(`${target}: ${language} key ${key} uses single-brace interpolation`)
      }
      if (/<\/?[A-Za-z][^>]*>/.test(value)) {
        errors.push(`${target}: ${language} key ${key} contains HTML; render structure in React instead`)
      }
    }
  }
}

function walkFiles(root, extensions) {
  if (!fs.existsSync(root)) return []
  const files = []
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    if (entry.name === 'node_modules' || entry.name === 'dist' || entry.name === 'build') continue
    const fullPath = path.join(root, entry.name)
    if (entry.isDirectory()) files.push(...walkFiles(fullPath, extensions))
    else if (extensions.some((extension) => entry.name.endsWith(extension))) files.push(fullPath)
  }
  return files
}

const locales = new Map()
let supportedLanguages = []
for (const target of localeTargets) {
  const dir = path.join(workspaceRoot, target.dir)
  const localeSet = new Map()
  const localeFiles = fs.readdirSync(dir)
    .filter((name) => name.endsWith('.json'))
    .sort()

  for (const fileName of localeFiles) {
    const language = path.basename(fileName, '.json')
    const file = path.join(dir, fileName)
    localeSet.set(language, flatten(readLocale(file), '', new Map(), relative(file)))
  }

  if (target.name === 'shared') supportedLanguages = [...localeSet.keys()].sort()
  compareLocaleSet(target.name, localeSet, target.name === 'shared' ? null : supportedLanguages)
  locales.set(target.name, localeSet)
}

const shared = locales.get('shared')
const staticCallPattern = /\b(?:t|i18n\.t|i18next\.t)\(\s*(['"])([^'"\r\n]+)\1/g
for (const target of sourceTargets) {
  const local = target.locale ? locales.get(target.locale) : null
  const effectiveLocales = new Map(
    supportedLanguages.map((language) => [
      language,
      new Set([
        ...shared.get(language).keys(),
        ...(local?.get(language)?.keys() ?? []),
      ]),
    ]),
  )

  for (const file of walkFiles(path.join(workspaceRoot, target.dir), ['.ts', '.tsx'])) {
    const source = fs.readFileSync(file, 'utf8')
    for (const match of source.matchAll(staticCallPattern)) {
      const key = match[2]
      const line = source.slice(0, match.index).split('\n').length
      for (const language of supportedLanguages) {
        if (!effectiveLocales.get(language).has(key)) {
          errors.push(`${relative(file)}:${line}: missing ${language} key ${key}`)
        }
      }
    }

    if (/import\s+i18next\s+from\s+['"]i18next['"]/.test(source)) {
      errors.push(`${relative(file)}: imports the global i18next instance`)
    }
    if (/okText\s*=\s*{\s*t\(['"]common\.saveSuccess['"]\)\s*}/.test(source)) {
      errors.push(`${relative(file)}: uses common.saveSuccess as an action label`)
    }
    if (/title\s*:\s*t\(['"]common\.columnsSettings['"]/.test(source)) {
      errors.push(`${relative(file)}: uses common.columnsSettings as a table action title`)
    }
  }
}

if (errors.length) {
  console.error(`i18n check failed with ${errors.length} issue(s):`)
  errors.forEach((error) => console.error(`- ${error}`))
  process.exit(1)
}

const localeKeyCount = [...locales.values()].reduce(
  (count, localeSet) => count + [...localeSet.values()].reduce((sum, locale) => sum + locale.size, 0),
  0,
)
console.log(`i18n check passed: ${localeTargets.length} locale sets, ${supportedLanguages.length} languages (${supportedLanguages.join(', ')}), ${sourceTargets.length} source trees, ${localeKeyCount} locale entries`)
