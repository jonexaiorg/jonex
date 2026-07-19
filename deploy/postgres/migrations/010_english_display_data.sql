







BEGIN;




UPDATE platform.tenants AS t
SET name = v.name, description = v.description
FROM (VALUES
    ('tenant_jonex_demo',  'Jonex Demo Tenant',       'Local development and demonstration tenant'),
    ('tenant_jonex_alpha', 'Jonex Alpha Test Tenant', 'Tenant selection flow test tenant'),
    ('tenant_jonex_beta',  'Jonex Beta Test Tenant',  'Tenant selection flow test tenant')
) AS v(id, name, description)
WHERE t.id = v.id;

UPDATE platform.users AS u
SET display_name = v.display_name
FROM (VALUES
    ('tenant_jonex_demo',  'admin',              'System Administrator'),
    ('tenant_jonex_demo',  'multi_same_pass',    'Same Credentials User - Demo Tenant'),
    ('tenant_jonex_alpha', 'multi_same_pass',    'Same Credentials User - Alpha Tenant'),
    ('tenant_jonex_demo',  'multi_one_match',    'Single Tenant Password Match - Demo Tenant'),
    ('tenant_jonex_alpha', 'multi_one_match',    'Single Tenant Password Match - Alpha Tenant'),
    ('tenant_jonex_beta',  'tenant_header_user', 'Explicit Tenant Login Test User - Beta Tenant')
) AS v(tenant_id, username, display_name)
WHERE u.tenant_id = v.tenant_id AND u.username = v.username;

UPDATE platform.roles
SET description = CASE name
    WHEN 'admin' THEN 'System administrator role'
    WHEN 'user' THEN 'Standard user role'
    ELSE description
END
WHERE name IN ('admin', 'user');

UPDATE platform.roles
SET name = CASE name
    WHEN U&'\77E5\8BC6\7F16\8F91\8005' THEN 'Knowledge Editor'
    WHEN U&'\89C2\5BDF\8005' THEN 'Observer'
    ELSE name
END,
description = CASE name
    WHEN U&'\77E5\8BC6\7F16\8F91\8005' THEN 'Edits, uploads, and maintains knowledge base documents and data'
    WHEN U&'\89C2\5BDF\8005' THEN 'Read-only access to search and view knowledge'
    ELSE description
END
WHERE name IN (U&'\77E5\8BC6\7F16\8F91\8005', U&'\89C2\5BDF\8005');

UPDATE platform.permissions
SET name = initcap(action) || ' ' || initcap(replace(resource, '_', ' ')),
    description = CASE
        WHEN description ~ U&'[\4E00-\9FA5]' THEN initcap(action) || ' access for ' || replace(resource, '_', ' ')
        ELSE description
    END
WHERE name ~ U&'[\4E00-\9FA5]' OR coalesce(description, '') ~ U&'[\4E00-\9FA5]';

UPDATE platform.menus AS m
SET name = v.name
FROM (VALUES
    (1, 'Platform Management'),
    (2, 'User Management'),
    (3, 'Role Management'),
    (4, 'Menu Management'),
    (5, 'Application Management'),
    (6, 'System Configuration'),
    (7, 'Audit Logs'),
    (8, 'Task Scheduling')
) AS v(id, name)
WHERE m.id = v.id;

UPDATE platform.applications AS a
SET name = v.name, description = v.description
FROM (VALUES
    ('shell',                 'Jonex Shell',          'Unified login and navigation shell'),
    ('core-business',         'Core Business',        'Core business management'),
    ('platform-management',   'Platform Management',  'Platform administration'),
    ('ecosystem-management',  'Ecosystem Management', 'Ecosystem administration')
) AS v(app_code, name, description)
WHERE a.app_code = v.app_code;

UPDATE platform.api_keys
SET name = 'Test API Key'
WHERE api_key = 'jonex_test_key';




UPDATE business_domain.skill_catalog AS s
SET name = v.name,
    description = v.description,
    instruction = v.instruction,
    input_schema_json = v.input_schema::jsonb,
    tags_json = v.tags::jsonb
FROM (VALUES
    (
      'skill_image_recognition',
      'Image Recognition and Analysis',
      'Intelligently analyzes images to identify objects, text, scenes, and other multimodal information, including OCR.',
      'Use this tool when a user needs to identify objects, text, or scenes in an image. Provide an accessible image URL to receive recognition results and confidence scores.',
      '{"type":"object","properties":{"file_url":{"type":"string","description":"Accessible image URL"},"tasks":{"type":"array","items":{"type":"string","enum":["ocr","object_detection","scene_classification"]},"description":"Recognition tasks to perform"}},"required":["file_url"]}',
      '["Image","OCR","Recognition"]'
    ),
    (
      'skill_speech_to_text',
      'Speech to Text',
      'Transcribes speech from audio files into structured text with multilingual recognition and speaker diarization.',
      'Use this tool when a user needs to convert audio or recordings into text. It supports multilingual recognition and speaker diarization.',
      '{"type":"object","properties":{"file_url":{"type":"string","description":"Accessible audio file URL"},"language":{"type":"string","description":"Audio language, for example en-US"},"speaker_diarization":{"type":"boolean","description":"Whether to enable speaker diarization"}},"required":["file_url"]}',
      '["Audio","Transcription","ASR"]'
    ),
    (
      'skill_document_layout',
      'Document Layout Analysis',
      'Analyzes the layout of PDFs and images to identify paragraphs, tables, charts, headers, footers, and other elements.',
      'Use this tool when a user needs to analyze the layout of a PDF or image document. It identifies paragraphs, tables, charts, headers, footers, and other layout elements.',
      '{"type":"object","properties":{"file_url":{"type":"string","description":"Accessible PDF or image document URL"},"output_format":{"type":"string","enum":["json","markdown"],"description":"Output format"}},"required":["file_url"]}',
      '["Document","Layout","Structured Data"]'
    ),
    (
      'skill_video_understanding',
      'Video Content Understanding',
      'Samples and analyzes video frames to identify scenes, actions, people, and event timelines.',
      'Use this tool when a user needs to understand video content. It supports frame sampling, scene recognition, action detection, and timeline extraction.',
      '{"type":"object","properties":{"file_url":{"type":"string","description":"Accessible video file URL"},"sample_rate":{"type":"integer","description":"Frame sampling interval in seconds","default":5}},"required":["file_url"]}',
      '["Video","Frame Sampling","Analysis"]'
    ),
    (
      'skill_multimodal_search',
      'Multimodal Search',
      'Provides unified semantic retrieval and similarity matching across text, images, audio, and other modalities.',
      'Use this tool when a user needs to search across text, images, and audio. It supports semantic understanding and similarity matching.',
      '{"type":"object","properties":{"query":{"type":"string","description":"Search query"},"modalities":{"type":"array","items":{"type":"string","enum":["text","image","audio"]},"description":"Modalities to search"},"top_k":{"type":"integer","description":"Maximum number of results","default":10}},"required":["query"]}',
      '["Search","Multimodal","Semantic"]'
    ),
    (
      'skill_data_extraction',
      'Intelligent Data Extraction',
      'Extracts key fields and structured data from unstructured documents, including tables, forms, invoices, and contracts.',
      'Use this tool when a user needs structured data extracted from an unstructured document. It supports key-field extraction from tables, forms, invoices, contracts, and general documents.',
      '{"type":"object","properties":{"file_url":{"type":"string","description":"Accessible document URL"},"schema":{"type":"object","description":"Definition of fields to extract"},"doc_type":{"type":"string","enum":["invoice","form","contract","table","general"],"description":"Document type"}},"required":["file_url"]}',
      '["Extraction","Structured Data","Document"]'
    )
) AS v(id, name, description, instruction, input_schema, tags)
WHERE s.id = v.id;




UPDATE business_domain.adapters AS a
SET name = v.name, config_json = jsonb_build_object('description', v.description)
FROM (VALUES
    ('adapter_demo_dingtalk',        'ADP Adapter',       'ADP human resources data integration'),
    ('adapter_demo_wechat_agent',    'HiAgent Adapter',   'HiAgent agent platform integration'),
    ('adapter_demo_feishu_analytics','AWS QuickSight',    'AWS analytics platform integration'),
    ('adapter_demo_dingtalk_ai',     'Gemini Adapter',    'Google Gemini model integration'),
    ('adapter_demo_wechat_workbench','WorkBuddy',         'WorkBuddy workflow integration'),
    ('adapter_demo_feishu_crawler',  'Claw Adapter',      'Claw data crawling platform integration')
) AS v(id, name, description)
WHERE a.id = v.id;

UPDATE business_domain.model_providers AS p
SET model_type = v.model_type,
    config_json = jsonb_set(p.config_json, '{vendor}', to_jsonb(v.vendor::text), true)
FROM (VALUES
    ('provider_demo_gpt4o',    'Chat Model',      'OpenAI'),
    ('provider_demo_claude',   'Chat Model',      'Anthropic'),
    ('provider_demo_text2vec', 'Embedding Model', 'Local Deployment'),
    ('provider_demo_reranker', 'Reranking Model', 'Local Deployment')
) AS v(id, model_type, vendor)
WHERE p.id = v.id;

UPDATE business_domain.parser_configs AS p
SET name = v.name, config_json = v.config_json::jsonb
FROM (VALUES
    ('parser_demo_video',    'Video Parser',    '{"version":"v2.3.0","process_count":1245,"display_fields":[{"label":"Keyframe Extraction","value":"Smart Mode"},{"label":"Resolution Limit","value":"1080p"}]}'),
    ('parser_demo_audio',    'Audio Parser',    '{"version":"v2.1.2","process_count":3678,"display_fields":[{"label":"Transcription Model","value":"General Transcription Model"},{"label":"Output Format","value":"SRT"}]}'),
    ('parser_demo_image',    'Image Parser',    '{"version":"v1.9.5","process_count":5432,"display_fields":[{"label":"OCR Engine","value":"Built-in OCR"},{"label":"Image Compression","value":"High Quality"}]}'),
    ('parser_demo_document', 'Document Parser', '{"version":"v3.0.1","process_count":12890,"display_fields":[{"label":"Preserve Layout","value":"Enabled"},{"label":"Table Extraction","value":"Smart Extraction"}]}'),
    ('parser_demo_web',      'Web Parser',      '{"version":"--","process_count":0,"display_fields":[{"label":"Rendering Mode","value":"Static Rendering"},{"label":"Crawl Depth","value":"--"}]}'),
    ('parser_demo_cad',      'CAD Parser',      '{"version":"--","process_count":0,"display_fields":[{"label":"Precision Level","value":"Standard"},{"label":"Layer Extraction","value":"All"}]}')
) AS v(id, name, config_json)
WHERE p.id = v.id;

UPDATE business_domain.data_access_methods AS d
SET name = v.name, config_json = jsonb_build_object('description', v.description)
FROM (VALUES
    ('dam_demo_api',      'API Pull',                  'Ingest data through REST or gRPC APIs'),
    ('dam_api_push_demo', 'Open API Push',             'Receive documents pushed through OpenAPI'),
    ('dam_demo_storage',  'Direct Storage Connection', 'Connect directly to NAS, S3, MinIO, or OSS'),
    ('dam_demo_file',     'File Upload',               'Upload PDF, DOCX, CSV, JSON, and other files'),
    ('dam_demo_mqtt',     'MQTT Integration',          'Ingest data from IoT message queues')
) AS v(id, name, description)
WHERE d.id = v.id;




UPDATE business_domain.template_domains AS d
SET name = v.name, description = v.description
FROM (VALUES
    ('tpl_domain_internet',      'Internet Technology', 'Ontology templates for internet companies, products, and technology intelligence'),
    ('tpl_domain_finance',       'Financial Services',  'Ontology templates for risk control, advisory services, and customer operations'),
    ('tpl_domain_medical',       'Healthcare',          'Ontology templates for medical data parsing and health management'),
    ('tpl_domain_manufacturing', 'Manufacturing',       'Ontology templates for production, quality inspection, and equipment operations')
) AS v(id, name, description)
WHERE d.id = v.id;

UPDATE business_domain.template_scenarios AS s
SET name = v.name, description = v.description
FROM (VALUES
    ('tpl_scenario_internet_general',   'General Internet Intelligence', 'General entity and relationship extraction for internet technology'),
    ('tpl_scenario_credit_risk',        'Credit Risk Control',           'Credit risk assessment based on enterprise financial data'),
    ('tpl_scenario_robo_advisor',       'Robo-Advisor',                  'Automated investment advisory based on market data'),
    ('tpl_scenario_medical_record',     'Medical Record Parsing',        'Structured extraction from electronic medical records'),
    ('tpl_scenario_quality_inspection', 'Production Quality Analysis',   'Quality inspection data analysis for manufacturing processes')
) AS v(id, name, description)
WHERE s.id = v.id;

WITH object_labels(id, name, description) AS (VALUES
    ('tpl_obj_inet_company',              'Company',             'Internet company or platform operator'),
    ('tpl_obj_inet_product',              'Product',             'Application, product, or platform'),
    ('tpl_obj_inet_tech',                 'Technology',          'Framework, protocol, algorithm, or method'),
    ('tpl_obj_inet_feature',              'Feature',             'Product feature or functional module'),
    ('tpl_obj_inet_person',               'Person',              'Founder, executive, or engineer'),
    ('tpl_obj_inet_event',                'Event',               'Launch, financing, or business event'),
    ('tpl_obj_inet_market',               'Market',              'Target market, segment, or audience'),
    ('tpl_obj_inet_investor',             'Investor',            'Venture capital or investment organization'),
    ('tpl_object_enterprise_customer',    'Enterprise Customer', 'Enterprise applying for credit'),
    ('tpl_object_financial_statement',    'Financial Statement', 'Enterprise financial statement data'),
    ('tpl_object_guarantee_company',      'Guarantor Company',   'Enterprise providing a loan guarantee'),
    ('tpl_object_patient_record',         'Patient Record',      'Electronic patient medical record'),
    ('tpl_object_visit_record',           'Visit Record',        'A single patient visit record'),
    ('tpl_object_diagnosis_result',       'Diagnosis Result',    'Clinical diagnosis provided by a physician'),
    ('tpl_obj_mfg_product',               'Manufactured Product','Manufactured product or component'),
    ('tpl_obj_mfg_line',                  'Production Line',     'Manufacturing production line'),
    ('tpl_obj_mfg_defect',                'Quality Defect',      'Defect identified during quality inspection'),
    ('tpl_obj_mfg_inspection',            'Inspection Report',  'Product quality inspection report')
)
UPDATE business_domain.template_objects AS o
SET name = v.name,
    description = v.description,
    aliases = jsonb_build_array(v.name)
FROM object_labels AS v
WHERE o.id = v.id;



UPDATE business_domain.template_attributes
SET attr_name = initcap(replace(ontology_code, '_', ' ')),
    description = 'Business definition for ' || initcap(replace(ontology_code, '_', ' ')),
    attr_type = CASE attr_type
        WHEN U&'\5B57\7B26\4E32' THEN 'string'
        WHEN U&'\6587\672C'   THEN 'text'
        WHEN U&'\6570\503C'   THEN 'number'
        WHEN U&'\65E5\671F'   THEN 'date'
        WHEN U&'\679A\4E3E'   THEN 'enum'
        ELSE attr_type
    END
WHERE id LIKE 'tpl_attr_%'
  AND ontology_code IS NOT NULL;

UPDATE business_domain.template_relations
SET name = initcap(replace(ontology_code, '_', ' ')),
    description = 'Ontology relationship: ' || initcap(replace(ontology_code, '_', ' ')),
    aliases = jsonb_build_array(initcap(replace(ontology_code, '_', ' '))),
    relation_type = CASE relation_type
        WHEN U&'\4E00\5BF9\4E00' THEN 'one_to_one'
        WHEN U&'\4E00\5BF9\591A' THEN 'one_to_many'
        WHEN U&'\591A\5BF9\4E00' THEN 'many_to_one'
        WHEN U&'\591A\5BF9\591A' THEN 'many_to_many'
        ELSE relation_type
    END
WHERE id LIKE 'tpl_rel_%' OR id LIKE 'tpl_relation_%';




UPDATE knowledge_base.spaces
SET name = 'Demo Workspace', description = 'Demonstration workspace'
WHERE id = 'space_demo_test';

UPDATE knowledge_base.knowledge_info AS k
SET name = v.name, description = v.description
FROM (VALUES
    ('kb_demo_internet',    'Internet Technology Knowledge Base', 'Demo knowledge base for internet ontology extraction'),
    ('kb_demo_credit_risk', 'Credit Risk Knowledge Base',         'Demo knowledge base for financial credit risk ontology extraction'),
    ('kb_demo_medical',     'Healthcare Knowledge Base',          'Demo knowledge base for medical record ontology extraction')
) AS v(id, name, description)
WHERE k.id = v.id;

UPDATE knowledge_base.knowledge_data_sources
SET name = 'File Upload'
WHERE id IN ('ds_demo_internet_file', 'ds_demo_credit_file', 'ds_demo_medical_file');

UPDATE knowledge_base.services AS s
SET name = v.name, description = v.description, domain_type = v.domain_type
FROM (VALUES
    ('svc_demo_internet', 'Internet Intelligence Service', 'Test service for internet technology intelligence', 'Technology'),
    ('svc_demo_credit',   'Credit Risk Service',            'Test service for credit risk analysis',              'Finance'),
    ('svc_demo_medical',  'Healthcare Record Service',      'Test service for medical record parsing',            'Healthcare')
) AS v(id, name, description, domain_type)
WHERE s.id = v.id;




CREATE OR REPLACE FUNCTION pg_temp.clean_compiled_display_json(
    p_value jsonb,
    p_parent_key text DEFAULT NULL
) RETURNS jsonb
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    result jsonb;
    item jsonb;
    pair record;
    raw_text text;
BEGIN
    CASE jsonb_typeof(p_value)
        WHEN 'object' THEN
            result := '{}'::jsonb;
            FOR pair IN SELECT key, value FROM jsonb_each(p_value)
            LOOP
                IF pair.key = 'display_name'
                   AND jsonb_typeof(pair.value) = 'string'
                   AND (pair.value #>> '{}') ~ U&'[\4E00-\9FA5]'
                   AND p_value ? 'name'
                THEN
                    result := result || jsonb_build_object(pair.key, p_value -> 'name');
                ELSE
                    result := result || jsonb_build_object(
                        pair.key,
                        pg_temp.clean_compiled_display_json(pair.value, pair.key)
                    );
                END IF;
            END LOOP;
            RETURN result;
        WHEN 'array' THEN
            result := '[]'::jsonb;
            FOR item IN SELECT value FROM jsonb_array_elements(p_value)
            LOOP
                IF p_parent_key = 'aliases'
                   AND jsonb_typeof(item) = 'string'
                   AND (item #>> '{}') ~ U&'[\4E00-\9FA5]'
                THEN
                    CONTINUE;
                END IF;
                result := result || jsonb_build_array(
                    pg_temp.clean_compiled_display_json(item, p_parent_key)
                );
            END LOOP;
            RETURN result;
        WHEN 'string' THEN
            raw_text := p_value #>> '{}';
            IF raw_text ~ U&'[\4E00-\9FA5]' THEN
                RETURN to_jsonb(initcap(replace(coalesce(p_parent_key, 'value'), '_', ' ')));
            END IF;
            RETURN p_value;
        ELSE
            RETURN p_value;
    END CASE;
END;
$$;

UPDATE knowledge_base.ontology_compiled_schemas
SET entity_types = pg_temp.clean_compiled_display_json(entity_types),
    relation_types = pg_temp.clean_compiled_display_json(relation_types),
    prompt_schema = pg_temp.clean_compiled_display_json(prompt_schema)
WHERE entity_types::text ~ U&'[\4E00-\9FA5]'
   OR relation_types::text ~ U&'[\4E00-\9FA5]'
   OR prompt_schema::text ~ U&'[\4E00-\9FA5]';




UPDATE knowledge_base.ontology_compiled_schemas
SET entity_types = replace(
    replace(
    replace(
    replace(
    replace(
    replace(entity_types::text,
        U&'\7EDF\4E00\793E\4F1A\4FE1\7528\4EE3\78011', 'Unified Social Credit Code 1'),
        U&'\516C\53F8\540D\79F0', 'Company Name'),
        U&'\6240\5C5E\884C\4E1A', 'Industry'),
        U&'\6210\7ACB\65F6\95F4', 'Founded Date'),
        U&'\6CE8\518C\8D44\672C', 'Registered Capital'),
        U&'\516C\53F8\7B80\4ECB', 'Company Overview')::jsonb
WHERE knowledge_base_id = 'kb_demo_internet'
  AND entity_types::text ~ U&'[\4E00-\9FA5]';

COMMIT;
