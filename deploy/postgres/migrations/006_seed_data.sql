






INSERT INTO platform.tenants (id, name, description, plan_type)
VALUES ('tenant_jonex_demo', U&'Jonex\6F14\793A\79DF\6237', U&'\672C\5730\5F00\53D1\4E0E\6F14\793A\79DF\6237', 'free')
ON CONFLICT (id) DO NOTHING;


INSERT INTO platform.tenants (id, name, description, plan_type)
VALUES
    ('tenant_jonex_alpha', U&'Jonex Alpha \6D4B\8BD5\79DF\6237', U&'\7528\4E8E\591A\79DF\6237\767B\5F55\9009\62E9\6D41\7A0B\6D4B\8BD5', 'free'),
    ('tenant_jonex_beta', U&'Jonex Beta \6D4B\8BD5\79DF\6237', U&'\7528\4E8E\591A\79DF\6237\767B\5F55\9009\62E9\6D41\7A0B\6D4B\8BD5', 'free')
ON CONFLICT (id) DO NOTHING;


INSERT INTO platform.api_keys (tenant_id, api_key, name, rate_limit)
VALUES ('tenant_jonex_demo', 'jonex_test_key', U&'\6D4B\8BD5\7528 API Key', 1000)
ON CONFLICT (api_key) DO NOTHING;


INSERT INTO platform.users (tenant_id, username, password_hash, display_name, role)
VALUES ('tenant_jonex_demo', 'admin',
        '$2b$12$IRcfNr1RSXcVINY.tBvnGefCYSiMdQLI/BaUk/ARNpVFzr0BVQhCG',
        U&'\7CFB\7EDF\7BA1\7406\5458', 'admin')
ON CONFLICT (tenant_id, username) DO NOTHING;




INSERT INTO platform.users (tenant_id, username, password_hash, display_name, role)
VALUES
    ('tenant_jonex_demo', 'multi_same_pass',
     '$2b$12$IRcfNr1RSXcVINY.tBvnGefCYSiMdQLI/BaUk/ARNpVFzr0BVQhCG',
     U&'\540C\540D\540C\5BC6\7528\6237 - \6F14\793A\79DF\6237', 'admin'),
    ('tenant_jonex_alpha', 'multi_same_pass',
     '$2b$12$IRcfNr1RSXcVINY.tBvnGefCYSiMdQLI/BaUk/ARNpVFzr0BVQhCG',
     U&'\540C\540D\540C\5BC6\7528\6237 - Alpha \79DF\6237', 'admin')
ON CONFLICT (tenant_id, username) DO NOTHING;



INSERT INTO platform.users (tenant_id, username, password_hash, display_name, role)
VALUES
    ('tenant_jonex_demo', 'multi_one_match',
     '$2b$12$IRcfNr1RSXcVINY.tBvnGefCYSiMdQLI/BaUk/ARNpVFzr0BVQhCG',
     U&'\5355\79DF\6237\5BC6\7801\5339\914D\7528\6237 - \6F14\793A\79DF\6237', 'admin'),
    ('tenant_jonex_alpha', 'multi_one_match',
     '$2b$12$A9CcGiSS0l31Ejy8CJNCyeyiIigzyr3hZjzuhpp3PBA9EkbrZyw6O',
     U&'\5355\79DF\6237\5BC6\7801\5339\914D\7528\6237 - Alpha \79DF\6237', 'admin')
ON CONFLICT (tenant_id, username) DO NOTHING;


INSERT INTO platform.users (tenant_id, username, password_hash, display_name, role)
VALUES
    ('tenant_jonex_beta', 'tenant_header_user',
     '$2b$12$IRcfNr1RSXcVINY.tBvnGefCYSiMdQLI/BaUk/ARNpVFzr0BVQhCG',
     U&'\6307\5B9A\79DF\6237\767B\5F55\6D4B\8BD5\7528\6237 - Beta \79DF\6237', 'admin')
ON CONFLICT (tenant_id, username) DO NOTHING;


INSERT INTO platform.roles (tenant_id, name, description, is_system)
VALUES ('tenant_jonex_demo', 'admin', U&'\7CFB\7EDF\7BA1\7406\5458\89D2\8272', 1)
ON CONFLICT DO NOTHING;

INSERT INTO platform.roles (tenant_id, name, description, is_system)
VALUES ('tenant_jonex_demo', 'user', U&'\666E\901A\7528\6237\89D2\8272', 1)
ON CONFLICT DO NOTHING;


INSERT INTO platform.permissions (code, name, resource, action) VALUES
    ('platform:user:read', U&'\67E5\770B\7528\6237', 'user', 'read'),
    ('platform:user:write', U&'\7BA1\7406\7528\6237', 'user', 'write'),
    ('platform:role:read', U&'\67E5\770B\89D2\8272', 'role', 'read'),
    ('platform:role:write', U&'\7BA1\7406\89D2\8272', 'role', 'write'),
    ('platform:menu:read', U&'\67E5\770B\83DC\5355', 'menu', 'read'),
    ('platform:menu:write', U&'\7BA1\7406\83DC\5355', 'menu', 'write'),
    ('platform:app:read', U&'\67E5\770B\5E94\7528', 'application', 'read'),
    ('platform:app:write', U&'\7BA1\7406\5E94\7528', 'application', 'write'),
    ('platform:config:read', U&'\67E5\770B\914D\7F6E', 'system_config', 'read'),
    ('platform:config:write', U&'\7BA1\7406\914D\7F6E', 'system_config', 'write'),
    ('platform:audit:read', U&'\67E5\770B\5BA1\8BA1\65E5\5FD7', 'audit_log', 'read'),
    ('platform:task:read', U&'\67E5\770B\4EFB\52A1', 'task_schedule', 'read'),
    ('platform:task:write', U&'\7BA1\7406\4EFB\52A1', 'task_schedule', 'write')
ON CONFLICT (code) DO NOTHING;


INSERT INTO platform.permissions (id, code, name, resource, action, description) VALUES
    (1, 'tenant:read', U&'\67E5\770B\79DF\6237', 'tenant', 'read', U&'\67E5\770B\79DF\6237\5217\8868\548C\8BE6\60C5'),
    (2, 'tenant:write', U&'\7BA1\7406\79DF\6237', 'tenant', 'write', U&'\521B\5EFA、\7F16\8F91、\5220\9664\79DF\6237'),
    (3, 'user:read', U&'\67E5\770B\7528\6237', 'user', 'read', U&'\67E5\770B\7528\6237\5217\8868\548C\8BE6\60C5'),
    (4, 'user:write', U&'\7BA1\7406\7528\6237', 'user', 'write', U&'\521B\5EFA、\7F16\8F91、\5220\9664\7528\6237'),
    (5, 'role:read', U&'\67E5\770B\89D2\8272', 'role', 'read', U&'\67E5\770B\89D2\8272\548C\6743\9650\914D\7F6E'),
    (6, 'role:write', U&'\7BA1\7406\89D2\8272', 'role', 'write', U&'\521B\5EFA、\7F16\8F91、\5220\9664\89D2\8272，\5206\914D\6743\9650'),
    (7, 'knowledge:read', U&'\67E5\770B\77E5\8BC6', 'knowledge', 'read', U&'\68C0\7D22\548C\67E5\770B\77E5\8BC6\5E93\5185\5BB9'),
    (8, 'knowledge:write', U&'\7F16\8F91\77E5\8BC6', 'knowledge', 'write', U&'\7F16\8F91、\4E0A\4F20、\7EF4\62A4\77E5\8BC6\6587\6863'),
    (9, 'service:read', U&'\67E5\770B\670D\52A1', 'service', 'read', U&'\67E5\770B\9886\57DF\670D\52A1\548C\914D\7F6E'),
    (10, 'service:write', U&'\7BA1\7406\670D\52A1', 'service', 'write', U&'\521B\5EFA\548C\7BA1\7406\9886\57DF\670D\52A1、\77E5\8BC6\5E93、\6570\636E\6E90'),
    (11, 'model:read', U&'\67E5\770B\6A21\578B', 'model', 'read', U&'\67E5\770B\6A21\578B\914D\7F6E\548C\72B6\6001'),
    (12, 'model:write', U&'\7BA1\7406\6A21\578B', 'model', 'write', U&'\914D\7F6E\548C\7BA1\7406\6A21\578B\9002\914D'),
    (13, 'system:read', U&'\67E5\770B\7CFB\7EDF\914D\7F6E', 'system', 'read', U&'\67E5\770B\7CFB\7EDF\914D\7F6E\9879'),
    (14, 'system:write', U&'\7BA1\7406\7CFB\7EDF\914D\7F6E', 'system', 'write', U&'\4FEE\6539\7CFB\7EDF\914D\7F6E')
ON CONFLICT (id) DO NOTHING;


INSERT INTO platform.roles (id, tenant_id, name, description, is_system) VALUES
    (1, 'tenant_jonex_demo', U&'\7CFB\7EDF\7BA1\7406\5458', U&'\62E5\6709\5E73\53F0\5168\90E8\7BA1\7406\6743\9650，\5305\62EC\7CFB\7EDF\914D\7F6E、\7528\6237\7BA1\7406、\79DF\6237\7BA1\7406、\6A21\578B\7BA1\7406\7B49\6240\6709\529F\80FD\6A21\5757', 1),
    (2, 'tenant_jonex_demo', U&'\9886\57DF\670D\52A1\7BA1\7406\5458', U&'\7BA1\7406\9886\57DF\670D\52A1、\77E5\8BC6\5E93、\6570\636E\6E90\7B49\670D\52A1\76F8\5173\914D\7F6E，\53EF\521B\5EFA\548C\7BA1\7406\9886\57DF\7A7A\95F4', 0),
    (3, 'tenant_jonex_demo', U&'\77E5\8BC6\7F16\8F91\8005', U&'\8D1F\8D23\77E5\8BC6\7684\7F16\8F91、\4E0A\4F20\548C\7EF4\62A4，\53EF\7BA1\7406\77E5\8BC6\5E93\4E2D\7684\6587\6863\548C\6570\636E', 0),
    (4, 'tenant_jonex_demo', U&'\89C2\5BDF\8005', U&'\4EC5\53EF\68C0\7D22\548C\67E5\770B\77E5\8BC6，\4E0D\5177\5907\7F16\8F91\548C\7BA1\7406\6743\9650，\9002\7528\4E8E\53EA\8BFB\8BBF\95EE\573A\666F', 0)
ON CONFLICT (id) DO NOTHING;


INSERT INTO platform.role_permissions (tenant_id, role_id, permission_id) VALUES
    ('tenant_jonex_demo', 1, 1), ('tenant_jonex_demo', 1, 2), ('tenant_jonex_demo', 1, 3),
    ('tenant_jonex_demo', 1, 4), ('tenant_jonex_demo', 1, 5), ('tenant_jonex_demo', 1, 6),
    ('tenant_jonex_demo', 1, 7), ('tenant_jonex_demo', 1, 8), ('tenant_jonex_demo', 1, 9),
    ('tenant_jonex_demo', 1, 10), ('tenant_jonex_demo', 1, 11), ('tenant_jonex_demo', 1, 12),
    ('tenant_jonex_demo', 1, 13), ('tenant_jonex_demo', 1, 14),
    ('tenant_jonex_demo', 2, 3), ('tenant_jonex_demo', 2, 5), ('tenant_jonex_demo', 2, 7),
    ('tenant_jonex_demo', 2, 9), ('tenant_jonex_demo', 2, 10),
    ('tenant_jonex_demo', 3, 7), ('tenant_jonex_demo', 3, 8),
    ('tenant_jonex_demo', 4, 3), ('tenant_jonex_demo', 4, 5), ('tenant_jonex_demo', 4, 7),
    ('tenant_jonex_demo', 4, 9), ('tenant_jonex_demo', 4, 11), ('tenant_jonex_demo', 4, 13)
ON CONFLICT DO NOTHING;


INSERT INTO platform.menus (id, parent_id, name, path, icon, app_id, sort_order) VALUES
    (1, 0, U&'\5E73\53F0\7BA1\7406', '/platform', 'SettingOutlined', NULL, 1),
    (2, 1, U&'\7528\6237\7BA1\7406', '/platform/users', 'UserOutlined', NULL, 1),
    (3, 1, U&'\89D2\8272\7BA1\7406', '/platform/roles', 'TeamOutlined', NULL, 2),
    (4, 1, U&'\83DC\5355\7BA1\7406', '/platform/menus', 'MenuOutlined', NULL, 3),
    (5, 1, U&'\5E94\7528\7BA1\7406', '/platform/applications', 'AppstoreOutlined', NULL, 4),
    (6, 1, U&'\7CFB\7EDF\914D\7F6E', '/platform/configs', 'SettingOutlined', NULL, 5),
    (7, 1, U&'\5BA1\8BA1\65E5\5FD7', '/platform/audit-logs', 'FileTextOutlined', NULL, 6),
    (8, 1, U&'\4EFB\52A1\8C03\5EA6', '/platform/tasks', 'ClockCircleOutlined', NULL, 7)
ON CONFLICT DO NOTHING;


INSERT INTO platform.applications (app_code, name, entry_path, description, sort_order) VALUES
    ('shell', 'Jonex Shell', '/', U&'\7EDF\4E00\767B\5F55\5165\53E3\4E0E\5BFC\822A\58F3', 1),
    ('core-business', U&'\6838\5FC3\4E1A\52A1', '/apps/core-business', U&'\6838\5FC3\4E1A\52A1\7BA1\7406', 2),
    ('platform-management', U&'\5E73\53F0\7BA1\7406', '/apps/platform-management', U&'\5E73\53F0\7BA1\7406', 3),
    ('ecosystem-management', U&'\751F\6001\7BA1\7406', '/apps/ecosystem-management', U&'\751F\6001\7BA1\7406', 4)
ON CONFLICT (app_code) DO NOTHING;





INSERT INTO business_domain.skill_catalog (
    id, name, description, category, icon, status,
    tool_name, instruction, input_schema_json, output_schema_json,
    artifact_bucket, artifact_object_key, artifact_checksum, artifact_size, artifact_content_type,
    tags_json, capability_json
) VALUES (
    'skill_image_recognition',
    U&'\56FE\50CF\8BC6\522B\4E0E\5206\6790',
    U&'\5BF9\56FE\7247\5185\5BB9\8FDB\884C\667A\80FD\8BC6\522B，\63D0\53D6\7269\4F53、\6587\5B57、\573A\666F\7B49\591A\6A21\6001\4FE1\606F，\652F\6301OCR\6587\5B57\8BC6\522B',
    'image', 'FileImage', 'published',
    'image_recognition',
    U&'\5F53\7528\6237\9700\8981\8BC6\522B\56FE\7247\4E2D\7684\7269\4F53、\6587\5B57\6216\573A\666F\65F6\8C03\7528\8BE5\5DE5\5177。\4F20\5165\56FE\7247URL，\8FD4\56DE\8BC6\522B\7ED3\679C\548C\7F6E\4FE1\5EA6。',
    U&'{"type":"object","properties":{"file_url":{"type":"string","description":"\53EF\8BBF\95EE\7684\56FE\7247\5730\5740"},"tasks":{"type":"array","items":{"type":"string","enum":["ocr","object_detection","scene_classification"]},"description":"\8BC6\522B\4EFB\52A1\5217\8868"}},"required":["file_url"]}'::jsonb,
    '{"type":"object","properties":{"text":{"type":"string"},"objects":{"type":"array"},"scene":{"type":"string"},"confidence":{"type":"number"}}}'::jsonb,
    'jonex-skills',
    'mcp-tools/image-recognition/latest/image-recognition.zip',
    'sha256:replace_with_real_checksum',
    0, 'application/zip',
    U&'["\56FE\50CF","OCR","\8BC6\522B"]'::jsonb,
    '{"requires_file":true,"supports_batch":true}'::jsonb
) ON CONFLICT (id) DO NOTHING;

INSERT INTO business_domain.skill_catalog (
    id, name, description, category, icon, status,
    tool_name, instruction, input_schema_json, output_schema_json,
    artifact_bucket, artifact_object_key, artifact_checksum, artifact_size, artifact_content_type,
    tags_json, capability_json
) VALUES (
    'skill_speech_to_text',
    U&'\8BED\97F3\8F6C\6587\672C',
    U&'\5C06\97F3\9891\6587\4EF6\4E2D\7684\8BED\97F3\5185\5BB9\81EA\52A8\8F6C\5F55\4E3A\7ED3\6784\5316\6587\672C，\652F\6301\591A\8BED\79CD\548C\8BF4\8BDD\4EBA\5206\79BB',
    'voice', 'Audio', 'published',
    'speech_to_text',
    U&'\5F53\7528\6237\9700\8981\5C06\97F3\9891、\5F55\97F3\8F6C\6362\4E3A\6587\5B57\65F6\8C03\7528\8BE5\5DE5\5177。\652F\6301\591A\8BED\79CD\8BC6\522B\548C\8BF4\8BDD\4EBA\5206\79BB。',
    U&'{"type":"object","properties":{"file_url":{"type":"string","description":"\53EF\8BBF\95EE\7684\97F3\9891\6587\4EF6\5730\5740"},"language":{"type":"string","description":"\97F3\9891\8BED\79CD，\5982 zh-CN"},"speaker_diarization":{"type":"boolean","description":"\662F\5426\542F\7528\8BF4\8BDD\4EBA\5206\79BB"}},"required":["file_url"]}'::jsonb,
    '{"type":"object","properties":{"text":{"type":"string"},"segments":{"type":"array"},"speakers":{"type":"array"}}}'::jsonb,
    'jonex-skills',
    'mcp-tools/speech-to-text/latest/speech-to-text.zip',
    'sha256:replace_with_real_checksum',
    0, 'application/zip',
    U&'["\8BED\97F3","\8F6C\5F55","ASR"]'::jsonb,
    '{"requires_file":true,"supports_batch":true}'::jsonb
) ON CONFLICT (id) DO NOTHING;

INSERT INTO business_domain.skill_catalog (
    id, name, description, category, icon, status,
    tool_name, instruction, input_schema_json, output_schema_json,
    artifact_bucket, artifact_object_key, artifact_checksum, artifact_size, artifact_content_type,
    tags_json, capability_json
) VALUES (
    'skill_document_layout',
    U&'\6587\6863\7248\9762\5206\6790',
    U&'\5206\6790PDF、\56FE\7247\7B49\6587\6863\7684\7248\9762\7ED3\6784，\8BC6\522B\6BB5\843D、\8868\683C、\56FE\8868、\9875\7709\9875\811A\7B49\5143\7D20',
    'document', 'FileText', 'published',
    'document_layout_analysis',
    U&'\5F53\7528\6237\9700\8981\5206\6790PDF\6216\56FE\7247\6587\6863\7684\7248\9762\7ED3\6784\65F6\8C03\7528\8BE5\5DE5\5177。\53EF\8BC6\522B\6BB5\843D、\8868\683C、\56FE\8868、\9875\7709\9875\811A\7B49\7248\9762\5143\7D20。',
    U&'{"type":"object","properties":{"file_url":{"type":"string","description":"\53EF\8BBF\95EE\7684\6587\6863\5730\5740（PDF\6216\56FE\7247）"},"output_format":{"type":"string","enum":["json","markdown"],"description":"\8F93\51FA\683C\5F0F"}},"required":["file_url"]}'::jsonb,
    '{"type":"object","properties":{"pages":{"type":"array"},"elements":{"type":"array"},"structure":{"type":"object"}}}'::jsonb,
    'jonex-skills',
    'mcp-tools/document-layout/latest/document-layout.zip',
    'sha256:replace_with_real_checksum',
    0, 'application/zip',
    U&'["\6587\6863","\7248\9762","\7ED3\6784\5316"]'::jsonb,
    '{"requires_file":true,"supports_batch":false}'::jsonb
) ON CONFLICT (id) DO NOTHING;

INSERT INTO business_domain.skill_catalog (
    id, name, description, category, icon, status,
    tool_name, instruction, input_schema_json, output_schema_json,
    artifact_bucket, artifact_object_key, artifact_checksum, artifact_size, artifact_content_type,
    tags_json, capability_json
) VALUES (
    'skill_video_understanding',
    U&'\89C6\9891\5185\5BB9\7406\89E3',
    U&'\5BF9\89C6\9891\5185\5BB9\8FDB\884C\62BD\5E27\5206\6790，\8BC6\522B\573A\666F、\52A8\4F5C、\4EBA\7269\53CA\4E8B\4EF6\65F6\95F4\7EBF',
    'video', 'VideoCamera', 'published',
    'video_understanding',
    U&'\5F53\7528\6237\9700\8981\7406\89E3\89C6\9891\5185\5BB9\65F6\8C03\7528\8BE5\5DE5\5177。\53EF\8FDB\884C\62BD\5E27\5206\6790、\573A\666F\8BC6\522B、\52A8\4F5C\68C0\6D4B\548C\65F6\95F4\7EBF\63D0\53D6。',
    U&'{"type":"object","properties":{"file_url":{"type":"string","description":"\53EF\8BBF\95EE\7684\89C6\9891\6587\4EF6\5730\5740"},"sample_rate":{"type":"integer","description":"\62BD\5E27\95F4\9694（\79D2）","default":5}},"required":["file_url"]}'::jsonb,
    '{"type":"object","properties":{"scenes":{"type":"array"},"objects":{"type":"array"},"timeline":{"type":"array"},"summary":{"type":"string"}}}'::jsonb,
    'jonex-skills',
    'mcp-tools/video-understanding/latest/video-understanding.zip',
    'sha256:replace_with_real_checksum',
    0, 'application/zip',
    U&'["\89C6\9891","\62BD\5E27","\5206\6790"]'::jsonb,
    '{"requires_file":true,"supports_batch":false}'::jsonb
) ON CONFLICT (id) DO NOTHING;

INSERT INTO business_domain.skill_catalog (
    id, name, description, category, icon, status,
    tool_name, instruction, input_schema_json, output_schema_json,
    artifact_bucket, artifact_object_key, artifact_checksum, artifact_size, artifact_content_type,
    tags_json, capability_json
) VALUES (
    'skill_multimodal_search',
    U&'\591A\6A21\6001\878D\5408\68C0\7D22',
    U&'\8DE8\6587\672C、\56FE\50CF、\8BED\97F3\7B49\591A\6A21\6001\6570\636E\7684\7EDF\4E00\8BED\4E49\68C0\7D22\4E0E\76F8\4F3C\5EA6\5339\914D',
    'fusion', 'Search', 'published',
    'multimodal_search',
    U&'\5F53\7528\6237\9700\8981\8DE8\6587\672C、\56FE\50CF、\8BED\97F3\7B49\591A\6A21\6001\6570\636E\8FDB\884C\68C0\7D22\65F6\8C03\7528\8BE5\5DE5\5177。\652F\6301\8BED\4E49\7406\89E3\548C\76F8\4F3C\5EA6\5339\914D。',
    U&'{"type":"object","properties":{"query":{"type":"string","description":"\68C0\7D22\67E5\8BE2\6587\672C"},"modalities":{"type":"array","items":{"type":"string","enum":["text","image","audio"]},"description":"\68C0\7D22\6A21\6001\8303\56F4"},"top_k":{"type":"integer","description":"\8FD4\56DE\7ED3\679C\6570","default":10}},"required":["query"]}'::jsonb,
    '{"type":"object","properties":{"results":{"type":"array"},"total":{"type":"integer"},"scores":{"type":"array"}}}'::jsonb,
    'jonex-skills',
    'mcp-tools/multimodal-search/latest/multimodal-search.zip',
    'sha256:replace_with_real_checksum',
    0, 'application/zip',
    U&'["\68C0\7D22","\878D\5408","\8BED\4E49"]'::jsonb,
    '{"requires_file":false,"supports_batch":true}'::jsonb
) ON CONFLICT (id) DO NOTHING;

INSERT INTO business_domain.skill_catalog (
    id, name, description, category, icon, status,
    tool_name, instruction, input_schema_json, output_schema_json,
    artifact_bucket, artifact_object_key, artifact_checksum, artifact_size, artifact_content_type,
    tags_json, capability_json
) VALUES (
    'skill_data_extraction',
    U&'\667A\80FD\6570\636E\63D0\53D6',
    U&'\4ECE\975E\7ED3\6784\5316\6587\6863\4E2D\81EA\52A8\63D0\53D6\5173\952E\5B57\6BB5\548C\7ED3\6784\5316\6570\636E，\652F\6301\8868\683C、\8868\5355、\53D1\7968\7B49\573A\666F',
    'custom', 'Database', 'published',
    'data_extraction',
    U&'\5F53\7528\6237\9700\8981\4ECE\975E\7ED3\6784\5316\6587\6863\4E2D\63D0\53D6\7ED3\6784\5316\6570\636E\65F6\8C03\7528\8BE5\5DE5\5177。\652F\6301\8868\683C、\8868\5355、\53D1\7968\7B49\5E38\89C1\6587\6863\7C7B\578B\7684\5173\952E\5B57\6BB5\63D0\53D6。',
    U&'{"type":"object","properties":{"file_url":{"type":"string","description":"\53EF\8BBF\95EE\7684\6587\6863\5730\5740"},"schema":{"type":"object","description":"\671F\671B\63D0\53D6\7684\5B57\6BB5\5B9A\4E49"},"doc_type":{"type":"string","enum":["invoice","form","contract","table","general"],"description":"\6587\6863\7C7B\578B"}},"required":["file_url"]}'::jsonb,
    '{"type":"object","properties":{"extracted_data":{"type":"object"},"confidence":{"type":"number"},"fields_found":{"type":"array"}}}'::jsonb,
    'jonex-skills',
    'mcp-tools/data-extraction/latest/data-extraction.zip',
    'sha256:replace_with_real_checksum',
    0, 'application/zip',
    U&'["\63D0\53D6","\7ED3\6784\5316","\6587\6863"]'::jsonb,
    '{"requires_file":true,"supports_batch":true}'::jsonb
) ON CONFLICT (id) DO NOTHING;


INSERT INTO business_domain.tenant_skills (id, tenant_id, skill_id, status)
VALUES ('tenant_skill_demo_image', 'tenant_jonex_demo', 'skill_image_recognition', 'enabled')
ON CONFLICT (tenant_id, skill_id) DO UPDATE
SET status = EXCLUDED.status, updated_at = CURRENT_TIMESTAMP, is_deleted = 0;

INSERT INTO business_domain.tenant_skills (id, tenant_id, skill_id, status)
VALUES ('tenant_skill_demo_speech', 'tenant_jonex_demo', 'skill_speech_to_text', 'enabled')
ON CONFLICT (tenant_id, skill_id) DO UPDATE
SET status = EXCLUDED.status, updated_at = CURRENT_TIMESTAMP, is_deleted = 0;

INSERT INTO business_domain.tenant_skills (id, tenant_id, skill_id, status)
VALUES ('tenant_skill_demo_layout', 'tenant_jonex_demo', 'skill_document_layout', 'enabled')
ON CONFLICT (tenant_id, skill_id) DO UPDATE
SET status = EXCLUDED.status, updated_at = CURRENT_TIMESTAMP, is_deleted = 0;





INSERT INTO business_domain.adapters (id, tenant_id, name, adapter_type, config_json, status)
VALUES
    ('adapter_demo_dingtalk', 'tenant_jonex_demo', U&'ADP \9002\914D\5668', 'dingtalk',
     U&'{"description":"ADP \4EBA\529B\8D44\6E90\6570\636E\63A5\5165"}'::jsonb, 'connected'),
    ('adapter_demo_wechat_agent', 'tenant_jonex_demo', U&'HiAgent \9002\914D\5668', 'wechat_work',
     U&'{"description":"HiAgent \667A\80FD\4F53\5E73\53F0\96C6\6210"}'::jsonb, 'disconnected'),
    ('adapter_demo_feishu_analytics', 'tenant_jonex_demo', 'AWS QuickSight', 'feishu',
     U&'{"description":"AWS \6570\636E\5206\6790\5E73\53F0\96C6\6210"}'::jsonb, 'disconnected'),
    ('adapter_demo_dingtalk_ai', 'tenant_jonex_demo', U&'Gemini \9002\914D\5668', 'dingtalk',
     U&'{"description":"Google Gemini \6A21\578B\63A5\5165"}'::jsonb, 'disconnected'),
    ('adapter_demo_wechat_workbench', 'tenant_jonex_demo', 'WorkBuddy', 'wechat_work',
     U&'{"description":"WorkBuddy \5DE5\4F5C\6D41\96C6\6210"}'::jsonb, 'disconnected'),
    ('adapter_demo_feishu_crawler', 'tenant_jonex_demo', U&'Claw \9002\914D\5668', 'feishu',
     U&'{"description":"Claw \6570\636E\6293\53D6\5E73\53F0\96C6\6210"}'::jsonb, 'disconnected')
ON CONFLICT (id) DO NOTHING;





INSERT INTO business_domain.model_providers (id, tenant_id, name, provider_type, model_type, model_name, latency_ms, token_limit, vector_dimension, call_count, success_rate, status, config_json)
VALUES
    ('provider_demo_gpt4o', 'tenant_jonex_demo', 'GPT-4o', 'llm', U&'\5BF9\8BDD\6A21\578B', 'gpt-4o', 1200, 128000, NULL, 12458, 99, 'active', '{"vendor":"OpenAI"}'::jsonb),
    ('provider_demo_claude', 'tenant_jonex_demo', 'Claude Opus 4', 'llm', U&'\5BF9\8BDD\6A21\578B', 'claude-opus-4', 1800, 200000, NULL, 8234, 99, 'active', '{"vendor":"Anthropic"}'::jsonb),
    ('provider_demo_text2vec', 'tenant_jonex_demo', 'text2vec-large', 'embedding', U&'\5411\91CF\6A21\578B', 'text2vec-large-chinese', 300, NULL, 768, 56892, 100, 'active', U&'{"vendor":"\672C\5730\90E8\7F72"}'::jsonb),
    ('provider_demo_reranker', 'tenant_jonex_demo', 'bge-reranker', 'reranker', U&'\91CD\6392\5E8F\6A21\578B', 'bge-reranker-v2-m3', 500, NULL, NULL, 23456, 99, 'active', U&'{"vendor":"\672C\5730\90E8\7F72","batch_size":64}'::jsonb)
ON CONFLICT (id) DO NOTHING;













INSERT INTO business_domain.parser_configs (id, tenant_id, name, parser_type, file_types, config_json, status)
VALUES
    ('parser_demo_video', 'tenant_jonex_demo', U&'\89C6\9891\89E3\6790\5668', 'video',
     '["MP4","AVI","MOV","MKV","FLV","WMV","WEBM","M4V","MPG","MPEG","3GP"]'::jsonb,
     U&'{"version":"v2.3.0","process_count":1245,"display_fields":[{"label":"\5173\952E\5E27\63D0\53D6","value":"\667A\80FD\6A21\5F0F"},{"label":"\5206\8FA8\7387\9650\5236","value":"1080p"}]}'::jsonb, 'active'),
    ('parser_demo_audio', 'tenant_jonex_demo', U&'\97F3\9891\89E3\6790\5668', 'audio',
     '["MP3","WAV","FLAC","AAC","M4A","OGG","WMA","OPUS","AMR"]'::jsonb,
     U&'{"version":"v2.1.2","process_count":3678,"display_fields":[{"label":"\8F6C\5199\6A21\578B","value":"\901A\7528\8F6C\5199\6A21\578B"},{"label":"\8F93\51FA\683C\5F0F","value":"SRT"}]}'::jsonb, 'active'),
    ('parser_demo_image', 'tenant_jonex_demo', U&'\56FE\50CF\89E3\6790\5668', 'image',
     '["JPG","JPEG","PNG","GIF","BMP","TIFF","TIF","WEBP"]'::jsonb,
     U&'{"version":"v1.9.5","process_count":5432,"display_fields":[{"label":"OCR \5F15\64CE","value":"\5185\7F6E OCR"},{"label":"\56FE\50CF\538B\7F29","value":"\9AD8\8D28\91CF"}]}'::jsonb, 'active'),
    ('parser_demo_document', 'tenant_jonex_demo', U&'\6587\6863\89E3\6790\5668', 'document',
     '["PDF","DOC","DOCX","PPT","PPTX","XLS","XLSX","TXT","MD"]'::jsonb,
     U&'{"version":"v3.0.1","process_count":12890,"display_fields":[{"label":"\6392\7248\4FDD\7559","value":"\542F\7528"},{"label":"\8868\683C\63D0\53D6","value":"\667A\80FD\63D0\53D6"}]}'::jsonb, 'active'),
    ('parser_demo_web', 'tenant_jonex_demo', U&'\7F51\9875\89E3\6790\5668', 'web',
     '["HTML","HTM","XHTML"]'::jsonb,
     U&'{"version":"--","process_count":0,"display_fields":[{"label":"\6E32\67D3\6A21\5F0F","value":"\9759\6001\6E32\67D3"},{"label":"\6293\53D6\6DF1\5EA6","value":"--"}]}'::jsonb, 'inactive'),
    ('parser_demo_cad', 'tenant_jonex_demo', U&'CAD \89E3\6790\5668', 'cad',
     '["DWG","DXF","STEP"]'::jsonb,
     U&'{"version":"--","process_count":0,"display_fields":[{"label":"\7CBE\5EA6\7B49\7EA7","value":"\6807\51C6"},{"label":"\56FE\5C42\63D0\53D6","value":"\5168\90E8"}]}'::jsonb, 'inactive')
ON CONFLICT (id) DO NOTHING;





INSERT INTO business_domain.data_access_methods (id, tenant_id, name, access_type, config_json, status) VALUES
    ('dam_demo_api', 'tenant_jonex_demo', U&'API \63A5\5165（\62C9\53D6）', 'api', U&'{"description":"\901A\8FC7 REST/gRPC \63A5\53E3\63A5\5165\6570\636E"}'::jsonb, 'active'),
    ('dam_api_push_demo', 'tenant_jonex_demo', U&'API \5F00\653E（\63A8\9001）', 'api_push', U&'{"description":"\5916\90E8\7CFB\7EDF\901A\8FC7 OpenAPI \63A8\9001\6587\6863\5165\5E93"}'::jsonb, 'active'),
    ('dam_demo_storage', 'tenant_jonex_demo', U&'\6587\4EF6\5B58\50A8\76F4\8FDE', 'storage', U&'{"description":"NAS/S3/MinIO/OSS \7B49"}'::jsonb, 'active'),
    ('dam_demo_file', 'tenant_jonex_demo', U&'\6587\4EF6\4E0A\4F20', 'file', U&'{"description":"PDF/DOCX/CSV/JSON \7B49"}'::jsonb, 'active'),
    ('dam_demo_mqtt', 'tenant_jonex_demo', U&'MQTT \63A5\5165', 'mqtt', U&'{"description":"\7269\8054\7F51\6D88\606F\961F\5217\63A5\5165"}'::jsonb, 'inactive')
ON CONFLICT (id) DO NOTHING;






INSERT INTO business_domain.template_domains (id, tenant_id, name, description, status, version, published_at, structure_hash)
VALUES ('tpl_domain_internet', 'tenant_jonex_demo', U&'\4E92\8054\7F51', U&'\4E92\8054\7F51\79D1\6280\516C\53F8/\4EA7\54C1/\6280\672F\60C5\62A5\6A21\677F\9886\57DF', 'active', 1,
        '2026-06-01T00:00:00+00'::timestamptz,
        'b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0abc1de')
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_domain.template_scenarios (id, tenant_id, domain_id, name, description, config_json, version, published_at, structure_hash)
VALUES ('tpl_scenario_internet_general', 'tenant_jonex_demo', 'tpl_domain_internet', U&'\901A\7528', U&'\4E92\8054\7F51\901A\7528\5B9E\4F53/\5173\7CFB\62BD\53D6\573A\666F', '{}'::jsonb, 1,
        '2026-06-01T00:00:00+00'::timestamptz,
        'b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0abc1de')
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_domain.template_objects (id, tenant_id, domain_id, scenario_id, name, description, status, ontology_code, aliases)
VALUES
 ('tpl_obj_inet_company','tenant_jonex_demo','tpl_domain_internet','tpl_scenario_internet_general',U&'\516C\53F8',U&'\4E92\8054\7F51\516C\53F8/\5E73\53F0\65B9','active','Company',U&'["\516C\53F8","\4F01\4E1A","\5382\5546","\5E73\53F0\65B9","\673A\6784","Organization"]'::jsonb),
 ('tpl_obj_inet_product','tenant_jonex_demo','tpl_domain_internet','tpl_scenario_internet_general',U&'\4EA7\54C1',U&'App/\5E94\7528/\5E73\53F0','active','Product',U&'["\4EA7\54C1","App","\5E94\7528","\5E73\53F0","Product"]'::jsonb),
 ('tpl_obj_inet_tech','tenant_jonex_demo','tpl_domain_internet','tpl_scenario_internet_general',U&'\6280\672F',U&'\6846\67B6/\534F\8BAE/\7B97\6CD5','active','Technology',U&'["\6280\672F","\6846\67B6","\534F\8BAE","\7B97\6CD5","\65B9\6CD5","Method"]'::jsonb),
 ('tpl_obj_inet_feature','tenant_jonex_demo','tpl_domain_internet','tpl_scenario_internet_general',U&'\529F\80FD\7279\6027',U&'\4EA7\54C1\529F\80FD/\6A21\5757','active','Feature',U&'["\529F\80FD","\7279\6027","\6A21\5757","\6982\5FF5","Concept"]'::jsonb),
 ('tpl_obj_inet_person','tenant_jonex_demo','tpl_domain_internet','tpl_scenario_internet_general',U&'\4EBA\5458',U&'\521B\59CB\4EBA/\9AD8\7BA1/\5DE5\7A0B\5E08','active','Person',U&'["\4EBA\5458","\521B\59CB\4EBA","\9AD8\7BA1","\5DE5\7A0B\5E08","\4EBA","Person"]'::jsonb),
 ('tpl_obj_inet_event','tenant_jonex_demo','tpl_domain_internet','tpl_scenario_internet_general',U&'\4E8B\4EF6',U&'\53D1\5E03\4F1A/\878D\8D44/\6D3B\52A8','active','Event',U&'["\4E8B\4EF6","\53D1\5E03\4F1A","\878D\8D44","\6D3B\52A8","Event"]'::jsonb),
 ('tpl_obj_inet_market','tenant_jonex_demo','tpl_domain_internet','tpl_scenario_internet_general',U&'\5E02\573A',U&'\7528\6237\7FA4\4F53/\8D5B\9053','active','Market',U&'["\5E02\573A","\7528\6237\7FA4\4F53","\8D5B\9053","\9886\57DF"]'::jsonb),
 ('tpl_obj_inet_investor','tenant_jonex_demo','tpl_domain_internet','tpl_scenario_internet_general',U&'\6295\8D44\673A\6784',U&'VC/\8D44\672C/\6295\8D44\65B9','active','Investor',U&'["\6295\8D44\673A\6784","\8D44\672C","VC","\6295\8D44\65B9"]'::jsonb)
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_domain.template_attributes
    (id, tenant_id, template_object_id, attr_name, description, attr_type, is_primary_key, constraints_json, sort_order, ontology_code, is_required)
VALUES

    ('tpl_attr_inet_co_code','tenant_jonex_demo','tpl_obj_inet_company',U&'\7EDF\4E00\793E\4F1A\4FE1\7528\4EE3\7801',U&'\4F01\4E1A\552F\4E00\8EAB\4EFD\8BC6\522B\4EE3\7801',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'unified_social_credit_code',1),
    ('tpl_attr_inet_co_name','tenant_jonex_demo','tpl_obj_inet_company',U&'\516C\53F8\540D\79F0',U&'\5DE5\5546\767B\8BB0\4F01\4E1A\5168\79F0',U&'\5B57\7B26\4E32',0,'{}'::jsonb,2,'company_name',1),
    ('tpl_attr_inet_co_industry','tenant_jonex_demo','tpl_obj_inet_company',U&'\6240\5C5E\884C\4E1A',U&'\884C\4E1A\5206\7C7B，\5982\7535\5546、\793E\4EA4、\91D1\878D\79D1\6280\7B49',U&'\679A\4E3E',0,'{}'::jsonb,3,'industry',0),
    ('tpl_attr_inet_co_founded','tenant_jonex_demo','tpl_obj_inet_company',U&'\6210\7ACB\65F6\95F4',U&'\516C\53F8\6210\7ACB\65E5\671F',U&'\65E5\671F',0,'{}'::jsonb,4,'founded',0),
    ('tpl_attr_inet_co_capital','tenant_jonex_demo','tpl_obj_inet_company',U&'\6CE8\518C\8D44\672C',U&'\6CE8\518C\8D44\672C\91D1\989D（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,5,'registered_capital',0),
    ('tpl_attr_inet_co_summary','tenant_jonex_demo','tpl_obj_inet_company',U&'\516C\53F8\7B80\4ECB',U&'\516C\53F8\4E3B\8425\4E1A\52A1\4E0E\6838\5FC3\7ADE\4E89\529B\6982\8FF0',U&'\6587\672C',0,'{}'::jsonb,6,'company_summary',0),

    ('tpl_attr_inet_pd_name','tenant_jonex_demo','tpl_obj_inet_product',U&'\4EA7\54C1\540D\79F0',U&'\4EA7\54C1/\5E94\7528/\5E73\53F0\540D\79F0',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'product_name',1),
    ('tpl_attr_inet_pd_category','tenant_jonex_demo','tpl_obj_inet_product',U&'\7C7B\522B',U&'\4EA7\54C1\7C7B\522B，\5982 App、SaaS、\5E73\53F0\7B49',U&'\679A\4E3E',0,'{}'::jsonb,2,'category',0),
    ('tpl_attr_inet_pd_platform','tenant_jonex_demo','tpl_obj_inet_product',U&'\5E73\53F0',U&'\6240\5C5E\5E73\53F0，\5982 iOS、Android、Web \7B49',U&'\679A\4E3E',0,'{}'::jsonb,3,'platform',0),
    ('tpl_attr_inet_pd_users','tenant_jonex_demo','tpl_obj_inet_product',U&'\7528\6237\89C4\6A21',U&'\6708\6D3B\7528\6237\6570\6216\6CE8\518C\7528\6237\6570',U&'\6570\503C',0,'{}'::jsonb,4,'user_scale',0),
    ('tpl_attr_inet_pd_desc','tenant_jonex_demo','tpl_obj_inet_product',U&'\4EA7\54C1\63CF\8FF0',U&'\4EA7\54C1\529F\80FD\4E0E\6838\5FC3\4EF7\503C\63CF\8FF0',U&'\6587\672C',0,'{}'::jsonb,5,'product_description',0),

    ('tpl_attr_inet_tech_name','tenant_jonex_demo','tpl_obj_inet_tech',U&'\6280\672F\540D\79F0',U&'\6280\672F/\6846\67B6/\534F\8BAE\540D\79F0',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'tech_name',1),
    ('tpl_attr_inet_tech_category','tenant_jonex_demo','tpl_obj_inet_tech',U&'\6280\672F\5206\7C7B',U&'\5982\524D\7AEF\6846\67B6、\540E\7AEF\6846\67B6、\6570\636E\5E93、AI\7B97\6CD5\7B49',U&'\679A\4E3E',0,'{}'::jsonb,2,'tech_category',0),
    ('tpl_attr_inet_tech_desc','tenant_jonex_demo','tpl_obj_inet_tech',U&'\6280\672F\63CF\8FF0',U&'\6280\672F\539F\7406\4E0E\5E94\7528\573A\666F\8BF4\660E',U&'\6587\672C',0,'{}'::jsonb,3,'tech_description',0),

    ('tpl_attr_inet_feat_name','tenant_jonex_demo','tpl_obj_inet_feature',U&'\7279\6027\540D\79F0',U&'\529F\80FD/\6A21\5757\540D\79F0',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'feature_name',1),
    ('tpl_attr_inet_feat_desc','tenant_jonex_demo','tpl_obj_inet_feature',U&'\7279\6027\63CF\8FF0',U&'\529F\80FD\7279\6027\8BF4\660E',U&'\6587\672C',0,'{}'::jsonb,2,'feature_description',0),

    ('tpl_attr_inet_per_name','tenant_jonex_demo','tpl_obj_inet_person',U&'\59D3\540D',U&'\4EBA\5458\59D3\540D',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'person_name',1),
    ('tpl_attr_inet_per_title','tenant_jonex_demo','tpl_obj_inet_person',U&'\804C\4F4D',U&'\804C\7EA7/\5934\8854',U&'\5B57\7B26\4E32',0,'{}'::jsonb,2,'title',0),
    ('tpl_attr_inet_per_company','tenant_jonex_demo','tpl_obj_inet_person',U&'\6240\5C5E\516C\53F8',U&'\4EFB\804C\516C\53F8/\673A\6784',U&'\5B57\7B26\4E32',0,'{}'::jsonb,3,'affiliated_company',0),
    ('tpl_attr_inet_per_bio','tenant_jonex_demo','tpl_obj_inet_person',U&'\7B80\4ECB',U&'\4E2A\4EBA\5C65\5386\4E0E\6210\5C31\6458\8981',U&'\6587\672C',0,'{}'::jsonb,4,'biography',0),

    ('tpl_attr_inet_ev_name','tenant_jonex_demo','tpl_obj_inet_event',U&'\4E8B\4EF6\540D\79F0',U&'\4E8B\4EF6\6807\9898',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'event_name',1),
    ('tpl_attr_inet_ev_type','tenant_jonex_demo','tpl_obj_inet_event',U&'\4E8B\4EF6\7C7B\578B',U&'\5982\53D1\5E03\4F1A、\878D\8D44、\6536\8D2D、\5408\4F5C\7B49',U&'\679A\4E3E',0,'{}'::jsonb,2,'event_type',0),
    ('tpl_attr_inet_ev_date','tenant_jonex_demo','tpl_obj_inet_event',U&'\65E5\671F',U&'\4E8B\4EF6\53D1\751F\65E5\671F',U&'\65E5\671F',0,'{}'::jsonb,3,'event_date',0),
    ('tpl_attr_inet_ev_desc','tenant_jonex_demo','tpl_obj_inet_event',U&'\4E8B\4EF6\63CF\8FF0',U&'\4E8B\4EF6\8BE6\60C5\6458\8981',U&'\6587\672C',0,'{}'::jsonb,4,'event_description',0),

    ('tpl_attr_inet_mkt_name','tenant_jonex_demo','tpl_obj_inet_market',U&'\5E02\573A\540D\79F0',U&'\76EE\6807\5E02\573A/\8D5B\9053\540D\79F0',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'market_name',1),
    ('tpl_attr_inet_mkt_size','tenant_jonex_demo','tpl_obj_inet_market',U&'\5E02\573A\89C4\6A21',U&'\5E02\573A\89C4\6A21\4F30\503C（\4EBF\5143）',U&'\6570\503C',0,'{}'::jsonb,2,'market_size',0),
    ('tpl_attr_inet_mkt_desc','tenant_jonex_demo','tpl_obj_inet_market',U&'\5E02\573A\63CF\8FF0',U&'\76EE\6807\5E02\573A\7279\5F81\4E0E\8D8B\52BF\63CF\8FF0',U&'\6587\672C',0,'{}'::jsonb,3,'market_description',0),

    ('tpl_attr_inet_inv_name','tenant_jonex_demo','tpl_obj_inet_investor',U&'\673A\6784\540D\79F0',U&'\6295\8D44\673A\6784\5168\79F0',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'investor_name',1),
    ('tpl_attr_inet_inv_type','tenant_jonex_demo','tpl_obj_inet_investor',U&'\673A\6784\7C7B\578B',U&'\5982 VC、PE、CVC、\5929\4F7F\6295\8D44\7B49',U&'\679A\4E3E',0,'{}'::jsonb,2,'investor_type',0),
    ('tpl_attr_inet_inv_aum','tenant_jonex_demo','tpl_obj_inet_investor',U&'\7BA1\7406\89C4\6A21',U&'\8D44\4EA7\7BA1\7406\89C4\6A21（\4EBF\5143）',U&'\6570\503C',0,'{}'::jsonb,3,'aum',0),
    ('tpl_attr_inet_inv_desc','tenant_jonex_demo','tpl_obj_inet_investor',U&'\673A\6784\7B80\4ECB',U&'\6295\8D44\98CE\683C、\8D5B\9053\504F\597D\4E0E\4EE3\8868\6848\4F8B',U&'\6587\672C',0,'{}'::jsonb,4,'investor_description',0)
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_domain.template_relations
    (id, tenant_id, domain_id, scenario_id, name, description, source_object_id, target_object_id, relation_type, status, ontology_code, aliases)
VALUES
 ('tpl_rel_inet_develops','tenant_jonex_demo','tpl_domain_internet','tpl_scenario_internet_general',U&'\5F00\53D1',U&'\516C\53F8\5F00\53D1/\63A8\51FA\4EA7\54C1','tpl_obj_inet_company','tpl_obj_inet_product',U&'\4E00\5BF9\591A','active','DEVELOPS',U&'["\5F00\53D1","\63A8\51FA"]'::jsonb),
 ('tpl_rel_inet_usestech','tenant_jonex_demo','tpl_domain_internet','tpl_scenario_internet_general',U&'\91C7\7528\6280\672F',U&'\4EA7\54C1\91C7\7528\7684\6280\672F\6808/\6846\67B6','tpl_obj_inet_product','tpl_obj_inet_tech',U&'\591A\5BF9\591A','active','USES_TECH',U&'["\91C7\7528","\4F7F\7528\6280\672F"]'::jsonb),
 ('tpl_rel_inet_hasfeature','tenant_jonex_demo','tpl_domain_internet','tpl_scenario_internet_general',U&'\5177\5907\529F\80FD',U&'\4EA7\54C1\5177\5907\7684\529F\80FD\7279\6027','tpl_obj_inet_product','tpl_obj_inet_feature',U&'\4E00\5BF9\591A','active','HAS_FEATURE',U&'["\5177\5907\529F\80FD","\5305\542B"]'::jsonb),
 ('tpl_rel_inet_foundedby','tenant_jonex_demo','tpl_domain_internet','tpl_scenario_internet_general',U&'\521B\7ACB',U&'\516C\53F8\7531\4EBA\5458\521B\7ACB','tpl_obj_inet_company','tpl_obj_inet_person',U&'\591A\5BF9\591A','active','FOUNDED_BY',U&'["\521B\7ACB","\521B\529E"]'::jsonb),
 ('tpl_rel_inet_worksat','tenant_jonex_demo','tpl_domain_internet','tpl_scenario_internet_general',U&'\4EFB\804C',U&'\4EBA\5458\5728\67D0\516C\53F8\4EFB\804C','tpl_obj_inet_person','tpl_obj_inet_company',U&'\591A\5BF9\4E00','active','WORKS_AT',U&'["\4EFB\804C","\5C31\804C"]'::jsonb),
 ('tpl_rel_inet_invests','tenant_jonex_demo','tpl_domain_internet','tpl_scenario_internet_general',U&'\6295\8D44',U&'\6295\8D44\673A\6784\6295\8D44\67D0\516C\53F8','tpl_obj_inet_investor','tpl_obj_inet_company',U&'\591A\5BF9\591A','active','INVESTS_IN',U&'["\6295\8D44","\6CE8\8D44"]'::jsonb),
 ('tpl_rel_inet_competes','tenant_jonex_demo','tpl_domain_internet','tpl_scenario_internet_general',U&'\7ADE\4E89',U&'\4EA7\54C1\4E4B\95F4\7684\7ADE\4E89\5173\7CFB','tpl_obj_inet_product','tpl_obj_inet_product',U&'\591A\5BF9\591A','active','COMPETES_WITH',U&'["\7ADE\4E89","\5BF9\6807"]'::jsonb),
 ('tpl_rel_inet_targets','tenant_jonex_demo','tpl_domain_internet','tpl_scenario_internet_general',U&'\9762\5411',U&'\4EA7\54C1\9762\5411\7684\76EE\6807\5E02\573A','tpl_obj_inet_product','tpl_obj_inet_market',U&'\591A\5BF9\4E00','active','TARGETS',U&'["\9762\5411","\5B9A\4F4D"]'::jsonb),
 ('tpl_rel_inet_participates','tenant_jonex_demo','tpl_domain_internet','tpl_scenario_internet_general',U&'\53C2\4E0E',U&'\516C\53F8\53C2\4E0E/\7EC4\7EC7\4E8B\4EF6','tpl_obj_inet_company','tpl_obj_inet_event',U&'\591A\5BF9\591A','active','PARTICIPATES',U&'["\53C2\4E0E","\51FA\5E2D"]'::jsonb)
ON CONFLICT (id) DO NOTHING;






INSERT INTO business_domain.template_domains (id, tenant_id, name, description, status, version, published_at, structure_hash)
VALUES ('tpl_domain_finance', 'tenant_jonex_demo', U&'\91D1\878D\884C\4E1A', U&'\91D1\878D\673A\6784\98CE\63A7、\6295\987E\4E0E\5BA2\6237\7ECF\8425\6A21\677F\9886\57DF', 'active', 1,
        '2026-06-01T00:00:00+00'::timestamptz,
        '0476f5786a7e292d7a2aaaed06a06b6787b96a746da8818e3869cf2cd71f9777')
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_domain.template_scenarios (id, tenant_id, domain_id, name, description, config_json, version, published_at, structure_hash)
VALUES
    ('tpl_scenario_credit_risk', 'tenant_jonex_demo', 'tpl_domain_finance', U&'\4FE1\8D37\98CE\63A7', U&'\57FA\4E8E\4F01\4E1A\8D22\52A1\6570\636E\7684\4FE1\8D37\98CE\9669\8BC4\4F30\573A\666F', '{}'::jsonb, 1,
     '2026-06-01T00:00:00+00'::timestamptz, '0476f5786a7e292d7a2aaaed06a06b6787b96a746da8818e3869cf2cd71f9777'),
    ('tpl_scenario_robo_advisor', 'tenant_jonex_demo', 'tpl_domain_finance', U&'\667A\80FD\6295\987E', U&'\57FA\4E8E\5E02\573A\884C\60C5\7684\667A\80FD\6295\8D44\987E\95EE\573A\666F', '{}'::jsonb, 1,
     '2026-06-01T00:00:00+00'::timestamptz, '6140449c1d747a2622f6c4d8dbc1542c07c26a250a7b9735c670dbbfd0ca62c1')
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_domain.template_objects (id, tenant_id, domain_id, scenario_id, name, description, status, ontology_code, aliases)
VALUES
    ('tpl_object_enterprise_customer', 'tenant_jonex_demo', 'tpl_domain_finance', 'tpl_scenario_credit_risk', U&'\4F01\4E1A\5BA2\6237', U&'\8D37\6B3E\7533\8BF7\4F01\4E1A\4E3B\4F53\4FE1\606F', 'active', 'enterprise_customer', U&'["\8D37\6B3E\7533\8BF7\4F01\4E1A","\5BA2\6237\4E3B\4F53"]'::jsonb),
    ('tpl_object_financial_statement', 'tenant_jonex_demo', 'tpl_domain_finance', 'tpl_scenario_credit_risk', U&'\8D22\52A1\62A5\8868', U&'\4F01\4E1A\8D22\52A1\62A5\8868\6570\636E', 'active', 'financial_statement', U&'["\8D22\62A5","\8D22\52A1\62A5\544A"]'::jsonb),
    ('tpl_object_guarantee_company', 'tenant_jonex_demo', 'tpl_domain_finance', 'tpl_scenario_credit_risk', U&'\62C5\4FDD\4F01\4E1A', U&'\4E3A\8D37\6B3E\7533\8BF7\63D0\4F9B\62C5\4FDD\7684\4F01\4E1A\4E3B\4F53', 'active', 'guarantee_company', U&'["\62C5\4FDD\65B9","\4FDD\8BC1\4F01\4E1A"]'::jsonb)
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_domain.template_attributes
    (id, tenant_id, template_object_id, attr_name, description, attr_type, is_primary_key, constraints_json, sort_order, ontology_code, is_required)
VALUES

    ('tpl_attr_enterprise_code', 'tenant_jonex_demo', 'tpl_object_enterprise_customer', U&'\7EDF\4E00\793E\4F1A\4FE1\7528\4EE3\7801', U&'\4F01\4E1A\552F\4E00\8EAB\4EFD\8BC6\522B\4EE3\7801', U&'\5B57\7B26\4E32', 1, '{}'::jsonb, 1, 'unified_social_credit_code', 1),
    ('tpl_attr_enterprise_name', 'tenant_jonex_demo', 'tpl_object_enterprise_customer', U&'\4F01\4E1A\540D\79F0', U&'\5DE5\5546\767B\8BB0\4F01\4E1A\540D\79F0', U&'\5B57\7B26\4E32', 0, '{}'::jsonb, 2, 'enterprise_name', 1),
    ('tpl_attr_enterprise_capital', 'tenant_jonex_demo', 'tpl_object_enterprise_customer', U&'\6CE8\518C\8D44\672C', U&'\4F01\4E1A\6CE8\518C\8D44\672C\91D1\989D', U&'\6570\503C', 0, '{}'::jsonb, 3, 'registered_capital', 0),
    ('tpl_attr_enterprise_date', 'tenant_jonex_demo', 'tpl_object_enterprise_customer', U&'\6210\7ACB\65E5\671F', U&'\4F01\4E1A\6210\7ACB\65E5\671F', U&'\65E5\671F', 0, '{}'::jsonb, 4, 'establishment_date', 0),

    ('tpl_attr_statement_id', 'tenant_jonex_demo', 'tpl_object_financial_statement', U&'\62A5\8868ID', U&'\8D22\52A1\62A5\8868\552F\4E00\7F16\53F7', U&'\5B57\7B26\4E32', 1, '{}'::jsonb, 1, 'statement_id', 1),
    ('tpl_attr_statement_type', 'tenant_jonex_demo', 'tpl_object_financial_statement', U&'\62A5\8868\7C7B\578B', U&'\8D44\4EA7\8D1F\503A\8868、\5229\6DA6\8868\7B49', U&'\679A\4E3E', 0, '{}'::jsonb, 2, 'statement_type', 0),
    ('tpl_attr_statement_period', 'tenant_jonex_demo', 'tpl_object_financial_statement', U&'\62A5\544A\671F', U&'\8D22\52A1\62A5\544A\6240\5C5E\671F\95F4', U&'\65E5\671F', 0, '{}'::jsonb, 3, 'reporting_period', 0),
    ('tpl_attr_statement_revenue', 'tenant_jonex_demo', 'tpl_object_financial_statement', U&'\8425\4E1A\6536\5165', U&'\62A5\544A\671F\5185\8425\4E1A\6536\5165', U&'\6570\503C', 0, '{}'::jsonb, 4, 'operating_revenue', 0),
    ('tpl_attr_statement_profit', 'tenant_jonex_demo', 'tpl_object_financial_statement', U&'\51C0\5229\6DA6', U&'\62A5\544A\671F\5185\51C0\5229\6DA6', U&'\6570\503C', 0, '{}'::jsonb, 5, 'net_profit', 0),

    ('tpl_attr_guarantee_code', 'tenant_jonex_demo', 'tpl_object_guarantee_company', U&'\7EDF\4E00\793E\4F1A\4FE1\7528\4EE3\7801', U&'\62C5\4FDD\4F01\4E1A\552F\4E00\8EAB\4EFD\8BC6\522B\4EE3\7801', U&'\5B57\7B26\4E32', 1, '{}'::jsonb, 1, 'guarantee_credit_code', 1),
    ('tpl_attr_guarantee_name', 'tenant_jonex_demo', 'tpl_object_guarantee_company', U&'\4F01\4E1A\540D\79F0', U&'\62C5\4FDD\4F01\4E1A\5DE5\5546\767B\8BB0\540D\79F0', U&'\5B57\7B26\4E32', 0, '{}'::jsonb, 2, 'guarantee_name', 1),
    ('tpl_attr_guarantee_amount', 'tenant_jonex_demo', 'tpl_object_guarantee_company', U&'\62C5\4FDD\91D1\989D', U&'\4E3A\672C\7B14\8D37\6B3E\63D0\4F9B\7684\62C5\4FDD\91D1\989D（\4E07\5143）', U&'\6570\503C', 0, '{}'::jsonb, 3, 'guarantee_amount', 0)
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_domain.template_relations
    (id, tenant_id, domain_id, scenario_id, name, description, source_object_id, target_object_id, relation_type, status, ontology_code, aliases)
VALUES
    ('tpl_relation_customer_statement', 'tenant_jonex_demo', 'tpl_domain_finance', 'tpl_scenario_credit_risk', U&'\6301\6709', U&'\4F01\4E1A\5BA2\6237\6301\6709\8D22\52A1\62A5\8868\7684\5173\7CFB', 'tpl_object_enterprise_customer', 'tpl_object_financial_statement', U&'\4E00\5BF9\591A', 'active', 'owns_financial_statement', U&'["\6301\6709","\62E5\6709"]'::jsonb),
    ('tpl_relation_customer_guarantee', 'tenant_jonex_demo', 'tpl_domain_finance', 'tpl_scenario_credit_risk', U&'\62C5\4FDD', U&'\4F01\4E1A\95F4\62C5\4FDD\5173\7CFB', 'tpl_object_enterprise_customer', 'tpl_object_guarantee_company', U&'\591A\5BF9\591A', 'active', 'guaranteed_by', U&'["\62C5\4FDD","\4FDD\8BC1"]'::jsonb)
ON CONFLICT (id) DO NOTHING;






INSERT INTO business_domain.template_domains (id, tenant_id, name, description, status, version, published_at, structure_hash)
VALUES ('tpl_domain_medical', 'tenant_jonex_demo', U&'\533B\7597\5065\5EB7', U&'\533B\7597\6570\636E\89E3\6790\4E0E\5065\5EB7\7BA1\7406\6A21\677F\9886\57DF', 'active', 1,
        '2026-06-01T00:00:00+00'::timestamptz,
        '6b518c74048be883c991406f509f03b1921f062a5ed0a7c1167e85e1886f38ba')
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_domain.template_scenarios (id, tenant_id, domain_id, name, description, config_json, version, published_at, structure_hash)
VALUES ('tpl_scenario_medical_record', 'tenant_jonex_demo', 'tpl_domain_medical', U&'\75C5\5386\667A\80FD\89E3\6790', U&'\7535\5B50\75C5\5386\6587\672C\7684\7ED3\6784\5316\89E3\6790\573A\666F', '{}'::jsonb, 1,
        '2026-06-01T00:00:00+00'::timestamptz,
        '6b518c74048be883c991406f509f03b1921f062a5ed0a7c1167e85e1886f38ba')
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_domain.template_objects (id, tenant_id, domain_id, scenario_id, name, description, status, ontology_code, aliases)
VALUES
    ('tpl_object_patient_record', 'tenant_jonex_demo', 'tpl_domain_medical', 'tpl_scenario_medical_record', U&'\60A3\8005\75C5\5386', U&'\60A3\8005\7535\5B50\75C5\5386\4FE1\606F', 'active', 'patient_record', U&'["\75C5\5386","\60A3\8005\6863\6848"]'::jsonb),
    ('tpl_object_visit_record', 'tenant_jonex_demo', 'tpl_domain_medical', 'tpl_scenario_medical_record', U&'\5C31\8BCA\8BB0\5F55', U&'\60A3\8005\5355\6B21\5C31\8BCA\8BB0\5F55', 'active', 'visit_record', U&'["\5C31\8BCA","\95E8\8BCA\8BB0\5F55"]'::jsonb),
    ('tpl_object_diagnosis_result', 'tenant_jonex_demo', 'tpl_domain_medical', 'tpl_scenario_medical_record', U&'\8BCA\65AD\7ED3\679C', U&'\533B\751F\7ED9\51FA\7684\8BCA\65AD\7ED3\8BBA', 'active', 'diagnosis_result', U&'["\8BCA\65AD","\8BCA\65AD\7ED3\8BBA"]'::jsonb)
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_domain.template_attributes
    (id, tenant_id, template_object_id, attr_name, description, attr_type, is_primary_key, constraints_json, sort_order, ontology_code, is_required)
VALUES

    ('tpl_attr_record_no', 'tenant_jonex_demo', 'tpl_object_patient_record', U&'\75C5\5386\53F7', U&'\75C5\5386\552F\4E00\7F16\53F7', U&'\5B57\7B26\4E32', 1, '{}'::jsonb, 1, 'record_no', 1),
    ('tpl_attr_patient_name', 'tenant_jonex_demo', 'tpl_object_patient_record', U&'\60A3\8005\59D3\540D', U&'\60A3\8005\59D3\540D', U&'\5B57\7B26\4E32', 0, '{}'::jsonb, 2, 'patient_name', 1),
    ('tpl_attr_patient_gender', 'tenant_jonex_demo', 'tpl_object_patient_record', U&'\6027\522B', U&'\60A3\8005\6027\522B', U&'\679A\4E3E', 0, '{}'::jsonb, 3, 'gender', 1),
    ('tpl_attr_patient_age', 'tenant_jonex_demo', 'tpl_object_patient_record', U&'\5E74\9F84', U&'\60A3\8005\5E74\9F84', U&'\6570\503C', 0, '{}'::jsonb, 4, 'age', 0),
    ('tpl_attr_diagnosis_text', 'tenant_jonex_demo', 'tpl_object_patient_record', U&'\8BCA\65AD\7ED3\679C', U&'\533B\751F\7ED9\51FA\7684\8BCA\65AD\7ED3\8BBA', U&'\6587\672C', 0, '{}'::jsonb, 5, 'diagnosis_text', 0),
    ('tpl_attr_visit_date', 'tenant_jonex_demo', 'tpl_object_patient_record', U&'\5C31\8BCA\65E5\671F', U&'\672C\6B21\5C31\8BCA\65E5\671F', U&'\65E5\671F', 0, '{}'::jsonb, 6, 'visit_date', 0),

    ('tpl_attr_visit_no', 'tenant_jonex_demo', 'tpl_object_visit_record', U&'\5C31\8BCA\7F16\53F7', U&'\5355\6B21\5C31\8BCA\552F\4E00\7F16\53F7', U&'\5B57\7B26\4E32', 1, '{}'::jsonb, 1, 'visit_no', 1),
    ('tpl_attr_visit_dept', 'tenant_jonex_demo', 'tpl_object_visit_record', U&'\5C31\8BCA\79D1\5BA4', U&'\5C31\8BCA\79D1\5BA4\540D\79F0', U&'\5B57\7B26\4E32', 0, '{}'::jsonb, 2, 'department', 0),
    ('tpl_attr_visit_symptom', 'tenant_jonex_demo', 'tpl_object_visit_record', U&'\4E3B\8BC9\75C7\72B6', U&'\60A3\8005\4E3B\8BC9\75C7\72B6\63CF\8FF0', U&'\6587\672C', 0, '{}'::jsonb, 3, 'symptoms', 0),

    ('tpl_attr_diag_code', 'tenant_jonex_demo', 'tpl_object_diagnosis_result', U&'\8BCA\65AD\7F16\7801', U&'ICD \75BE\75C5\7F16\7801', U&'\5B57\7B26\4E32', 1, '{}'::jsonb, 1, 'diagnosis_code', 1),
    ('tpl_attr_diag_name', 'tenant_jonex_demo', 'tpl_object_diagnosis_result', U&'\8BCA\65AD\540D\79F0', U&'\75BE\75C5\8BCA\65AD\540D\79F0', U&'\5B57\7B26\4E32', 0, '{}'::jsonb, 2, 'diagnosis_name', 1),
    ('tpl_attr_diag_conclusion', 'tenant_jonex_demo', 'tpl_object_diagnosis_result', U&'\8BCA\65AD\7ED3\8BBA', U&'\533B\751F\6700\7EC8\8BCA\65AD\610F\89C1\548C\5EFA\8BAE', U&'\6587\672C', 0, '{}'::jsonb, 3, 'diagnosis_conclusion', 0)
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_domain.template_relations
    (id, tenant_id, domain_id, scenario_id, name, description, source_object_id, target_object_id, relation_type, status, ontology_code, aliases)
VALUES
    ('tpl_relation_record_visit', 'tenant_jonex_demo', 'tpl_domain_medical', 'tpl_scenario_medical_record', U&'\5C31\8BCA', U&'\60A3\8005\75C5\5386\4E0E\5C31\8BCA\8BB0\5F55\7684\5173\7CFB', 'tpl_object_patient_record', 'tpl_object_visit_record', U&'\4E00\5BF9\591A', 'active', 'has_visit_record', U&'["\5C31\8BCA","\5C31\533B"]'::jsonb),
    ('tpl_relation_visit_diagnosis', 'tenant_jonex_demo', 'tpl_domain_medical', 'tpl_scenario_medical_record', U&'\8BCA\65AD', U&'\5C31\8BCA\8BB0\5F55\4E0E\8BCA\65AD\7ED3\679C\7684\5173\8054', 'tpl_object_visit_record', 'tpl_object_diagnosis_result', U&'\4E00\5BF9\4E00', 'active', 'resulted_in_diagnosis', U&'["\8BCA\65AD","\5F97\51FA\8BCA\65AD"]'::jsonb)
ON CONFLICT (id) DO NOTHING;






INSERT INTO business_domain.template_domains (id, tenant_id, name, description, status, version, published_at, structure_hash)
VALUES ('tpl_domain_manufacturing', 'tenant_jonex_demo', U&'\5236\9020\4E1A', U&'\751F\4EA7\5236\9020、\8D28\68C0\4E0E\8BBE\5907\8FD0\7EF4\6A21\677F\9886\57DF', 'active', 1,
        '2026-06-01T00:00:00+00'::timestamptz,
        'cb568b75836751b97660df5f6ff1f07c50ea57dcc428f12ef438ffcba8e02456')
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_domain.template_scenarios (id, tenant_id, domain_id, name, description, config_json, version, published_at, structure_hash)
VALUES ('tpl_scenario_quality_inspection', 'tenant_jonex_demo', 'tpl_domain_manufacturing', U&'\751F\4EA7\8D28\68C0\5206\6790', U&'\751F\4EA7\73AF\8282\8D28\91CF\68C0\6D4B\6570\636E\5206\6790\573A\666F', '{}'::jsonb, 1,
        '2026-06-01T00:00:00+00'::timestamptz,
        'cb568b75836751b97660df5f6ff1f07c50ea57dcc428f12ef438ffcba8e02456')
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_domain.template_objects (id, tenant_id, domain_id, scenario_id, name, description, status, ontology_code, aliases)
VALUES
    ('tpl_obj_mfg_product', 'tenant_jonex_demo', 'tpl_domain_manufacturing', 'tpl_scenario_quality_inspection', U&'\4EA7\54C1', U&'\751F\4EA7\5236\9020\7684\4EA7\54C1/\96F6\90E8\4EF6', 'active', 'ManufacturedProduct', U&'["\4EA7\54C1","\96F6\90E8\4EF6","\5236\6210\54C1"]'::jsonb),
    ('tpl_obj_mfg_line', 'tenant_jonex_demo', 'tpl_domain_manufacturing', 'tpl_scenario_quality_inspection', U&'\751F\4EA7\7EBF', U&'\4EA7\54C1\751F\4EA7\6D41\6C34\7EBF', 'active', 'ProductionLine', U&'["\751F\4EA7\7EBF","\6D41\6C34\7EBF","\4EA7\7EBF"]'::jsonb),
    ('tpl_obj_mfg_defect', 'tenant_jonex_demo', 'tpl_domain_manufacturing', 'tpl_scenario_quality_inspection', U&'\8D28\91CF\7F3A\9677', U&'\8D28\68C0\8FC7\7A0B\4E2D\53D1\73B0\7684\7F3A\9677\8BB0\5F55', 'active', 'QualityDefect', U&'["\7F3A\9677","\8D28\91CF\95EE\9898","\4E0D\5408\683C\9879"]'::jsonb),
    ('tpl_obj_mfg_inspection', 'tenant_jonex_demo', 'tpl_domain_manufacturing', 'tpl_scenario_quality_inspection', U&'\8D28\68C0\62A5\544A', U&'\4EA7\54C1\8D28\91CF\68C0\6D4B\62A5\544A', 'active', 'InspectionReport', U&'["\8D28\68C0\62A5\544A","\68C0\6D4B\62A5\544A","\68C0\9A8C\5355"]'::jsonb)
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_domain.template_attributes
    (id, tenant_id, template_object_id, attr_name, description, attr_type, is_primary_key, constraints_json, sort_order, ontology_code, is_required)
VALUES

    ('tpl_attr_mfg_prod_code', 'tenant_jonex_demo', 'tpl_obj_mfg_product', U&'\4EA7\54C1\7F16\7801', U&'\4EA7\54C1\552F\4E00\7F16\7801/SKU', U&'\5B57\7B26\4E32', 1, '{}'::jsonb, 1, 'product_code', 1),
    ('tpl_attr_mfg_prod_name', 'tenant_jonex_demo', 'tpl_obj_mfg_product', U&'\4EA7\54C1\540D\79F0', U&'\4EA7\54C1\540D\79F0/\578B\53F7', U&'\5B57\7B26\4E32', 0, '{}'::jsonb, 2, 'product_name', 1),
    ('tpl_attr_mfg_prod_category', 'tenant_jonex_demo', 'tpl_obj_mfg_product', U&'\4EA7\54C1\7C7B\522B', U&'\4EA7\54C1\5206\7C7B', U&'\679A\4E3E', 0, '{}'::jsonb, 3, 'product_category', 0),
    ('tpl_attr_mfg_prod_spec', 'tenant_jonex_demo', 'tpl_obj_mfg_product', U&'\89C4\683C\578B\53F7', U&'\4EA7\54C1\89C4\683C\548C\6280\672F\53C2\6570', U&'\6587\672C', 0, '{}'::jsonb, 4, 'specification', 0),

    ('tpl_attr_mfg_line_code', 'tenant_jonex_demo', 'tpl_obj_mfg_line', U&'\4EA7\7EBF\7F16\7801', U&'\751F\4EA7\7EBF\552F\4E00\7F16\53F7', U&'\5B57\7B26\4E32', 1, '{}'::jsonb, 1, 'line_code', 1),
    ('tpl_attr_mfg_line_name', 'tenant_jonex_demo', 'tpl_obj_mfg_line', U&'\4EA7\7EBF\540D\79F0', U&'\751F\4EA7\7EBF\540D\79F0', U&'\5B57\7B26\4E32', 0, '{}'::jsonb, 2, 'line_name', 1),
    ('tpl_attr_mfg_line_status', 'tenant_jonex_demo', 'tpl_obj_mfg_line', U&'\8FD0\884C\72B6\6001', U&'\4EA7\7EBF\5F53\524D\8FD0\884C\72B6\6001', U&'\679A\4E3E', 0, '{}'::jsonb, 3, 'line_status', 0),

    ('tpl_attr_mfg_defect_code', 'tenant_jonex_demo', 'tpl_obj_mfg_defect', U&'\7F3A\9677\7F16\53F7', U&'\7F3A\9677\8BB0\5F55\552F\4E00\7F16\53F7', U&'\5B57\7B26\4E32', 1, '{}'::jsonb, 1, 'defect_code', 1),
    ('tpl_attr_mfg_defect_type', 'tenant_jonex_demo', 'tpl_obj_mfg_defect', U&'\7F3A\9677\7C7B\578B', U&'\7F3A\9677\5206\7C7B', U&'\679A\4E3E', 0, '{}'::jsonb, 2, 'defect_type', 0),
    ('tpl_attr_mfg_defect_severity', 'tenant_jonex_demo', 'tpl_obj_mfg_defect', U&'\4E25\91CD\7B49\7EA7', U&'\7F3A\9677\4E25\91CD\7A0B\5EA6', U&'\679A\4E3E', 0, '{}'::jsonb, 3, 'severity_level', 0),
    ('tpl_attr_mfg_defect_desc', 'tenant_jonex_demo', 'tpl_obj_mfg_defect', U&'\7F3A\9677\63CF\8FF0', U&'\7F3A\9677\73B0\8C61\548C\539F\56E0\63CF\8FF0', U&'\6587\672C', 0, '{}'::jsonb, 4, 'defect_description', 0),

    ('tpl_attr_mfg_insp_no', 'tenant_jonex_demo', 'tpl_obj_mfg_inspection', U&'\62A5\544A\7F16\53F7', U&'\8D28\68C0\62A5\544A\552F\4E00\7F16\53F7', U&'\5B57\7B26\4E32', 1, '{}'::jsonb, 1, 'report_no', 1),
    ('tpl_attr_mfg_insp_date', 'tenant_jonex_demo', 'tpl_obj_mfg_inspection', U&'\68C0\9A8C\65E5\671F', U&'\8D28\91CF\68C0\6D4B\65E5\671F', U&'\65E5\671F', 0, '{}'::jsonb, 2, 'inspection_date', 0),
    ('tpl_attr_mfg_insp_result', 'tenant_jonex_demo', 'tpl_obj_mfg_inspection', U&'\68C0\9A8C\7ED3\679C', U&'\5408\683C/\4E0D\5408\683C/\8BA9\6B65\63A5\6536', U&'\679A\4E3E', 0, '{}'::jsonb, 3, 'inspection_result', 0),
    ('tpl_attr_mfg_insp_conclusion', 'tenant_jonex_demo', 'tpl_obj_mfg_inspection', U&'\68C0\9A8C\7ED3\8BBA', U&'\8D28\68C0\7EFC\5408\7ED3\8BBA\548C\5EFA\8BAE', U&'\6587\672C', 0, '{}'::jsonb, 4, 'inspection_conclusion', 0)
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_domain.template_relations
    (id, tenant_id, domain_id, scenario_id, name, description, source_object_id, target_object_id, relation_type, status, ontology_code, aliases)
VALUES
    ('tpl_rel_mfg_prod_line', 'tenant_jonex_demo', 'tpl_domain_manufacturing', 'tpl_scenario_quality_inspection', U&'\751F\4EA7\4E8E', U&'\4EA7\54C1\5728\67D0\751F\4EA7\7EBF\751F\4EA7', 'tpl_obj_mfg_product', 'tpl_obj_mfg_line', U&'\591A\5BF9\4E00', 'active', 'PRODUCED_ON', U&'["\751F\4EA7\4E8E","\4EA7\81EA"]'::jsonb),
    ('tpl_rel_mfg_prod_defect', 'tenant_jonex_demo', 'tpl_domain_manufacturing', 'tpl_scenario_quality_inspection', U&'\5B58\5728\7F3A\9677', U&'\4EA7\54C1\5B58\5728\7684\8D28\91CF\7F3A\9677', 'tpl_obj_mfg_product', 'tpl_obj_mfg_defect', U&'\4E00\5BF9\591A', 'active', 'HAS_DEFECT', U&'["\5B58\5728\7F3A\9677","\53D1\73B0"]'::jsonb),
    ('tpl_rel_mfg_insp_prod', 'tenant_jonex_demo', 'tpl_domain_manufacturing', 'tpl_scenario_quality_inspection', U&'\68C0\6D4B', U&'\8D28\68C0\62A5\544A\5BF9\4EA7\54C1\7684\68C0\6D4B', 'tpl_obj_mfg_inspection', 'tpl_obj_mfg_product', U&'\591A\5BF9\4E00', 'active', 'INSPECTS', U&'["\68C0\6D4B","\68C0\9A8C"]'::jsonb),
    ('tpl_rel_mfg_insp_defect', 'tenant_jonex_demo', 'tpl_domain_manufacturing', 'tpl_scenario_quality_inspection', U&'\8BB0\5F55\7F3A\9677', U&'\8D28\68C0\62A5\544A\4E2D\8BB0\5F55\7684\7F3A\9677', 'tpl_obj_mfg_inspection', 'tpl_obj_mfg_defect', U&'\4E00\5BF9\591A', 'active', 'RECORDS_DEFECT', U&'["\8BB0\5F55\7F3A\9677","\53D1\73B0"]'::jsonb)
ON CONFLICT (id) DO NOTHING;




INSERT INTO knowledge_base.spaces (id, tenant_id, name, description, status, knowledge_base_count, service_count) VALUES
    ('space_demo_test', 'tenant_jonex_demo', U&'\6D4B\8BD5\7A7A\95F4', U&'\6D4B\8BD5\7A7A\95F4', 'active', 0, 0)
ON CONFLICT (id) DO NOTHING;




INSERT INTO knowledge_base.knowledge_info (id, tenant_id, space_id, name, description, data_source_types, document_count, status, owner_id) VALUES
    ('kb_demo_internet', 'tenant_jonex_demo', 'space_demo_test', U&'\4E92\8054\7F51\77E5\8BC6\5E93', U&'\4E92\8054\7F51\672C\4F53\62BD\53D6\6F14\793A\77E5\8BC6\5E93', '["file"]'::jsonb, 0, 'synced', '1'),
    ('kb_demo_credit_risk', 'tenant_jonex_demo', 'space_demo_test', U&'\4FE1\8D37\98CE\63A7\77E5\8BC6\5E93', U&'\91D1\878D\884C\4E1A\4FE1\8D37\98CE\63A7\672C\4F53\62BD\53D6\6F14\793A', '["file"]'::jsonb, 0, 'synced', '1'),
    ('kb_demo_medical', 'tenant_jonex_demo', 'space_demo_test', U&'\533B\7597\77E5\8BC6\5E93', U&'\533B\7597\75C5\5386\667A\80FD\89E3\6790\672C\4F53\62BD\53D6\6F14\793A', '["file"]'::jsonb, 0, 'synced', '1')
ON CONFLICT (id) DO NOTHING;



INSERT INTO knowledge_base.knowledge_data_sources
    (id, tenant_id, knowledge_base_id, access_method_id,access_type, name, config_json, sync_mode, status)
VALUES
    ('ds_demo_internet_file', 'tenant_jonex_demo', 'kb_demo_internet', 'dam_demo_file', 'file', U&'\6587\4EF6\4E0A\4F20', '{}'::jsonb, 'manual', 'active'),
    ('ds_demo_credit_file', 'tenant_jonex_demo', 'kb_demo_credit_risk', 'dam_demo_file', 'file', U&'\6587\4EF6\4E0A\4F20', '{}'::jsonb, 'manual', 'active'),
    ('ds_demo_medical_file', 'tenant_jonex_demo', 'kb_demo_medical', 'dam_demo_file', 'file', U&'\6587\4EF6\4E0A\4F20', '{}'::jsonb, 'manual', 'active')
ON CONFLICT (id) DO NOTHING;





INSERT INTO knowledge_base.services (id, tenant_id, space_id, name, description, domain_type, status, api_key_encrypted)
VALUES
    ('svc_demo_internet', 'tenant_jonex_demo', 'space_demo_test', U&'\4E92\8054\7F51\6D4B\8BD5\9886\57DF\670D\52A1', U&'\4E92\8054\7F51\6D4B\8BD5\9886\57DF\670D\52A1', U&'\6D4B\8BD5', 'active', 'demo-baseline-0123456789abcdef0123456789abcdef'),
    ('svc_demo_credit', 'tenant_jonex_demo', 'space_demo_test', U&'\4FE1\8D37\98CE\63A7\9886\57DF\670D\52A1', U&'\4FE1\8D37\98CE\63A7\6D4B\8BD5\9886\57DF\670D\52A1', U&'\91D1\878D', 'active', 'demo-credit-0123456789abcdef0123456789abcdef'),
    ('svc_demo_medical', 'tenant_jonex_demo', 'space_demo_test', U&'\533B\7597\9886\57DF\670D\52A1', U&'\533B\7597\75C5\5386\89E3\6790\6D4B\8BD5\9886\57DF\670D\52A1', U&'\533B\7597', 'active', 'demo-medical-0123456789abcdef0123456789abcdef')
ON CONFLICT (id) DO NOTHING;


INSERT INTO knowledge_base.service_knowledge_bases (id, tenant_id, service_id, kb_id)
VALUES
    ('skb_demo_internet', 'tenant_jonex_demo', 'svc_demo_internet', 'kb_demo_internet'),
    ('skb_demo_credit', 'tenant_jonex_demo', 'svc_demo_credit', 'kb_demo_credit_risk'),
    ('skb_demo_medical', 'tenant_jonex_demo', 'svc_demo_medical', 'kb_demo_medical')
ON CONFLICT (id) DO NOTHING;


INSERT INTO knowledge_base.service_api_keys (id, tenant_id, service_id, key_prefix, key_encrypted, expires_at, is_active)
VALUES

    ('sak_internet_main', 'tenant_jonex_demo', 'svc_demo_internet', 'demo', 'demo-baseline-0123456789abcdef0123456789abcdef', '2027-12-31'::timestamp, 1),
    ('sak_internet_readonly', 'tenant_jonex_demo', 'svc_demo_internet', 'demo', 'demo-ro-a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6', '2026-12-31'::timestamp, 1),
    ('sak_internet_expired', 'tenant_jonex_demo', 'svc_demo_internet', 'demo', 'demo-expired-00000000000000000000000000000000', '2026-01-01'::timestamp, 0),

    ('sak_credit_main', 'tenant_jonex_demo', 'svc_demo_credit', 'demo', 'demo-credit-0123456789abcdef0123456789abcdef', '2027-12-31'::timestamp, 1),
    ('sak_credit_readonly', 'tenant_jonex_demo', 'svc_demo_credit', 'demo', 'demo-ro-credit-a1b2c3d4e5f6a7b8c9d0e1f2a3b4', '2026-12-31'::timestamp, 1),
    ('sak_credit_expired', 'tenant_jonex_demo', 'svc_demo_credit', 'demo', 'demo-expired-credit-0000000000000000000000', '2026-01-01'::timestamp, 0),

    ('sak_medical_main', 'tenant_jonex_demo', 'svc_demo_medical', 'demo', 'demo-medical-0123456789abcdef0123456789abcdef', '2027-12-31'::timestamp, 1),
    ('sak_medical_readonly', 'tenant_jonex_demo', 'svc_demo_medical', 'demo', 'demo-ro-medical-a1b2c3d4e5f6a7b8c9d0e1f2a', '2026-12-31'::timestamp, 1),
    ('sak_medical_expired', 'tenant_jonex_demo', 'svc_demo_medical', 'demo', 'demo-expired-medical-000000000000000000000', '2026-01-01'::timestamp, 0)
ON CONFLICT (id) DO NOTHING;







INSERT INTO knowledge_base.ontology_template_bindings
    (tenant_id, knowledge_base_id, template_domain_id, template_scenario_id, source_type, status)
VALUES
    ('tenant_jonex_demo','kb_demo_internet','tpl_domain_internet','tpl_scenario_internet_general','business_template','active'),
    ('tenant_jonex_demo','kb_demo_credit_risk','tpl_domain_finance','tpl_scenario_credit_risk','business_template','active'),
    ('tenant_jonex_demo','kb_demo_medical','tpl_domain_medical','tpl_scenario_medical_record','business_template','active')
ON CONFLICT (tenant_id, knowledge_base_id) DO NOTHING;


INSERT INTO knowledge_base.ontology_compiled_schemas
    (tenant_id, knowledge_base_id, template_domain_id, template_scenario_id,
     source_type, source_version, source_hash, schema_version,
     entity_types, relation_types, constraints, disambiguation, prompt_schema,
     status, compiled_at)
VALUES (
    'tenant_jonex_demo', 'kb_demo_internet',
    'tpl_domain_internet', 'tpl_scenario_internet_general',
    'business_template', 1, 'b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0abc1de', 1,
    U&'[
        {"name":"Company","display_name":"\516C\53F8","aliases":["\4F01\4E1A","\5382\5546","\5E73\53F0\65B9","\673A\6784","Organization"],"source_object_id":"tpl_obj_inet_company","attributes":[
            {"name":"unified_social_credit_code","display_name":"\7EDF\4E00\793E\4F1A\4FE1\7528\4EE3\7801","type":"string","required":true,"source_attribute_id":"tpl_attr_inet_co_code"},
            {"name":"company_name","display_name":"\516C\53F8\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_inet_co_name"},
            {"name":"industry","display_name":"\6240\5C5E\884C\4E1A","type":"enum","required":false,"source_attribute_id":"tpl_attr_inet_co_industry"},
            {"name":"founded","display_name":"\6210\7ACB\65F6\95F4","type":"date","required":false,"source_attribute_id":"tpl_attr_inet_co_founded"},
            {"name":"registered_capital","display_name":"\6CE8\518C\8D44\672C","type":"number","required":false,"source_attribute_id":"tpl_attr_inet_co_capital"},
            {"name":"company_summary","display_name":"\516C\53F8\7B80\4ECB","type":"text","required":false,"source_attribute_id":"tpl_attr_inet_co_summary"}
        ]},
        {"name":"Product","display_name":"\4EA7\54C1","aliases":["App","\5E94\7528","\5E73\53F0","Product"],"source_object_id":"tpl_obj_inet_product","attributes":[
            {"name":"product_name","display_name":"\4EA7\54C1\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_inet_pd_name"},
            {"name":"category","display_name":"\7C7B\522B","type":"enum","required":false,"source_attribute_id":"tpl_attr_inet_pd_category"},
            {"name":"platform","display_name":"\5E73\53F0","type":"enum","required":false,"source_attribute_id":"tpl_attr_inet_pd_platform"},
            {"name":"user_scale","display_name":"\7528\6237\89C4\6A21","type":"number","required":false,"source_attribute_id":"tpl_attr_inet_pd_users"},
            {"name":"product_description","display_name":"\4EA7\54C1\63CF\8FF0","type":"text","required":false,"source_attribute_id":"tpl_attr_inet_pd_desc"}
        ]},
        {"name":"Technology","display_name":"\6280\672F","aliases":["\6846\67B6","\534F\8BAE","\7B97\6CD5","\65B9\6CD5","Method"],"source_object_id":"tpl_obj_inet_tech","attributes":[
            {"name":"tech_name","display_name":"\6280\672F\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_inet_tech_name"},
            {"name":"tech_category","display_name":"\6280\672F\5206\7C7B","type":"enum","required":false,"source_attribute_id":"tpl_attr_inet_tech_category"},
            {"name":"tech_description","display_name":"\6280\672F\63CF\8FF0","type":"text","required":false,"source_attribute_id":"tpl_attr_inet_tech_desc"}
        ]},
        {"name":"Feature","display_name":"\529F\80FD\7279\6027","aliases":["\529F\80FD","\7279\6027","\6A21\5757","\6982\5FF5","Concept"],"source_object_id":"tpl_obj_inet_feature","attributes":[
            {"name":"feature_name","display_name":"\7279\6027\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_inet_feat_name"},
            {"name":"feature_description","display_name":"\7279\6027\63CF\8FF0","type":"text","required":false,"source_attribute_id":"tpl_attr_inet_feat_desc"}
        ]},
        {"name":"Person","display_name":"\4EBA\5458","aliases":["\521B\59CB\4EBA","\9AD8\7BA1","\5DE5\7A0B\5E08","\4EBA","Person"],"source_object_id":"tpl_obj_inet_person","attributes":[
            {"name":"person_name","display_name":"\59D3\540D","type":"string","required":true,"source_attribute_id":"tpl_attr_inet_per_name"},
            {"name":"title","display_name":"\804C\4F4D","type":"string","required":false,"source_attribute_id":"tpl_attr_inet_per_title"},
            {"name":"affiliated_company","display_name":"\6240\5C5E\516C\53F8","type":"string","required":false,"source_attribute_id":"tpl_attr_inet_per_company"},
            {"name":"biography","display_name":"\7B80\4ECB","type":"text","required":false,"source_attribute_id":"tpl_attr_inet_per_bio"}
        ]},
        {"name":"Event","display_name":"\4E8B\4EF6","aliases":["\53D1\5E03\4F1A","\878D\8D44","\6D3B\52A8","Event"],"source_object_id":"tpl_obj_inet_event","attributes":[
            {"name":"event_name","display_name":"\4E8B\4EF6\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_inet_ev_name"},
            {"name":"event_type","display_name":"\4E8B\4EF6\7C7B\578B","type":"enum","required":false,"source_attribute_id":"tpl_attr_inet_ev_type"},
            {"name":"event_date","display_name":"\65E5\671F","type":"date","required":false,"source_attribute_id":"tpl_attr_inet_ev_date"},
            {"name":"event_description","display_name":"\4E8B\4EF6\63CF\8FF0","type":"text","required":false,"source_attribute_id":"tpl_attr_inet_ev_desc"}
        ]},
        {"name":"Market","display_name":"\5E02\573A","aliases":["\7528\6237\7FA4\4F53","\8D5B\9053","\9886\57DF"],"source_object_id":"tpl_obj_inet_market","attributes":[
            {"name":"market_name","display_name":"\5E02\573A\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_inet_mkt_name"},
            {"name":"market_size","display_name":"\5E02\573A\89C4\6A21","type":"number","required":false,"source_attribute_id":"tpl_attr_inet_mkt_size"},
            {"name":"market_description","display_name":"\5E02\573A\63CF\8FF0","type":"text","required":false,"source_attribute_id":"tpl_attr_inet_mkt_desc"}
        ]},
        {"name":"Investor","display_name":"\6295\8D44\673A\6784","aliases":["\8D44\672C","VC","\6295\8D44\65B9"],"source_object_id":"tpl_obj_inet_investor","attributes":[
            {"name":"investor_name","display_name":"\673A\6784\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_inet_inv_name"},
            {"name":"investor_type","display_name":"\673A\6784\7C7B\578B","type":"enum","required":false,"source_attribute_id":"tpl_attr_inet_inv_type"},
            {"name":"aum","display_name":"\7BA1\7406\89C4\6A21","type":"number","required":false,"source_attribute_id":"tpl_attr_inet_inv_aum"},
            {"name":"investor_description","display_name":"\673A\6784\7B80\4ECB","type":"text","required":false,"source_attribute_id":"tpl_attr_inet_inv_desc"}
        ]}
    ]'::jsonb,
    U&'[
        {"name":"DEVELOPS","display_name":"\5F00\53D1","aliases":["\5F00\53D1","\63A8\51FA"],"source":"Company","target":"Product","source_relation_id":"tpl_rel_inet_develops","cardinality":"one_to_many"},
        {"name":"USES_TECH","display_name":"\91C7\7528\6280\672F","aliases":["\91C7\7528","\4F7F\7528\6280\672F"],"source":"Product","target":"Technology","source_relation_id":"tpl_rel_inet_usestech","cardinality":"many_to_many"},
        {"name":"HAS_FEATURE","display_name":"\5177\5907\529F\80FD","aliases":["\5177\5907\529F\80FD","\5305\542B"],"source":"Product","target":"Feature","source_relation_id":"tpl_rel_inet_hasfeature","cardinality":"one_to_many"},
        {"name":"FOUNDED_BY","display_name":"\521B\7ACB","aliases":["\521B\7ACB","\521B\529E"],"source":"Company","target":"Person","source_relation_id":"tpl_rel_inet_foundedby","cardinality":"many_to_many"},
        {"name":"WORKS_AT","display_name":"\4EFB\804C","aliases":["\4EFB\804C","\5C31\804C"],"source":"Person","target":"Company","source_relation_id":"tpl_rel_inet_worksat","cardinality":"many_to_one"},
        {"name":"INVESTS_IN","display_name":"\6295\8D44","aliases":["\6295\8D44","\6CE8\8D44"],"source":"Investor","target":"Company","source_relation_id":"tpl_rel_inet_invests","cardinality":"many_to_many"},
        {"name":"COMPETES_WITH","display_name":"\7ADE\4E89","aliases":["\7ADE\4E89","\5BF9\6807"],"source":"Product","target":"Product","source_relation_id":"tpl_rel_inet_competes","cardinality":"many_to_many"},
        {"name":"TARGETS","display_name":"\9762\5411","aliases":["\9762\5411","\5B9A\4F4D"],"source":"Product","target":"Market","source_relation_id":"tpl_rel_inet_targets","cardinality":"many_to_one"},
        {"name":"PARTICIPATES","display_name":"\53C2\4E0E","aliases":["\53C2\4E0E","\51FA\5E2D"],"source":"Company","target":"Event","source_relation_id":"tpl_rel_inet_participates","cardinality":"many_to_many"}
    ]'::jsonb,
    '[{"type":"entity","severity":"warning"}]'::jsonb,
    '{"case_insensitive":true,"alias_merge":true}'::jsonb,
    U&'{
        "entity_types":[
            {"name":"Company","aliases":["\4F01\4E1A","\5382\5546","\5E73\53F0\65B9","\673A\6784"],"attributes":[
                {"name":"unified_social_credit_code","type":"string","required":true},
                {"name":"company_name","type":"string","required":true},
                {"name":"industry","type":"enum","required":false},
                {"name":"founded","type":"date","required":false},
                {"name":"registered_capital","type":"number","required":false},
                {"name":"company_summary","type":"text","required":false}
            ]},
            {"name":"Product","aliases":["App","\5E94\7528","\5E73\53F0"],"attributes":[
                {"name":"product_name","type":"string","required":true},
                {"name":"category","type":"enum","required":false},
                {"name":"platform","type":"enum","required":false},
                {"name":"user_scale","type":"number","required":false},
                {"name":"product_description","type":"text","required":false}
            ]},
            {"name":"Technology","aliases":["\6846\67B6","\534F\8BAE","\7B97\6CD5","\65B9\6CD5"],"attributes":[
                {"name":"tech_name","type":"string","required":true},
                {"name":"tech_category","type":"enum","required":false},
                {"name":"tech_description","type":"text","required":false}
            ]},
            {"name":"Feature","aliases":["\529F\80FD","\7279\6027","\6A21\5757","\6982\5FF5"],"attributes":[
                {"name":"feature_name","type":"string","required":true},
                {"name":"feature_description","type":"text","required":false}
            ]},
            {"name":"Person","aliases":["\521B\59CB\4EBA","\9AD8\7BA1","\5DE5\7A0B\5E08","\4EBA"],"attributes":[
                {"name":"person_name","type":"string","required":true},
                {"name":"title","type":"string","required":false},
                {"name":"affiliated_company","type":"string","required":false},
                {"name":"biography","type":"text","required":false}
            ]},
            {"name":"Event","aliases":["\53D1\5E03\4F1A","\878D\8D44","\6D3B\52A8"],"attributes":[
                {"name":"event_name","type":"string","required":true},
                {"name":"event_type","type":"enum","required":false},
                {"name":"event_date","type":"date","required":false},
                {"name":"event_description","type":"text","required":false}
            ]},
            {"name":"Market","aliases":["\7528\6237\7FA4\4F53","\8D5B\9053","\9886\57DF"],"attributes":[
                {"name":"market_name","type":"string","required":true},
                {"name":"market_size","type":"number","required":false},
                {"name":"market_description","type":"text","required":false}
            ]},
            {"name":"Investor","aliases":["\8D44\672C","VC","\6295\8D44\65B9"],"attributes":[
                {"name":"investor_name","type":"string","required":true},
                {"name":"investor_type","type":"enum","required":false},
                {"name":"aum","type":"number","required":false},
                {"name":"investor_description","type":"text","required":false}
            ]}
        ],
        "relation_types":[
            {"name":"DEVELOPS","source":"Company","target":"Product"},
            {"name":"USES_TECH","source":"Product","target":"Technology"},
            {"name":"HAS_FEATURE","source":"Product","target":"Feature"},
            {"name":"FOUNDED_BY","source":"Company","target":"Person"},
            {"name":"WORKS_AT","source":"Person","target":"Company"},
            {"name":"INVESTS_IN","source":"Investor","target":"Company"},
            {"name":"COMPETES_WITH","source":"Product","target":"Product"},
            {"name":"TARGETS","source":"Product","target":"Market"},
            {"name":"PARTICIPATES","source":"Company","target":"Event"}
        ]
    }'::jsonb,
    'active', '2026-06-09T00:00:00+00'::timestamptz
) ON CONFLICT (tenant_id, knowledge_base_id) DO NOTHING;


INSERT INTO knowledge_base.ontology_compiled_schemas
    (tenant_id, knowledge_base_id, template_domain_id, template_scenario_id,
     source_type, source_version, source_hash, schema_version,
     entity_types, relation_types, constraints, disambiguation, prompt_schema,
     status, compiled_at)
VALUES (
    'tenant_jonex_demo', 'kb_demo_credit_risk',
    'tpl_domain_finance', 'tpl_scenario_credit_risk',
    'business_template', 1, '0476f5786a7e292d7a2aaaed06a06b6787b96a746da8818e3869cf2cd71f9777', 1,
    U&'[
        {"name":"enterprise_customer","display_name":"\4F01\4E1A\5BA2\6237","aliases":["\8D37\6B3E\7533\8BF7\4F01\4E1A","\5BA2\6237\4E3B\4F53"],"source_object_id":"tpl_object_enterprise_customer","attributes":[
            {"name":"unified_social_credit_code","display_name":"\7EDF\4E00\793E\4F1A\4FE1\7528\4EE3\7801","type":"string","required":true,"source_attribute_id":"tpl_attr_enterprise_code"},
            {"name":"enterprise_name","display_name":"\4F01\4E1A\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_enterprise_name"},
            {"name":"registered_capital","display_name":"\6CE8\518C\8D44\672C","type":"number","required":false,"source_attribute_id":"tpl_attr_enterprise_capital"},
            {"name":"establishment_date","display_name":"\6210\7ACB\65E5\671F","type":"date","required":false,"source_attribute_id":"tpl_attr_enterprise_date"}
        ]},
        {"name":"financial_statement","display_name":"\8D22\52A1\62A5\8868","aliases":["\8D22\62A5","\8D22\52A1\62A5\544A"],"source_object_id":"tpl_object_financial_statement","attributes":[
            {"name":"statement_id","display_name":"\62A5\8868ID","type":"string","required":true,"source_attribute_id":"tpl_attr_statement_id"},
            {"name":"statement_type","display_name":"\62A5\8868\7C7B\578B","type":"enum","required":false,"source_attribute_id":"tpl_attr_statement_type"},
            {"name":"reporting_period","display_name":"\62A5\544A\671F","type":"date","required":false,"source_attribute_id":"tpl_attr_statement_period"},
            {"name":"operating_revenue","display_name":"\8425\4E1A\6536\5165","type":"number","required":false,"source_attribute_id":"tpl_attr_statement_revenue"},
            {"name":"net_profit","display_name":"\51C0\5229\6DA6","type":"number","required":false,"source_attribute_id":"tpl_attr_statement_profit"}
        ]},
        {"name":"guarantee_company","display_name":"\62C5\4FDD\4F01\4E1A","aliases":["\62C5\4FDD\65B9","\4FDD\8BC1\4F01\4E1A"],"source_object_id":"tpl_object_guarantee_company","attributes":[
            {"name":"guarantee_credit_code","display_name":"\7EDF\4E00\793E\4F1A\4FE1\7528\4EE3\7801","type":"string","required":true,"source_attribute_id":"tpl_attr_guarantee_code"},
            {"name":"guarantee_name","display_name":"\4F01\4E1A\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_guarantee_name"},
            {"name":"guarantee_amount","display_name":"\62C5\4FDD\91D1\989D","type":"number","required":false,"source_attribute_id":"tpl_attr_guarantee_amount"}
        ]}
    ]'::jsonb,
    U&'[
        {"name":"owns_financial_statement","display_name":"\6301\6709","aliases":["\6301\6709","\62E5\6709"],"source":"enterprise_customer","target":"financial_statement","source_relation_id":"tpl_relation_customer_statement","cardinality":"one_to_many"},
        {"name":"guaranteed_by","display_name":"\62C5\4FDD","aliases":["\62C5\4FDD","\4FDD\8BC1"],"source":"enterprise_customer","target":"guarantee_company","source_relation_id":"tpl_relation_customer_guarantee","cardinality":"many_to_many"}
    ]'::jsonb,
    '[{"type":"entity","severity":"warning"}]'::jsonb,
    '{"case_insensitive":true,"alias_merge":true}'::jsonb,
    U&'{
        "entity_types":[
            {"name":"enterprise_customer","aliases":["\8D37\6B3E\7533\8BF7\4F01\4E1A","\5BA2\6237\4E3B\4F53"],"attributes":[
                {"name":"unified_social_credit_code","type":"string","required":true},
                {"name":"enterprise_name","type":"string","required":true},
                {"name":"registered_capital","type":"number","required":false},
                {"name":"establishment_date","type":"date","required":false}
            ]},
            {"name":"financial_statement","aliases":["\8D22\62A5","\8D22\52A1\62A5\544A"],"attributes":[
                {"name":"statement_id","type":"string","required":true},
                {"name":"statement_type","type":"enum","required":false},
                {"name":"reporting_period","type":"date","required":false},
                {"name":"operating_revenue","type":"number","required":false},
                {"name":"net_profit","type":"number","required":false}
            ]},
            {"name":"guarantee_company","aliases":["\62C5\4FDD\65B9","\4FDD\8BC1\4F01\4E1A"],"attributes":[
                {"name":"guarantee_credit_code","type":"string","required":true},
                {"name":"guarantee_name","type":"string","required":true},
                {"name":"guarantee_amount","type":"number","required":false}
            ]}
        ],
        "relation_types":[
            {"name":"owns_financial_statement","source":"enterprise_customer","target":"financial_statement"},
            {"name":"guaranteed_by","source":"enterprise_customer","target":"guarantee_company"}
        ]
    }'::jsonb,
    'active', '2026-06-09T00:00:00+00'::timestamptz
) ON CONFLICT (tenant_id, knowledge_base_id) DO NOTHING;


INSERT INTO knowledge_base.ontology_compiled_schemas
    (tenant_id, knowledge_base_id, template_domain_id, template_scenario_id,
     source_type, source_version, source_hash, schema_version,
     entity_types, relation_types, constraints, disambiguation, prompt_schema,
     status, compiled_at)
VALUES (
    'tenant_jonex_demo', 'kb_demo_medical',
    'tpl_domain_medical', 'tpl_scenario_medical_record',
    'business_template', 1, '6b518c74048be883c991406f509f03b1921f062a5ed0a7c1167e85e1886f38ba', 1,
    U&'[
        {"name":"patient_record","display_name":"\60A3\8005\75C5\5386","aliases":["\75C5\5386","\60A3\8005\6863\6848"],"source_object_id":"tpl_object_patient_record","attributes":[
            {"name":"record_no","display_name":"\75C5\5386\53F7","type":"string","required":true,"source_attribute_id":"tpl_attr_record_no"},
            {"name":"patient_name","display_name":"\60A3\8005\59D3\540D","type":"string","required":true,"source_attribute_id":"tpl_attr_patient_name"},
            {"name":"gender","display_name":"\6027\522B","type":"enum","required":true,"source_attribute_id":"tpl_attr_patient_gender"},
            {"name":"age","display_name":"\5E74\9F84","type":"number","required":false,"source_attribute_id":"tpl_attr_patient_age"},
            {"name":"diagnosis_text","display_name":"\8BCA\65AD\7ED3\679C","type":"text","required":false,"source_attribute_id":"tpl_attr_diagnosis_text"},
            {"name":"visit_date","display_name":"\5C31\8BCA\65E5\671F","type":"date","required":false,"source_attribute_id":"tpl_attr_visit_date"}
        ]},
        {"name":"visit_record","display_name":"\5C31\8BCA\8BB0\5F55","aliases":["\5C31\8BCA","\95E8\8BCA\8BB0\5F55"],"source_object_id":"tpl_object_visit_record","attributes":[
            {"name":"visit_no","display_name":"\5C31\8BCA\7F16\53F7","type":"string","required":true,"source_attribute_id":"tpl_attr_visit_no"},
            {"name":"department","display_name":"\5C31\8BCA\79D1\5BA4","type":"string","required":false,"source_attribute_id":"tpl_attr_visit_dept"},
            {"name":"symptoms","display_name":"\4E3B\8BC9\75C7\72B6","type":"text","required":false,"source_attribute_id":"tpl_attr_visit_symptom"}
        ]},
        {"name":"diagnosis_result","display_name":"\8BCA\65AD\7ED3\679C","aliases":["\8BCA\65AD","\8BCA\65AD\7ED3\8BBA"],"source_object_id":"tpl_object_diagnosis_result","attributes":[
            {"name":"diagnosis_code","display_name":"\8BCA\65AD\7F16\7801","type":"string","required":true,"source_attribute_id":"tpl_attr_diag_code"},
            {"name":"diagnosis_name","display_name":"\8BCA\65AD\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_diag_name"},
            {"name":"diagnosis_conclusion","display_name":"\8BCA\65AD\7ED3\8BBA","type":"text","required":false,"source_attribute_id":"tpl_attr_diag_conclusion"}
        ]}
    ]'::jsonb,
    U&'[
        {"name":"has_visit_record","display_name":"\5C31\8BCA","aliases":["\5C31\8BCA","\5C31\533B"],"source":"patient_record","target":"visit_record","source_relation_id":"tpl_relation_record_visit","cardinality":"one_to_many"},
        {"name":"resulted_in_diagnosis","display_name":"\8BCA\65AD","aliases":["\8BCA\65AD","\5F97\51FA\8BCA\65AD"],"source":"visit_record","target":"diagnosis_result","source_relation_id":"tpl_relation_visit_diagnosis","cardinality":"one_to_one"}
    ]'::jsonb,
    '[{"type":"entity","severity":"warning"}]'::jsonb,
    '{"case_insensitive":true,"alias_merge":true}'::jsonb,
    U&'{
        "entity_types":[
            {"name":"patient_record","aliases":["\75C5\5386","\60A3\8005\6863\6848"],"attributes":[
                {"name":"record_no","type":"string","required":true},
                {"name":"patient_name","type":"string","required":true},
                {"name":"gender","type":"enum","required":true},
                {"name":"age","type":"number","required":false},
                {"name":"diagnosis_text","type":"text","required":false},
                {"name":"visit_date","type":"date","required":false}
            ]},
            {"name":"visit_record","aliases":["\5C31\8BCA","\95E8\8BCA\8BB0\5F55"],"attributes":[
                {"name":"visit_no","type":"string","required":true},
                {"name":"department","type":"string","required":false},
                {"name":"symptoms","type":"text","required":false}
            ]},
            {"name":"diagnosis_result","aliases":["\8BCA\65AD","\8BCA\65AD\7ED3\8BBA"],"attributes":[
                {"name":"diagnosis_code","type":"string","required":true},
                {"name":"diagnosis_name","type":"string","required":true},
                {"name":"diagnosis_conclusion","type":"text","required":false}
            ]}
        ],
        "relation_types":[
            {"name":"has_visit_record","source":"patient_record","target":"visit_record"},
            {"name":"resulted_in_diagnosis","source":"visit_record","target":"diagnosis_result"}
        ]
    }'::jsonb,
    'active', '2026-06-09T00:00:00+00'::timestamptz
) ON CONFLICT (tenant_id, knowledge_base_id) DO NOTHING;









INSERT INTO business_domain.template_domains (id, tenant_id, name, description, status, version, published_at, structure_hash)
VALUES ('tpl_domain_hardware_internet', 'tenant_jonex_demo', U&'\786C\4EF6\4E92\8054\7F51', U&'\786C\4EF6\4E92\8054\7F51\4E0A\5E02\516C\53F8\8D22\62A5\5206\6790\4E0E\4E1A\52A1\60C5\62A5\6A21\677F\9886\57DF', 'active', 3,
        '2026-06-24T00:00:00+00'::timestamptz,
        'd5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6')
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_domain.template_scenarios (id, tenant_id, domain_id, name, description, config_json, version, published_at, structure_hash)
VALUES ('tpl_scenario_hw_inet_finance', 'tenant_jonex_demo', 'tpl_domain_hardware_internet', U&'\8D22\62A5\5206\6790', U&'\786C\4EF6\4E92\8054\7F51\4E0A\5E02\516C\53F8\5E74\5EA6/\5B63\5EA6\8D22\62A5\7ED3\6784\5316\62BD\53D6\573A\666F（\57FA\4E8E\5C0F\7C732025\5E74\62A5）', '{}'::jsonb, 3,
        '2026-06-24T00:00:00+00'::timestamptz,
        'd5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6')
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_domain.template_objects (id, tenant_id, domain_id, scenario_id, name, description, status, ontology_code, aliases)
VALUES
 ('tpl_obj_hwfin_company','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\4E0A\5E02\516C\53F8',U&'\8D22\62A5\62AB\9732\4E3B\4F53（\786C\4EF6\4E92\8054\7F51\4E0A\5E02\516C\53F8）','active','listed_company',U&'["\4E0A\5E02\516C\53F8","\516C\53F8","\96C6\56E2","\53D1\884C\4EBA","Issuer"]'::jsonb),
 ('tpl_obj_hwfin_report','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\8D22\52A1\62A5\544A',U&'\5E74\5EA6/\5B63\5EA6/\4E2D\671F\8D22\52A1\62A5\544A','active','financial_report',U&'["\8D22\52A1\62A5\544A","\8D22\62A5","\5E74\62A5","\5E74\5EA6\62A5\544A","\5B63\62A5","\4E2D\671F\62A5\544A","Annual Report"]'::jsonb),
 ('tpl_obj_hwfin_segment','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\4E1A\52A1\5206\90E8',U&'\516C\53F8\4E1A\52A1\5206\90E8（\5982\624B\673A×AIoT、\667A\80FD\7535\52A8\6C7D\8F66\53CAAI\7B49\521B\65B0\4E1A\52A1）','active','business_segment',U&'["\4E1A\52A1\5206\90E8","\5206\90E8","\677F\5757","\4E1A\52A1\7EBF","Segment"]'::jsonb),
 ('tpl_obj_hwfin_line','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\4EA7\54C1\7EBF',U&'\5206\90E8\4E0B\7684\4EA7\54C1\7EBF（\5982\667A\80FD\624B\673A、IoT\4E0E\751F\6D3B\6D88\8D39\4EA7\54C1、\4E92\8054\7F51\670D\52A1、\667A\80FD\7535\52A8\6C7D\8F66）','active','product_line',U&'["\4EA7\54C1\7EBF","\4E1A\52A1\7C7B\522B","Product Line"]'::jsonb),
 ('tpl_obj_hwfin_product','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\4EA7\54C1',U&'\5177\4F53\4EA7\54C1/\673A\578B/\5E94\7528/\670D\52A1/\8F66\578B','active','product',U&'["\4EA7\54C1","\673A\578B","\5E94\7528","\670D\52A1","\8F66\578B","Product"]'::jsonb),
 ('tpl_obj_hwfin_fin_metric','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\8D22\52A1\6307\6807',U&'\8425\6536/\5229\6DA6/\6BDB\5229\7B49\8D22\52A1\6307\6807','active','financial_metric',U&'["\8D22\52A1\6307\6807","\8D22\52A1\6570\636E","Financial Metric"]'::jsonb),
 ('tpl_obj_hwfin_op_metric','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\8FD0\8425\6307\6807',U&'\51FA\8D27\91CF/\6708\6D3B/\5E02\5360\7387/\8FDE\63A5\8BBE\5907\6570\7B49\8FD0\8425\6307\6807','active','operational_metric',U&'["\8FD0\8425\6307\6807","\7ECF\8425\6570\636E","Operational Metric"]'::jsonb),
 ('tpl_obj_hwfin_rnd_metric','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\7814\53D1\6307\6807',U&'\7814\53D1\6295\5165/\7814\53D1\4EBA\5458\7B49\7814\53D1\6307\6807','active','rnd_metric',U&'["\7814\53D1\6307\6807","\7814\53D1\6295\5165","RnD Metric"]'::jsonb),
 ('tpl_obj_hwfin_cost','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\6210\672C\8D39\7528',U&'\9500\552E\6210\672C/\9500\552E\63A8\5E7F/\884C\653F/\7814\53D1/\6240\5F97\7A0E\7B49\6210\672C\8D39\7528','active','cost_expense',U&'["\6210\672C\8D39\7528","\8D39\7528","\652F\51FA","Cost Expense"]'::jsonb),
 ('tpl_obj_hwfin_shareholder','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\80A1\4E1C\56DE\62A5',U&'\80A1\606F/\914D\552E/\56DE\8D2D\7B49\80A1\4E1C\56DE\62A5\4E8B\9879','active','shareholder_return',U&'["\80A1\4E1C\56DE\62A5","\80A1\606F","\5206\7EA2","\914D\552E","\56DE\8D2D","Shareholder Return"]'::jsonb),
 ('tpl_obj_hwfin_esg','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'ESG\6307\6807',U&'\73AF\5883/\793E\4F1A/\7BA1\6CBB\76F8\5173\6307\6807','active','esg_metric',U&'["ESG\6307\6807","ESG","\73AF\5883\793E\4F1A\7BA1\6CBB","ESG Metric"]'::jsonb),
 ('tpl_obj_hwfin_person','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\5173\952E\4EBA\5458',U&'\9AD8\7BA1/\521B\59CB\4EBA/\6838\5FC3\7BA1\7406\4EBA\5458/\8463\4E8B\4F1A\6210\5458','active','key_person',U&'["\5173\952E\4EBA\5458","\9AD8\7BA1","\7BA1\7406\5C42","\8463\4E8B","Key Person"]'::jsonb),
 ('tpl_obj_hwfin_event','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\4E1A\52A1\4E8B\4EF6',U&'\8D22\62A5\62AB\9732\7684\4E1A\52A1\4E8B\4EF6/\91CC\7A0B\7891','active','business_event',U&'["\4E1A\52A1\4E8B\4EF6","\4E8B\4EF6","\91CC\7A0B\7891","Business Event"]'::jsonb),
 ('tpl_obj_hwfin_market','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\5730\533A\5E02\573A',U&'\6536\5165/\95E8\5E97/\7528\6237\5206\5730\533A\62AB\9732\7684\5E02\573A（\5982\4E2D\56FD\5927\9646、\5883\5916、\6B27\6D32、\5370\5EA6）','active','geographic_market',U&'["\5730\533A\5E02\573A","\5E02\573A","\533A\57DF","\5730\533A","Region","Market"]'::jsonb),
 ('tpl_obj_hwfin_channel','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\9500\552E\6E20\9053',U&'\7EBF\4E0A/\7EBF\4E0B\9500\552E\4E0E\670D\52A1\6E20\9053（\5982\5C0F\7C73\4E4B\5BB6、\76F4\8425\5E97、\6388\6743\5E97、\7ECF\9500\5546、\5C0F\7C73\5546\57CE）','active','sales_channel',U&'["\9500\552E\6E20\9053","\6E20\9053","\95E8\5E97","\96F6\552E\7F51\7EDC","Channel"]'::jsonb),
 ('tpl_obj_hwfin_subsidiary','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\5B50\516C\53F8',U&'\9644\5C5E\516C\53F8/\96C6\56E2\5B9E\4F53（\5982\5C0F\7C73\5370\5EA6、\5883\5916\9644\5C5E\516C\53F8）','active','subsidiary',U&'["\5B50\516C\53F8","\9644\5C5E\516C\53F8","\96C6\56E2\5B9E\4F53","Subsidiary"]'::jsonb),
 ('tpl_obj_hwfin_risk','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\98CE\9669\56E0\7D20',U&'\5E74\62A5\62AB\9732\7684\98CE\9669\56E0\7D20（\5982\7ADE\4E89、\8206\60C5、\5730\7F18\653F\6CBB、\6C14\5019、\5916\6C47\98CE\9669）','active','risk_factor',U&'["\98CE\9669\56E0\7D20","\98CE\9669","Risk Factor"]'::jsonb),
 ('tpl_obj_hwfin_legal','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\6CD5\5F8B\8BC9\8BBC',U&'\8BC9\8BBC/\76D1\7BA1\8C03\67E5/\6216\7136\8D1F\503A\4E8B\9879（\5982\5C0F\7C73\5370\5EA6\8C03\67E5\4E0E\8D44\4EA7\51BB\7ED3）','active','legal_proceeding',U&'["\6CD5\5F8B\8BC9\8BBC","\8BC9\8BBC","\76D1\7BA1\8C03\67E5","\6216\7136\8D1F\503A","Legal Proceeding"]'::jsonb),
 ('tpl_obj_hwfin_esginit','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\53EF\6301\7EED\4E3E\63AA',U&'ESG/\53EF\6301\7EED\53D1\5C55\4E3E\63AA\4E0E\884C\52A8（\5982\7269\6D41\4F4E\78B3、\7EFF\7535\91C7\8D2D、\4EE5\65E7\6362\65B0、\78B3\51CF\6392）','active','sustainability_initiative',U&'["\53EF\6301\7EED\4E3E\63AA","ESG\4E3E\63AA","\53EF\6301\7EED\53D1\5C55","Sustainability Initiative"]'::jsonb)
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_domain.template_attributes
    (id, tenant_id, template_object_id, attr_name, description, attr_type, is_primary_key, constraints_json, sort_order, ontology_code, is_required)
VALUES

    ('tpl_attr_hwfin_co_stock','tenant_jonex_demo','tpl_obj_hwfin_company',U&'\80A1\7968\4EE3\7801',U&'\4EA4\6613\6240\80A1\7968\4EE3\7801（\5982 HK01810）',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'stock_code',1),
    ('tpl_attr_hwfin_co_name','tenant_jonex_demo','tpl_obj_hwfin_company',U&'\516C\53F8\540D\79F0',U&'\516C\53F8\5168\79F0',U&'\5B57\7B26\4E32',0,'{}'::jsonb,2,'company_name',1),
    ('tpl_attr_hwfin_co_exchange','tenant_jonex_demo','tpl_obj_hwfin_company',U&'\4E0A\5E02\4EA4\6613\6240',U&'\5982\6E2F\4EA4\6240、\4E0A\4EA4\6240、\6DF1\4EA4\6240、\7EB3\65AF\8FBE\514B',U&'\679A\4E3E',0,'{}'::jsonb,3,'exchange',0),
    ('tpl_attr_hwfin_co_industry','tenant_jonex_demo','tpl_obj_hwfin_company',U&'\6240\5C5E\884C\4E1A',U&'\5982\786C\4EF6\4E92\8054\7F51、\6D88\8D39\7535\5B50、\667A\80FD\51FA\884C',U&'\679A\4E3E',0,'{}'::jsonb,4,'industry',0),
    ('tpl_attr_hwfin_co_founded','tenant_jonex_demo','tpl_obj_hwfin_company',U&'\6210\7ACB\65E5\671F',U&'\516C\53F8\6210\7ACB\65E5\671F',U&'\65E5\671F',0,'{}'::jsonb,5,'founded_date',0),
    ('tpl_attr_hwfin_co_chairman','tenant_jonex_demo','tpl_obj_hwfin_company',U&'\8463\4E8B\957F',U&'\8463\4E8B\957F\59D3\540D',U&'\5B57\7B26\4E32',0,'{}'::jsonb,6,'chairman',0),
    ('tpl_attr_hwfin_co_ceo','tenant_jonex_demo','tpl_obj_hwfin_company',U&'\9996\5E2D\6267\884C\5B98',U&'CEO \59D3\540D',U&'\5B57\7B26\4E32',0,'{}'::jsonb,7,'ceo',0),
    ('tpl_attr_hwfin_co_hq','tenant_jonex_demo','tpl_obj_hwfin_company',U&'\603B\90E8',U&'\603B\90E8\6240\5728\5730',U&'\5B57\7B26\4E32',0,'{}'::jsonb,8,'headquarters',0),
    ('tpl_attr_hwfin_co_desc','tenant_jonex_demo','tpl_obj_hwfin_company',U&'\516C\53F8\7B80\4ECB',U&'\4E3B\8425\4E1A\52A1\4E0E\6838\5FC3\7ADE\4E89\529B\6982\8FF0',U&'\6587\672C',0,'{}'::jsonb,9,'company_description',0),

    ('tpl_attr_hwfin_rpt_id','tenant_jonex_demo','tpl_obj_hwfin_report',U&'\62A5\544AID',U&'\62A5\544A\552F\4E00\6807\8BC6',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'report_id',1),
    ('tpl_attr_hwfin_rpt_type','tenant_jonex_demo','tpl_obj_hwfin_report',U&'\62A5\544A\7C7B\578B','annual/quarterly/interim',U&'\679A\4E3E',0,'{}'::jsonb,2,'report_type',0),
    ('tpl_attr_hwfin_rpt_year','tenant_jonex_demo','tpl_obj_hwfin_report',U&'\8D22\5E74',U&'\8D22\62A5\6240\5C5E\8D22\5E74',U&'\6570\503C',0,'{}'::jsonb,3,'fiscal_year',1),
    ('tpl_attr_hwfin_rpt_period','tenant_jonex_demo','tpl_obj_hwfin_report',U&'\62A5\544A\671F',U&'\5982 2025FY / 2025Q4',U&'\5B57\7B26\4E32',0,'{}'::jsonb,4,'reporting_period',0),
    ('tpl_attr_hwfin_rpt_release','tenant_jonex_demo','tpl_obj_hwfin_report',U&'\53D1\5E03\65E5\671F',U&'\8D22\62A5\53D1\5E03\65E5\671F',U&'\65E5\671F',0,'{}'::jsonb,5,'release_date',0),
    ('tpl_attr_hwfin_rpt_currency','tenant_jonex_demo','tpl_obj_hwfin_report',U&'\5E01\79CD',U&'\5982\4EBA\6C11\5E01、\7F8E\5143',U&'\5B57\7B26\4E32',0,'{}'::jsonb,6,'currency',0),
    ('tpl_attr_hwfin_rpt_revenue','tenant_jonex_demo','tpl_obj_hwfin_report',U&'\603B\8425\6536',U&'\62A5\544A\671F\603B\8425\6536（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,7,'total_revenue',0),
    ('tpl_attr_hwfin_rpt_rev_yoy','tenant_jonex_demo','tpl_obj_hwfin_report',U&'\8425\6536\540C\6BD4',U&'\603B\8425\6536\540C\6BD4\589E\957F\7387（%）',U&'\6570\503C',0,'{}'::jsonb,8,'revenue_yoy',0),
    ('tpl_attr_hwfin_rpt_cogs','tenant_jonex_demo','tpl_obj_hwfin_report',U&'\9500\552E\6210\672C',U&'\62A5\544A\671F\9500\552E\6210\672C（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,9,'cost_of_sales',0),
    ('tpl_attr_hwfin_rpt_gp','tenant_jonex_demo','tpl_obj_hwfin_report',U&'\6BDB\5229',U&'\62A5\544A\671F\6BDB\5229（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,10,'gross_profit',0),
    ('tpl_attr_hwfin_rpt_gm','tenant_jonex_demo','tpl_obj_hwfin_report',U&'\6BDB\5229\7387',U&'\6BDB\5229\7387（%）',U&'\6570\503C',0,'{}'::jsonb,11,'gross_margin',0),
    ('tpl_attr_hwfin_rpt_selling','tenant_jonex_demo','tpl_obj_hwfin_report',U&'\9500\552E\53CA\63A8\5E7F\5F00\652F',U&'\62A5\544A\671F\9500\552E\53CA\63A8\5E7F\5F00\652F（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,12,'selling_expense',0),
    ('tpl_attr_hwfin_rpt_admin','tenant_jonex_demo','tpl_obj_hwfin_report',U&'\884C\653F\5F00\652F',U&'\62A5\544A\671F\884C\653F\5F00\652F（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,13,'admin_expense',0),
    ('tpl_attr_hwfin_rpt_rnd','tenant_jonex_demo','tpl_obj_hwfin_report',U&'\7814\53D1\5F00\652F',U&'\62A5\544A\671F\7814\53D1\5F00\652F（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,14,'rnd_expense',0),
    ('tpl_attr_hwfin_rpt_op','tenant_jonex_demo','tpl_obj_hwfin_report',U&'\7ECF\8425\5229\6DA6',U&'\62A5\544A\671F\7ECF\8425\5229\6DA6（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,15,'operating_profit',0),
    ('tpl_attr_hwfin_rpt_fincome','tenant_jonex_demo','tpl_obj_hwfin_report',U&'\8D22\52A1\6536\5165\51C0\989D',U&'\62A5\544A\671F\8D22\52A1\6536\5165\51C0\989D（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,16,'finance_income_net',0),
    ('tpl_attr_hwfin_rpt_pbt','tenant_jonex_demo','tpl_obj_hwfin_report',U&'\9664\6240\5F97\7A0E\524D\5229\6DA6',U&'\62A5\544A\671F\9664\6240\5F97\7A0E\524D\5229\6DA6（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,17,'profit_before_tax',0),
    ('tpl_attr_hwfin_rpt_tax','tenant_jonex_demo','tpl_obj_hwfin_report',U&'\6240\5F97\7A0E\8D39\7528',U&'\62A5\544A\671F\6240\5F97\7A0E\8D39\7528（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,18,'income_tax_expense',0),
    ('tpl_attr_hwfin_rpt_np','tenant_jonex_demo','tpl_obj_hwfin_report',U&'\5E74\5EA6\5229\6DA6',U&'\62A5\544A\671F\5E74\5EA6\5229\6DA6（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,19,'net_profit',0),
    ('tpl_attr_hwfin_rpt_anp','tenant_jonex_demo','tpl_obj_hwfin_report',U&'\7ECF\8C03\6574\51C0\5229\6DA6',U&'\7ECF\8C03\6574\51C0\5229\6DA6（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,20,'adjusted_net_profit',0),
    ('tpl_attr_hwfin_rpt_anp_yoy','tenant_jonex_demo','tpl_obj_hwfin_report',U&'\7ECF\8C03\6574\51C0\5229\6DA6\540C\6BD4',U&'\7ECF\8C03\6574\51C0\5229\6DA6\540C\6BD4\589E\957F\7387（%）',U&'\6570\503C',0,'{}'::jsonb,21,'adjusted_net_profit_yoy',0),

    ('tpl_attr_hwfin_seg_code','tenant_jonex_demo','tpl_obj_hwfin_segment',U&'\5206\90E8\4EE3\7801',U&'\5206\90E8\552F\4E00\6807\8BC6',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'segment_code',1),
    ('tpl_attr_hwfin_seg_name','tenant_jonex_demo','tpl_obj_hwfin_segment',U&'\5206\90E8\540D\79F0',U&'\5982\624B\673A×AIoT、\667A\80FD\7535\52A8\6C7D\8F66\53CAAI\7B49\521B\65B0\4E1A\52A1',U&'\5B57\7B26\4E32',0,'{}'::jsonb,2,'segment_name',1),
    ('tpl_attr_hwfin_seg_type','tenant_jonex_demo','tpl_obj_hwfin_segment',U&'\5206\90E8\7C7B\578B',U&'\5982\6838\5FC3\4E1A\52A1、\521B\65B0\4E1A\52A1',U&'\679A\4E3E',0,'{}'::jsonb,3,'segment_type',0),
    ('tpl_attr_hwfin_seg_rev','tenant_jonex_demo','tpl_obj_hwfin_segment',U&'\5206\90E8\8425\6536',U&'\5206\90E8\8425\6536（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,4,'revenue',0),
    ('tpl_attr_hwfin_seg_rev_yoy','tenant_jonex_demo','tpl_obj_hwfin_segment',U&'\8425\6536\540C\6BD4',U&'\5206\90E8\8425\6536\540C\6BD4\589E\957F\7387（%）',U&'\6570\503C',0,'{}'::jsonb,5,'revenue_yoy',0),
    ('tpl_attr_hwfin_seg_ratio','tenant_jonex_demo','tpl_obj_hwfin_segment',U&'\8425\6536\5360\6BD4',U&'\5206\90E8\8425\6536\5360\603B\8425\6536\6BD4\4F8B（%）',U&'\6570\503C',0,'{}'::jsonb,6,'revenue_ratio',0),
    ('tpl_attr_hwfin_seg_cogs','tenant_jonex_demo','tpl_obj_hwfin_segment',U&'\5206\90E8\9500\552E\6210\672C',U&'\5206\90E8\9500\552E\6210\672C（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,7,'cost_of_sales',0),
    ('tpl_attr_hwfin_seg_gp','tenant_jonex_demo','tpl_obj_hwfin_segment',U&'\5206\90E8\6BDB\5229',U&'\5206\90E8\6BDB\5229（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,8,'gross_profit',0),
    ('tpl_attr_hwfin_seg_gm','tenant_jonex_demo','tpl_obj_hwfin_segment',U&'\5206\90E8\6BDB\5229\7387',U&'\5206\90E8\6BDB\5229\7387（%）',U&'\6570\503C',0,'{}'::jsonb,9,'gross_margin',0),
    ('tpl_attr_hwfin_seg_op','tenant_jonex_demo','tpl_obj_hwfin_segment',U&'\5206\90E8\7ECF\8425\6536\76CA',U&'\5206\90E8\7ECF\8425\6536\76CA/(\4E8F\635F)（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,10,'operating_result',0),
    ('tpl_attr_hwfin_seg_anp','tenant_jonex_demo','tpl_obj_hwfin_segment',U&'\7ECF\8C03\6574\51C0\5229\6DA6',U&'\5206\90E8\7ECF\8C03\6574\51C0\5229\6DA6（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,11,'adjusted_net_profit',0),
    ('tpl_attr_hwfin_seg_anl','tenant_jonex_demo','tpl_obj_hwfin_segment',U&'\7ECF\8C03\6574\51C0\4E8F\635F',U&'\5206\90E8\7ECF\8C03\6574\51C0\4E8F\635F（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,12,'adjusted_net_loss',0),
    ('tpl_attr_hwfin_seg_desc','tenant_jonex_demo','tpl_obj_hwfin_segment',U&'\5206\90E8\63CF\8FF0',U&'\5206\90E8\4E1A\52A1\8303\56F4\4E0E\8868\73B0\8BF4\660E',U&'\6587\672C',0,'{}'::jsonb,13,'segment_description',0),

    ('tpl_attr_hwfin_ln_code','tenant_jonex_demo','tpl_obj_hwfin_line',U&'\4EA7\54C1\7EBF\4EE3\7801',U&'\4EA7\54C1\7EBF\552F\4E00\6807\8BC6',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'line_code',1),
    ('tpl_attr_hwfin_ln_name','tenant_jonex_demo','tpl_obj_hwfin_line',U&'\4EA7\54C1\7EBF\540D\79F0',U&'\5982\667A\80FD\624B\673A、IoT\4E0E\751F\6D3B\6D88\8D39\4EA7\54C1、\4E92\8054\7F51\670D\52A1、\667A\80FD\7535\52A8\6C7D\8F66',U&'\5B57\7B26\4E32',0,'{}'::jsonb,2,'line_name',1),
    ('tpl_attr_hwfin_ln_cat','tenant_jonex_demo','tpl_obj_hwfin_line',U&'\7C7B\522B',U&'\4EA7\54C1\7EBF\7C7B\522B',U&'\679A\4E3E',0,'{}'::jsonb,3,'category',0),
    ('tpl_attr_hwfin_ln_rev','tenant_jonex_demo','tpl_obj_hwfin_line',U&'\4EA7\54C1\7EBF\8425\6536',U&'\4EA7\54C1\7EBF\8425\6536（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,4,'revenue',0),
    ('tpl_attr_hwfin_ln_rev_yoy','tenant_jonex_demo','tpl_obj_hwfin_line',U&'\8425\6536\540C\6BD4',U&'\4EA7\54C1\7EBF\8425\6536\540C\6BD4\589E\957F\7387（%）',U&'\6570\503C',0,'{}'::jsonb,5,'revenue_yoy',0),
    ('tpl_attr_hwfin_ln_ratio','tenant_jonex_demo','tpl_obj_hwfin_line',U&'\8425\6536\5360\6BD4',U&'\4EA7\54C1\7EBF\8425\6536\5360\603B\8425\6536\6BD4\4F8B（%）',U&'\6570\503C',0,'{}'::jsonb,6,'revenue_ratio',0),
    ('tpl_attr_hwfin_ln_cogs','tenant_jonex_demo','tpl_obj_hwfin_line',U&'\4EA7\54C1\7EBF\9500\552E\6210\672C',U&'\4EA7\54C1\7EBF\9500\552E\6210\672C（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,7,'cost_of_sales',0),
    ('tpl_attr_hwfin_ln_gp','tenant_jonex_demo','tpl_obj_hwfin_line',U&'\4EA7\54C1\7EBF\6BDB\5229',U&'\4EA7\54C1\7EBF\6BDB\5229（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,8,'gross_profit',0),
    ('tpl_attr_hwfin_ln_gm','tenant_jonex_demo','tpl_obj_hwfin_line',U&'\4EA7\54C1\7EBF\6BDB\5229\7387',U&'\4EA7\54C1\7EBF\6BDB\5229\7387（%）',U&'\6570\503C',0,'{}'::jsonb,9,'gross_margin',0),
    ('tpl_attr_hwfin_ln_desc','tenant_jonex_demo','tpl_obj_hwfin_line',U&'\63CF\8FF0',U&'\4EA7\54C1\7EBF\4E1A\52A1\8BF4\660E',U&'\6587\672C',0,'{}'::jsonb,10,'description',0),

    ('tpl_attr_hwfin_pd_code','tenant_jonex_demo','tpl_obj_hwfin_product',U&'\4EA7\54C1\4EE3\7801',U&'\4EA7\54C1\552F\4E00\6807\8BC6',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'product_code',1),
    ('tpl_attr_hwfin_pd_name','tenant_jonex_demo','tpl_obj_hwfin_product',U&'\4EA7\54C1\540D\79F0',U&'\5982\5C0F\7C73SU7、\5C0F\7C73SU7 Ultra、\5C0F\7C73YU7、\7C73\5BB6APP',U&'\5B57\7B26\4E32',0,'{}'::jsonb,2,'product_name',1),
    ('tpl_attr_hwfin_pd_cat','tenant_jonex_demo','tpl_obj_hwfin_product',U&'\4EA7\54C1\7C7B\522B',U&'\5982\667A\80FD\624B\673A、\7535\52A8\6C7D\8F66、\5BB6\7535、\5E94\7528',U&'\679A\4E3E',0,'{}'::jsonb,3,'product_category',0),
    ('tpl_attr_hwfin_pd_launch','tenant_jonex_demo','tpl_obj_hwfin_product',U&'\4E0A\5E02\65E5\671F',U&'\4EA7\54C1\4E0A\5E02/\53D1\5E03\65E5\671F',U&'\65E5\671F',0,'{}'::jsonb,4,'launch_date',0),
    ('tpl_attr_hwfin_pd_ship','tenant_jonex_demo','tpl_obj_hwfin_product',U&'\51FA\8D27\91CF',U&'\4EA7\54C1\51FA\8D27\91CF/\4EA4\4ED8\91CF',U&'\6570\503C',0,'{}'::jsonb,5,'shipment_volume',0),
    ('tpl_attr_hwfin_pd_ship_yoy','tenant_jonex_demo','tpl_obj_hwfin_product',U&'\51FA\8D27\91CF\540C\6BD4',U&'\51FA\8D27\91CF\540C\6BD4\589E\957F\7387（%）',U&'\6570\503C',0,'{}'::jsonb,6,'shipment_yoy',0),
    ('tpl_attr_hwfin_pd_asp','tenant_jonex_demo','tpl_obj_hwfin_product',U&'\5E73\5747\552E\4EF7',U&'\4EA7\54C1\5E73\5747\552E\4EF7（\5143）',U&'\6570\503C',0,'{}'::jsonb,7,'asp',0),
    ('tpl_attr_hwfin_pd_asp_yoy','tenant_jonex_demo','tpl_obj_hwfin_product',U&'ASP\540C\6BD4',U&'\5E73\5747\552E\4EF7\540C\6BD4\589E\957F\7387（%）',U&'\6570\503C',0,'{}'::jsonb,8,'asp_yoy',0),
    ('tpl_attr_hwfin_pd_gm','tenant_jonex_demo','tpl_obj_hwfin_product',U&'\6BDB\5229\7387',U&'\4EA7\54C1\6BDB\5229\7387（%）',U&'\6570\503C',0,'{}'::jsonb,9,'gross_margin',0),
    ('tpl_attr_hwfin_pd_share','tenant_jonex_demo','tpl_obj_hwfin_product',U&'\5E02\5360\7387',U&'\4EA7\54C1\5E02\573A\4EFD\989D（%）',U&'\6570\503C',0,'{}'::jsonb,10,'market_share',0),
    ('tpl_attr_hwfin_pd_desc','tenant_jonex_demo','tpl_obj_hwfin_product',U&'\4EA7\54C1\63CF\8FF0',U&'\4EA7\54C1\5B9A\4F4D\4E0E\6838\5FC3\5356\70B9',U&'\6587\672C',0,'{}'::jsonb,11,'product_description',0),

    ('tpl_attr_hwfin_fm_code','tenant_jonex_demo','tpl_obj_hwfin_fin_metric',U&'\6307\6807\4EE3\7801',U&'\6307\6807\552F\4E00\6807\8BC6',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'metric_code',1),
    ('tpl_attr_hwfin_fm_name','tenant_jonex_demo','tpl_obj_hwfin_fin_metric',U&'\6307\6807\540D\79F0',U&'\5982\603B\8425\6536、\6BDB\5229、\7ECF\8425\5229\6DA6',U&'\5B57\7B26\4E32',0,'{}'::jsonb,2,'metric_name',1),
    ('tpl_attr_hwfin_fm_val','tenant_jonex_demo','tpl_obj_hwfin_fin_metric',U&'\6307\6807\503C',U&'\6307\6807\6570\503C',U&'\6570\503C',0,'{}'::jsonb,3,'metric_value',0),
    ('tpl_attr_hwfin_fm_unit','tenant_jonex_demo','tpl_obj_hwfin_fin_metric',U&'\5355\4F4D',U&'\5982\4E07\5143、\4EBF\5143、%',U&'\5B57\7B26\4E32',0,'{}'::jsonb,4,'metric_unit',0),
    ('tpl_attr_hwfin_fm_yoy','tenant_jonex_demo','tpl_obj_hwfin_fin_metric',U&'\540C\6BD4',U&'\6307\6807\540C\6BD4\589E\957F\7387（%）',U&'\6570\503C',0,'{}'::jsonb,5,'metric_yoy',0),
    ('tpl_attr_hwfin_fm_period','tenant_jonex_demo','tpl_obj_hwfin_fin_metric',U&'\6307\6807\671F\95F4',U&'\5982 2025FY / 2025Q4',U&'\5B57\7B26\4E32',0,'{}'::jsonb,6,'metric_period',0),
    ('tpl_attr_hwfin_fm_cat','tenant_jonex_demo','tpl_obj_hwfin_fin_metric',U&'\6307\6807\5206\7C7B',U&'\5982\8425\6536、\5229\6DA6、\6210\672C',U&'\679A\4E3E',0,'{}'::jsonb,7,'metric_category',0),

    ('tpl_attr_hwfin_om_code','tenant_jonex_demo','tpl_obj_hwfin_op_metric',U&'\6307\6807\4EE3\7801',U&'\6307\6807\552F\4E00\6807\8BC6',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'metric_code',1),
    ('tpl_attr_hwfin_om_name','tenant_jonex_demo','tpl_obj_hwfin_op_metric',U&'\6307\6807\540D\79F0',U&'\5982\6708\6D3B、\51FA\8D27\91CF、\8FDE\63A5\8BBE\5907\6570',U&'\5B57\7B26\4E32',0,'{}'::jsonb,2,'metric_name',1),
    ('tpl_attr_hwfin_om_val','tenant_jonex_demo','tpl_obj_hwfin_op_metric',U&'\6307\6807\503C',U&'\6307\6807\6570\503C',U&'\6570\503C',0,'{}'::jsonb,3,'metric_value',0),
    ('tpl_attr_hwfin_om_unit','tenant_jonex_demo','tpl_obj_hwfin_op_metric',U&'\5355\4F4D',U&'\5982\4E07\53F0、\767E\4E07、\4EBF、%',U&'\5B57\7B26\4E32',0,'{}'::jsonb,4,'metric_unit',0),
    ('tpl_attr_hwfin_om_yoy','tenant_jonex_demo','tpl_obj_hwfin_op_metric',U&'\540C\6BD4',U&'\6307\6807\540C\6BD4\589E\957F\7387（%）',U&'\6570\503C',0,'{}'::jsonb,5,'metric_yoy',0),
    ('tpl_attr_hwfin_om_cat','tenant_jonex_demo','tpl_obj_hwfin_op_metric',U&'\6307\6807\5206\7C7B',U&'\5982 user/shipment/market_share/iot_device',U&'\679A\4E3E',0,'{}'::jsonb,6,'metric_category',0),
    ('tpl_attr_hwfin_om_region','tenant_jonex_demo','tpl_obj_hwfin_op_metric',U&'\7EDF\8BA1\533A\57DF',U&'\5982\5168\7403、\4E2D\56FD\5927\9646、\62C9\7F8E、\4E1C\5357\4E9A',U&'\5B57\7B26\4E32',0,'{}'::jsonb,7,'region',0),
    ('tpl_attr_hwfin_om_desc','tenant_jonex_demo','tpl_obj_hwfin_op_metric',U&'\6307\6807\63CF\8FF0',U&'\6307\6807\53E3\5F84\4E0E\7EDF\8BA1\8BF4\660E',U&'\6587\672C',0,'{}'::jsonb,8,'metric_description',0),

    ('tpl_attr_hwfin_rm_code','tenant_jonex_demo','tpl_obj_hwfin_rnd_metric',U&'\6307\6807\4EE3\7801',U&'\6307\6807\552F\4E00\6807\8BC6',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'metric_code',1),
    ('tpl_attr_hwfin_rm_name','tenant_jonex_demo','tpl_obj_hwfin_rnd_metric',U&'\6307\6807\540D\79F0',U&'\5982\7814\53D1\6295\5165、\7814\53D1\4EBA\5458\6570、\7D2F\8BA1\7814\53D1',U&'\5B57\7B26\4E32',0,'{}'::jsonb,2,'metric_name',1),
    ('tpl_attr_hwfin_rm_val','tenant_jonex_demo','tpl_obj_hwfin_rnd_metric',U&'\6307\6807\503C',U&'\6307\6807\6570\503C',U&'\6570\503C',0,'{}'::jsonb,3,'metric_value',0),
    ('tpl_attr_hwfin_rm_unit','tenant_jonex_demo','tpl_obj_hwfin_rnd_metric',U&'\5355\4F4D',U&'\5982\4E07\5143、\4EBA',U&'\5B57\7B26\4E32',0,'{}'::jsonb,4,'metric_unit',0),
    ('tpl_attr_hwfin_rm_yoy','tenant_jonex_demo','tpl_obj_hwfin_rnd_metric',U&'\540C\6BD4',U&'\6307\6807\540C\6BD4\589E\957F\7387（%）',U&'\6570\503C',0,'{}'::jsonb,5,'metric_yoy',0),
    ('tpl_attr_hwfin_rm_head','tenant_jonex_demo','tpl_obj_hwfin_rnd_metric',U&'\7814\53D1\4EBA\5458\6570',U&'\7814\53D1\4EBA\5458\6570\91CF',U&'\6570\503C',0,'{}'::jsonb,6,'rnd_headcount',0),
    ('tpl_attr_hwfin_rm_cum','tenant_jonex_demo','tpl_obj_hwfin_rnd_metric',U&'\7D2F\8BA1\7814\53D1\6295\5165',U&'\8FC7\53BB\82E5\5E72\5E74\7D2F\8BA1\7814\53D1\6295\5165（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,7,'cumulative_rnd',0),

    ('tpl_attr_hwfin_ce_code','tenant_jonex_demo','tpl_obj_hwfin_cost',U&'\8D39\7528\4EE3\7801',U&'\8D39\7528\9879\552F\4E00\6807\8BC6',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'expense_code',1),
    ('tpl_attr_hwfin_ce_name','tenant_jonex_demo','tpl_obj_hwfin_cost',U&'\8D39\7528\540D\79F0',U&'\5982\9500\552E\6210\672C、\9500\552E\63A8\5E7F、\884C\653F、\7814\53D1、\6240\5F97\7A0E',U&'\5B57\7B26\4E32',0,'{}'::jsonb,2,'expense_name',1),
    ('tpl_attr_hwfin_ce_cat','tenant_jonex_demo','tpl_obj_hwfin_cost',U&'\8D39\7528\5206\7C7B',U&'\5982 cost/selling/admin/rnd/tax',U&'\679A\4E3E',0,'{}'::jsonb,3,'expense_category',0),
    ('tpl_attr_hwfin_ce_val','tenant_jonex_demo','tpl_obj_hwfin_cost',U&'\8D39\7528\91D1\989D',U&'\8D39\7528\91D1\989D（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,4,'expense_value',0),
    ('tpl_attr_hwfin_ce_yoy','tenant_jonex_demo','tpl_obj_hwfin_cost',U&'\540C\6BD4',U&'\8D39\7528\540C\6BD4\589E\957F\7387（%）',U&'\6570\503C',0,'{}'::jsonb,5,'expense_yoy',0),
    ('tpl_attr_hwfin_ce_ratio','tenant_jonex_demo','tpl_obj_hwfin_cost',U&'\5360\8425\6536\6BD4',U&'\8D39\7528\5360\603B\8425\6536\6BD4\4F8B（%）',U&'\6570\503C',0,'{}'::jsonb,6,'expense_ratio',0),
    ('tpl_attr_hwfin_ce_period','tenant_jonex_demo','tpl_obj_hwfin_cost',U&'\8D39\7528\671F\95F4',U&'\5982 2025FY / 2025Q4',U&'\5B57\7B26\4E32',0,'{}'::jsonb,7,'expense_period',0),

    ('tpl_attr_hwfin_sr_code','tenant_jonex_demo','tpl_obj_hwfin_shareholder',U&'\4E8B\9879\4EE3\7801',U&'\4E8B\9879\552F\4E00\6807\8BC6',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'return_code',1),
    ('tpl_attr_hwfin_sr_type','tenant_jonex_demo','tpl_obj_hwfin_shareholder',U&'\4E8B\9879\7C7B\578B',U&'\5982 dividend/placement/buyback',U&'\679A\4E3E',0,'{}'::jsonb,2,'return_type',1),
    ('tpl_attr_hwfin_sr_desc','tenant_jonex_demo','tpl_obj_hwfin_shareholder',U&'\4E8B\9879\63CF\8FF0',U&'\5982\672B\671F\80A1\606F、2025\5E74\914D\552E\53CA\8BA4\8D2D',U&'\5B57\7B26\4E32',0,'{}'::jsonb,3,'return_description',0),
    ('tpl_attr_hwfin_sr_amount','tenant_jonex_demo','tpl_obj_hwfin_shareholder',U&'\91D1\989D/\89C4\6A21',U&'\4E8B\9879\91D1\989D\6216\89C4\6A21（\4E07\5143/\4E07\80A1）',U&'\6570\503C',0,'{}'::jsonb,4,'return_amount',0),
    ('tpl_attr_hwfin_sr_price','tenant_jonex_demo','tpl_obj_hwfin_shareholder',U&'\6BCF\80A1\4EF7\683C',U&'\6BCF\80A1\4EF7\683C（\6E2F\5143/\5143）',U&'\6570\503C',0,'{}'::jsonb,5,'per_share_price',0),
    ('tpl_attr_hwfin_sr_date','tenant_jonex_demo','tpl_obj_hwfin_shareholder',U&'\4E8B\9879\65E5\671F',U&'\4E8B\9879\53D1\751F/\5B8C\6210\65E5\671F',U&'\65E5\671F',0,'{}'::jsonb,6,'return_date',0),
    ('tpl_attr_hwfin_sr_status','tenant_jonex_demo','tpl_obj_hwfin_shareholder',U&'\4E8B\9879\72B6\6001',U&'\5982\5DF2\5BA3\6D3E/\4E0D\5BA3\6D3E/\5DF2\5B8C\6210',U&'\679A\4E3E',0,'{}'::jsonb,7,'return_status',0),

    ('tpl_attr_hwfin_eg_code','tenant_jonex_demo','tpl_obj_hwfin_esg',U&'\6307\6807\4EE3\7801',U&'\6307\6807\552F\4E00\6807\8BC6',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'metric_code',1),
    ('tpl_attr_hwfin_eg_name','tenant_jonex_demo','tpl_obj_hwfin_esg',U&'\6307\6807\540D\79F0',U&'\5982CDP\8BC4\7EA7、\78B3\6392\653E、\5149\4F0F\7528\7535',U&'\5B57\7B26\4E32',0,'{}'::jsonb,2,'metric_name',1),
    ('tpl_attr_hwfin_eg_cat','tenant_jonex_demo','tpl_obj_hwfin_esg',U&'\6307\6807\5206\7C7B',U&'\5982 environment/social/governance',U&'\679A\4E3E',0,'{}'::jsonb,3,'metric_category',0),
    ('tpl_attr_hwfin_eg_val','tenant_jonex_demo','tpl_obj_hwfin_esg',U&'\6307\6807\503C',U&'\6307\6807\6570\503C',U&'\6570\503C',0,'{}'::jsonb,4,'metric_value',0),
    ('tpl_attr_hwfin_eg_unit','tenant_jonex_demo','tpl_obj_hwfin_esg',U&'\5355\4F4D',U&'\5982\5428CO2e、\4E07\5EA6、\7EA7',U&'\5B57\7B26\4E32',0,'{}'::jsonb,5,'metric_unit',0),
    ('tpl_attr_hwfin_eg_yoy','tenant_jonex_demo','tpl_obj_hwfin_esg',U&'\540C\6BD4',U&'\6307\6807\540C\6BD4\53D8\5316（%）',U&'\6570\503C',0,'{}'::jsonb,6,'metric_yoy',0),
    ('tpl_attr_hwfin_eg_desc','tenant_jonex_demo','tpl_obj_hwfin_esg',U&'\6307\6807\63CF\8FF0',U&'\6307\6807\53E3\5F84\4E0E\8BF4\660E',U&'\6587\672C',0,'{}'::jsonb,7,'metric_description',0),

    ('tpl_attr_hwfin_kp_name','tenant_jonex_demo','tpl_obj_hwfin_person',U&'\59D3\540D',U&'\4EBA\5458\59D3\540D',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'person_name',1),
    ('tpl_attr_hwfin_kp_title','tenant_jonex_demo','tpl_obj_hwfin_person',U&'\804C\4F4D',U&'\804C\7EA7/\5934\8854',U&'\5B57\7B26\4E32',0,'{}'::jsonb,2,'title',1),
    ('tpl_attr_hwfin_kp_role','tenant_jonex_demo','tpl_obj_hwfin_person',U&'\89D2\8272',U&'\5982\8463\4E8B\957F、\526F\8463\4E8B\957F、CEO、\603B\88C1、\72EC\7ACB\975E\6267\884C\8463\4E8B',U&'\679A\4E3E',0,'{}'::jsonb,3,'role',0),
    ('tpl_attr_hwfin_kp_type','tenant_jonex_demo','tpl_obj_hwfin_person',U&'\8463\4E8B\7C7B\578B',U&'\5982\6267\884C\8463\4E8B、\975E\6267\884C\8463\4E8B、\72EC\7ACB\975E\6267\884C\8463\4E8B',U&'\679A\4E3E',0,'{}'::jsonb,4,'director_type',0),
    ('tpl_attr_hwfin_kp_co','tenant_jonex_demo','tpl_obj_hwfin_person',U&'\6240\5C5E\516C\53F8',U&'\4EFB\804C\516C\53F8',U&'\5B57\7B26\4E32',0,'{}'::jsonb,5,'affiliated_company',0),

    ('tpl_attr_hwfin_ev_name','tenant_jonex_demo','tpl_obj_hwfin_event',U&'\4E8B\4EF6\540D\79F0',U&'\4E8B\4EF6\6807\9898',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'event_name',1),
    ('tpl_attr_hwfin_ev_type','tenant_jonex_demo','tpl_obj_hwfin_event',U&'\4E8B\4EF6\7C7B\578B',U&'\5982\8D22\62A5\53D1\5E03、\4EA7\54C1\4EA4\4ED8、\6218\7565\53D1\5E03、\914D\552E',U&'\679A\4E3E',0,'{}'::jsonb,2,'event_type',0),
    ('tpl_attr_hwfin_ev_date','tenant_jonex_demo','tpl_obj_hwfin_event',U&'\4E8B\4EF6\65E5\671F',U&'\4E8B\4EF6\53D1\751F\65E5\671F',U&'\65E5\671F',0,'{}'::jsonb,3,'event_date',0),
    ('tpl_attr_hwfin_ev_desc','tenant_jonex_demo','tpl_obj_hwfin_event',U&'\4E8B\4EF6\63CF\8FF0',U&'\4E8B\4EF6\8BE6\60C5\6458\8981',U&'\6587\672C',0,'{}'::jsonb,4,'event_description',0),

    ('tpl_attr_hwfin_mk_name','tenant_jonex_demo','tpl_obj_hwfin_market',U&'\5E02\573A\540D\79F0',U&'\5730\533A/\5E02\573A\540D\79F0（\5982\4E2D\56FD\5927\9646、\5883\5916、\6B27\6D32、\5370\5EA6）',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'market_name',1),
    ('tpl_attr_hwfin_mk_type','tenant_jonex_demo','tpl_obj_hwfin_market',U&'\533A\57DF\7C7B\578B',U&'\4E2D\56FD\5927\9646/\5883\5916/\533A\57DF/\56FD\5BB6',U&'\679A\4E3E',0,'{}'::jsonb,2,'region_type',0),
    ('tpl_attr_hwfin_mk_rev','tenant_jonex_demo','tpl_obj_hwfin_market',U&'\5730\533A\8425\6536',U&'\8BE5\5730\533A\8425\6536（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,3,'revenue',0),
    ('tpl_attr_hwfin_mk_ratio','tenant_jonex_demo','tpl_obj_hwfin_market',U&'\8425\6536\5360\6BD4',U&'\8BE5\5730\533A\8425\6536\5360\603B\8425\6536\6BD4\4F8B（%）',U&'\6570\503C',0,'{}'::jsonb,4,'revenue_ratio',0),
    ('tpl_attr_hwfin_mk_store','tenant_jonex_demo','tpl_obj_hwfin_market',U&'\95E8\5E97\6570',U&'\8BE5\5730\533A\95E8\5E97/\670D\52A1\70B9\6570\91CF',U&'\6570\503C',0,'{}'::jsonb,5,'store_count',0),
    ('tpl_attr_hwfin_mk_desc','tenant_jonex_demo','tpl_obj_hwfin_market',U&'\5E02\573A\63CF\8FF0',U&'\5730\533A\5E02\573A\8868\73B0\4E0E\5E03\5C40\8BF4\660E',U&'\6587\672C',0,'{}'::jsonb,6,'market_description',0),

    ('tpl_attr_hwfin_ch_name','tenant_jonex_demo','tpl_obj_hwfin_channel',U&'\6E20\9053\540D\79F0',U&'\6E20\9053\540D\79F0（\5982\5C0F\7C73\4E4B\5BB6、\76F4\8425\5E97、\6388\6743\5E97、\7ECF\9500\5546、\5C0F\7C73\5546\57CE）',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'channel_name',1),
    ('tpl_attr_hwfin_ch_type','tenant_jonex_demo','tpl_obj_hwfin_channel',U&'\6E20\9053\7C7B\578B',U&'\7EBF\4E0A/\7EBF\4E0B/\76F4\8425/\6388\6743/\7ECF\9500',U&'\679A\4E3E',0,'{}'::jsonb,2,'channel_type',0),
    ('tpl_attr_hwfin_ch_store','tenant_jonex_demo','tpl_obj_hwfin_channel',U&'\95E8\5E97\6570',U&'\6E20\9053\95E8\5E97/\7F51\70B9\6570\91CF',U&'\6570\503C',0,'{}'::jsonb,3,'store_count',0),
    ('tpl_attr_hwfin_ch_region','tenant_jonex_demo','tpl_obj_hwfin_channel',U&'\8986\76D6\5730\533A',U&'\6E20\9053\8986\76D6\5730\533A',U&'\5B57\7B26\4E32',0,'{}'::jsonb,4,'region',0),
    ('tpl_attr_hwfin_ch_desc','tenant_jonex_demo','tpl_obj_hwfin_channel',U&'\6E20\9053\63CF\8FF0',U&'\6E20\9053\8FD0\8425\4E0E\5E03\5C40\8BF4\660E',U&'\6587\672C',0,'{}'::jsonb,5,'channel_description',0),

    ('tpl_attr_hwfin_sub_name','tenant_jonex_demo','tpl_obj_hwfin_subsidiary',U&'\5B50\516C\53F8\540D\79F0',U&'\9644\5C5E\516C\53F8/\96C6\56E2\5B9E\4F53\540D\79F0（\5982\5C0F\7C73\5370\5EA6）',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'subsidiary_name',1),
    ('tpl_attr_hwfin_sub_loc','tenant_jonex_demo','tpl_obj_hwfin_subsidiary',U&'\6240\5728\5730',U&'\5B50\516C\53F8\6240\5728\56FD\5BB6/\5730\533A',U&'\5B57\7B26\4E32',0,'{}'::jsonb,2,'location',0),
    ('tpl_attr_hwfin_sub_own','tenant_jonex_demo','tpl_obj_hwfin_subsidiary',U&'\6301\80A1\6BD4\4F8B',U&'\6BCD\516C\53F8\6301\80A1\6BD4\4F8B（%）',U&'\6570\503C',0,'{}'::jsonb,3,'ownership',0),
    ('tpl_attr_hwfin_sub_scope','tenant_jonex_demo','tpl_obj_hwfin_subsidiary',U&'\7ECF\8425\8303\56F4',U&'\5B50\516C\53F8\4E3B\8425\4E1A\52A1\8303\56F4',U&'\5B57\7B26\4E32',0,'{}'::jsonb,4,'business_scope',0),
    ('tpl_attr_hwfin_sub_desc','tenant_jonex_demo','tpl_obj_hwfin_subsidiary',U&'\5B50\516C\53F8\63CF\8FF0',U&'\5B50\516C\53F8\60C5\51B5\8BF4\660E',U&'\6587\672C',0,'{}'::jsonb,5,'subsidiary_description',0),

    ('tpl_attr_hwfin_rk_name','tenant_jonex_demo','tpl_obj_hwfin_risk',U&'\98CE\9669\540D\79F0',U&'\98CE\9669\56E0\7D20\540D\79F0（\5982\7ADE\4E89\98CE\9669、\5730\7F18\653F\6CBB\98CE\9669）',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'risk_name',1),
    ('tpl_attr_hwfin_rk_cat','tenant_jonex_demo','tpl_obj_hwfin_risk',U&'\98CE\9669\7C7B\522B',U&'\7ADE\4E89/\5E02\573A/\653F\6CBB/\6C14\5019/\8D22\52A1/\8FD0\8425/\5408\89C4',U&'\679A\4E3E',0,'{}'::jsonb,2,'risk_category',0),
    ('tpl_attr_hwfin_rk_desc','tenant_jonex_demo','tpl_obj_hwfin_risk',U&'\98CE\9669\63CF\8FF0',U&'\98CE\9669\6210\56E0\4E0E\6F5C\5728\5F71\54CD\8BF4\660E',U&'\6587\672C',0,'{}'::jsonb,3,'risk_description',0),
    ('tpl_attr_hwfin_rk_mit','tenant_jonex_demo','tpl_obj_hwfin_risk',U&'\5E94\5BF9\63AA\65BD',U&'\98CE\9669\7F13\91CA/\5E94\5BF9\63AA\65BD',U&'\6587\672C',0,'{}'::jsonb,4,'mitigation',0),

    ('tpl_attr_hwfin_lg_name','tenant_jonex_demo','tpl_obj_hwfin_legal',U&'\6848\4EF6\540D\79F0',U&'\8BC9\8BBC/\76D1\7BA1\4E8B\9879\540D\79F0',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'case_name',1),
    ('tpl_attr_hwfin_lg_juris','tenant_jonex_demo','tpl_obj_hwfin_legal',U&'\53F8\6CD5\7BA1\8F96',U&'\6D89\53CA\56FD\5BB6/\5730\533A/\76D1\7BA1\673A\6784（\5982\5370\5EA6\7A0E\52A1\5C40）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,2,'jurisdiction',0),
    ('tpl_attr_hwfin_lg_status','tenant_jonex_demo','tpl_obj_hwfin_legal',U&'\6848\4EF6\72B6\6001',U&'\8C03\67E5\4E2D/\807D\8B49/\5DF2\7ED3\6848\7B49',U&'\679A\4E3E',0,'{}'::jsonb,3,'status',0),
    ('tpl_attr_hwfin_lg_amount','tenant_jonex_demo','tpl_obj_hwfin_legal',U&'\6D89\53CA\91D1\989D',U&'\6D89\6848/\51BB\7ED3/\64A5\5099\91D1\989D（\4E07\5143）',U&'\6570\503C',0,'{}'::jsonb,4,'amount_involved',0),
    ('tpl_attr_hwfin_lg_desc','tenant_jonex_demo','tpl_obj_hwfin_legal',U&'\6848\4EF6\63CF\8FF0',U&'\4E8B\9879\8BE6\60C5\4E0E\8FDB\5C55\8BF4\660E',U&'\6587\672C',0,'{}'::jsonb,5,'case_description',0),

    ('tpl_attr_hwfin_si_name','tenant_jonex_demo','tpl_obj_hwfin_esginit',U&'\4E3E\63AA\540D\79F0',U&'\53EF\6301\7EED/ESG \4E3E\63AA\540D\79F0（\5982\7269\6D41\4F4E\78B3、\4EE5\65E7\6362\65B0）',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'initiative_name',1),
    ('tpl_attr_hwfin_si_pillar','tenant_jonex_demo','tpl_obj_hwfin_esginit',U&'ESG\652F\67F1',U&'\73AF\5883/\793E\4F1A/\7BA1\6CBB',U&'\679A\4E3E',0,'{}'::jsonb,2,'esg_pillar',0),
    ('tpl_attr_hwfin_si_target','tenant_jonex_demo','tpl_obj_hwfin_esginit',U&'\76EE\6807',U&'\4E3E\63AA\76EE\6807（\5982\78B3\51CF\6392\76EE\6807）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,3,'target',0),
    ('tpl_attr_hwfin_si_progress','tenant_jonex_demo','tpl_obj_hwfin_esginit',U&'\8FDB\5C55',U&'\4E3E\63AA\8FDB\5C55/\6210\6548（\5982\51CF\5C11\7EA62,471\5428CO2e）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,4,'progress',0),
    ('tpl_attr_hwfin_si_desc','tenant_jonex_demo','tpl_obj_hwfin_esginit',U&'\4E3E\63AA\63CF\8FF0',U&'\4E3E\63AA\5185\5BB9\4E0E\65B9\6CD5\8BF4\660E',U&'\6587\672C',0,'{}'::jsonb,5,'initiative_description',0)
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_domain.template_relations
    (id, tenant_id, domain_id, scenario_id, name, description, source_object_id, target_object_id, relation_type, status, ontology_code, aliases)
VALUES
 ('tpl_rel_hwfin_issues','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\53D1\5E03\62A5\544A',U&'\4E0A\5E02\516C\53F8\53D1\5E03\8D22\52A1\62A5\544A','tpl_obj_hwfin_company','tpl_obj_hwfin_report',U&'\4E00\5BF9\591A','active','ISSUES_REPORT',U&'["\53D1\5E03\62A5\544A","\62AB\9732","\51FA\5177"]'::jsonb),
 ('tpl_rel_hwfin_has_seg','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\5305\542B\5206\90E8',U&'\8D22\52A1\62A5\544A\5305\542B\7684\4E1A\52A1\5206\90E8','tpl_obj_hwfin_report','tpl_obj_hwfin_segment',U&'\4E00\5BF9\591A','active','HAS_SEGMENT',U&'["\5305\542B\5206\90E8","\6DB5\76D6\5206\90E8"]'::jsonb),
 ('tpl_rel_hwfin_seg_line','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\5206\90E8\542B\4EA7\54C1\7EBF',U&'\4E1A\52A1\5206\90E8\4E0B\7684\4EA7\54C1\7EBF','tpl_obj_hwfin_segment','tpl_obj_hwfin_line',U&'\4E00\5BF9\591A','active','SEGMENT_INCLUDES_LINE',U&'["\5305\542B\4EA7\54C1\7EBF","\4E0B\8BBE\4EA7\54C1\7EBF"]'::jsonb),
 ('tpl_rel_hwfin_line_prod','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\4EA7\54C1\7EBF\4EA7\51FA\4EA7\54C1',U&'\4EA7\54C1\7EBF\4EA7\51FA\7684\5177\4F53\4EA7\54C1','tpl_obj_hwfin_line','tpl_obj_hwfin_product',U&'\4E00\5BF9\591A','active','LINE_PRODUCES_PRODUCT',U&'["\4EA7\51FA","\751F\4EA7","\5305\542B\4EA7\54C1"]'::jsonb),
 ('tpl_rel_hwfin_rpt_fm','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\62A5\544A\8D22\52A1\6307\6807',U&'\8D22\52A1\62A5\544A\62AB\9732\7684\8D22\52A1\6307\6807','tpl_obj_hwfin_report','tpl_obj_hwfin_fin_metric',U&'\4E00\5BF9\591A','active','REPORT_HAS_FINANCIAL_METRIC',U&'["\62AB\9732\6307\6807","\542B\6307\6807"]'::jsonb),
 ('tpl_rel_hwfin_seg_fm','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\5206\90E8\8D22\52A1\6307\6807',U&'\4E1A\52A1\5206\90E8\62AB\9732\7684\8D22\52A1\6307\6807','tpl_obj_hwfin_segment','tpl_obj_hwfin_fin_metric',U&'\4E00\5BF9\591A','active','SEGMENT_HAS_METRIC',U&'["\5206\90E8\6307\6807"]'::jsonb),
 ('tpl_rel_hwfin_pd_om','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\4EA7\54C1\8FD0\8425\6307\6807',U&'\4EA7\54C1\5BF9\5E94\7684\8FD0\8425\6307\6807','tpl_obj_hwfin_product','tpl_obj_hwfin_op_metric',U&'\4E00\5BF9\591A','active','PRODUCT_HAS_OPERATIONAL_METRIC',U&'["\4EA7\54C1\6307\6807"]'::jsonb),
 ('tpl_rel_hwfin_co_kp','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\5173\952E\4EBA\5458',U&'\4E0A\5E02\516C\53F8\5173\952E\7BA1\7406\4EBA\5458','tpl_obj_hwfin_company','tpl_obj_hwfin_person',U&'\4E00\5BF9\591A','active','COMPANY_HAS_KEYPERSON',U&'["\9AD8\7BA1","\7BA1\7406\5C42"]'::jsonb),
 ('tpl_rel_hwfin_co_ev','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\53C2\4E0E\4E8B\4EF6',U&'\4E0A\5E02\516C\53F8\53C2\4E0E/\62AB\9732\7684\4E1A\52A1\4E8B\4EF6','tpl_obj_hwfin_company','tpl_obj_hwfin_event',U&'\591A\5BF9\591A','active','PARTICIPATES_EVENT',U&'["\53C2\4E0E","\62AB\9732\4E8B\4EF6"]'::jsonb),
 ('tpl_rel_hwfin_co_rm','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\7814\53D1\6307\6807',U&'\4E0A\5E02\516C\53F8\7814\53D1\6307\6807','tpl_obj_hwfin_company','tpl_obj_hwfin_rnd_metric',U&'\4E00\5BF9\591A','active','COMPANY_HAS_RND_METRIC',U&'["\7814\53D1\6295\5165"]'::jsonb),
 ('tpl_rel_hwfin_co_om','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\516C\53F8\8FD0\8425\6307\6807',U&'\4E0A\5E02\516C\53F8\6574\4F53\8FD0\8425\6307\6807','tpl_obj_hwfin_company','tpl_obj_hwfin_op_metric',U&'\4E00\5BF9\591A','active','COMPANY_HAS_OPERATIONAL_METRIC',U&'["\8FD0\8425\6307\6807"]'::jsonb),
 ('tpl_rel_hwfin_ln_fm','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\4EA7\54C1\7EBF\8D22\52A1\6307\6807',U&'\4EA7\54C1\7EBF\62AB\9732\7684\8D22\52A1\6307\6807','tpl_obj_hwfin_line','tpl_obj_hwfin_fin_metric',U&'\4E00\5BF9\591A','active','LINE_HAS_METRIC',U&'["\4EA7\54C1\7EBF\6307\6807"]'::jsonb),
 ('tpl_rel_hwfin_rpt_ce','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\62A5\544A\6210\672C\8D39\7528',U&'\8D22\52A1\62A5\544A\62AB\9732\7684\6210\672C\8D39\7528','tpl_obj_hwfin_report','tpl_obj_hwfin_cost',U&'\4E00\5BF9\591A','active','REPORT_HAS_COST_EXPENSE',U&'["\542B\8D39\7528","\62AB\9732\8D39\7528"]'::jsonb),
 ('tpl_rel_hwfin_seg_ce','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\5206\90E8\6210\672C\8D39\7528',U&'\4E1A\52A1\5206\90E8\62AB\9732\7684\6210\672C\8D39\7528','tpl_obj_hwfin_segment','tpl_obj_hwfin_cost',U&'\4E00\5BF9\591A','active','SEGMENT_HAS_COST_EXPENSE',U&'["\5206\90E8\8D39\7528"]'::jsonb),
 ('tpl_rel_hwfin_co_sr','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\80A1\4E1C\56DE\62A5',U&'\4E0A\5E02\516C\53F8\80A1\4E1C\56DE\62A5\4E8B\9879','tpl_obj_hwfin_company','tpl_obj_hwfin_shareholder',U&'\4E00\5BF9\591A','active','COMPANY_HAS_SHAREHOLDER_RETURN',U&'["\80A1\606F","\914D\552E","\56DE\8D2D"]'::jsonb),
 ('tpl_rel_hwfin_co_eg','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'ESG\6307\6807',U&'\4E0A\5E02\516C\53F8ESG\76F8\5173\6307\6807','tpl_obj_hwfin_company','tpl_obj_hwfin_esg',U&'\4E00\5BF9\591A','active','COMPANY_HAS_ESG_METRIC',U&'["ESG","\73AF\5883\793E\4F1A\7BA1\6CBB"]'::jsonb),
 ('tpl_rel_hwfin_co_mkt','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\5730\533A\7ECF\8425',U&'\4E0A\5E02\516C\53F8\5728\5404\5730\533A\5E02\573A\8FD0\8425','tpl_obj_hwfin_company','tpl_obj_hwfin_market',U&'\4E00\5BF9\591A','active','COMPANY_OPERATES_IN_MARKET',U&'["\5730\533A\7ECF\8425","\5206\5730\533A","\5E02\573A\5E03\5C40"]'::jsonb),
 ('tpl_rel_hwfin_seg_mkt','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\5206\5730\533A\8425\6536',U&'\4E1A\52A1\5206\90E8\5728\5404\5730\533A\7684\8425\6536\5206\5E03','tpl_obj_hwfin_segment','tpl_obj_hwfin_market',U&'\591A\5BF9\591A','active','SEGMENT_SELLS_IN_MARKET',U&'["\5206\5730\533A\8425\6536","\5730\533A\6536\5165"]'::jsonb),
 ('tpl_rel_hwfin_co_ch','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\9500\552E\6E20\9053',U&'\4E0A\5E02\516C\53F8\901A\8FC7\6E20\9053\9500\552E','tpl_obj_hwfin_company','tpl_obj_hwfin_channel',U&'\4E00\5BF9\591A','active','COMPANY_USES_CHANNEL',U&'["\9500\552E\6E20\9053","\6E20\9053\5E03\5C40"]'::jsonb),
 ('tpl_rel_hwfin_ch_mkt','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\6E20\9053\8986\76D6',U&'\9500\552E\6E20\9053\8986\76D6\7684\5730\533A\5E02\573A','tpl_obj_hwfin_channel','tpl_obj_hwfin_market',U&'\591A\5BF9\591A','active','CHANNEL_COVERS_MARKET',U&'["\6E20\9053\8986\76D6","\6E20\9053\5206\5E03"]'::jsonb),
 ('tpl_rel_hwfin_co_sub','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\5B50\516C\53F8',U&'\4E0A\5E02\516C\53F8\62E5\6709\7684\5B50\516C\53F8','tpl_obj_hwfin_company','tpl_obj_hwfin_subsidiary',U&'\4E00\5BF9\591A','active','COMPANY_HAS_SUBSIDIARY',U&'["\5B50\516C\53F8","\9644\5C5E\516C\53F8"]'::jsonb),
 ('tpl_rel_hwfin_sub_mkt','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\5B50\516C\53F8\6240\5728\5730',U&'\5B50\516C\53F8\6240\5728\7684\5730\533A\5E02\573A','tpl_obj_hwfin_subsidiary','tpl_obj_hwfin_market',U&'\591A\5BF9\4E00','active','SUBSIDIARY_LOCATED_IN_MARKET',U&'["\6240\5728\5730","\6CE8\518C\5730"]'::jsonb),
 ('tpl_rel_hwfin_co_risk','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\9762\4E34\98CE\9669',U&'\4E0A\5E02\516C\53F8\9762\4E34\7684\98CE\9669\56E0\7D20','tpl_obj_hwfin_company','tpl_obj_hwfin_risk',U&'\4E00\5BF9\591A','active','COMPANY_FACES_RISK',U&'["\9762\4E34\98CE\9669","\98CE\9669\62AB\9732"]'::jsonb),
 ('tpl_rel_hwfin_sub_lg','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\6D89\53CA\8BC9\8BBC',U&'\5B50\516C\53F8\6D89\53CA\7684\6CD5\5F8B\8BC9\8BBC/\76D1\7BA1\4E8B\9879','tpl_obj_hwfin_subsidiary','tpl_obj_hwfin_legal',U&'\4E00\5BF9\591A','active','SUBSIDIARY_INVOLVED_IN_PROCEEDING',U&'["\6D89\53CA\8BC9\8BBC","\6D89\8BC9"]'::jsonb),
 ('tpl_rel_hwfin_co_si','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\5F00\5C55\4E3E\63AA',U&'\4E0A\5E02\516C\53F8\5F00\5C55\7684\53EF\6301\7EED\4E3E\63AA','tpl_obj_hwfin_company','tpl_obj_hwfin_esginit',U&'\4E00\5BF9\591A','active','COMPANY_UNDERTAKES_INITIATIVE',U&'["\5F00\5C55\4E3E\63AA","\53EF\6301\7EED\884C\52A8"]'::jsonb),
 ('tpl_rel_hwfin_si_esg','tenant_jonex_demo','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance',U&'\6539\5584\6307\6807',U&'\53EF\6301\7EED\4E3E\63AA\6539\5584\7684ESG\6307\6807','tpl_obj_hwfin_esginit','tpl_obj_hwfin_esg',U&'\591A\5BF9\591A','active','INITIATIVE_IMPROVES_ESG',U&'["\6539\5584\6307\6807","\652F\6491ESG"]'::jsonb)
ON CONFLICT (id) DO NOTHING;




INSERT INTO knowledge_base.knowledge_info (id, tenant_id, space_id, name, description, data_source_types, document_count, status, owner_id) VALUES
    ('kb_demo_hw_inet_finance', 'tenant_jonex_demo', 'space_demo_test', U&'\786C\4EF6\4E92\8054\7F51\8D22\62A5\77E5\8BC6\5E93', U&'\786C\4EF6\4E92\8054\7F51\4E0A\5E02\516C\53F8\8D22\62A5\7ED3\6784\5316\62BD\53D6\6F14\793A（\57FA\4E8E\5C0F\7C73\96C6\56E22025\5E74\5EA6\62A5\544A）', '["file"]'::jsonb, 0, 'synced', '1')
ON CONFLICT (id) DO NOTHING;


INSERT INTO knowledge_base.knowledge_data_sources
    (id, tenant_id, knowledge_base_id, access_method_id,access_type, name, config_json, sync_mode, status)
VALUES
    ('ds_demo_hwfin_file', 'tenant_jonex_demo', 'kb_demo_hw_inet_finance', 'dam_demo_file', 'file', U&'\6587\4EF6\4E0A\4F20', '{}'::jsonb, 'manual', 'active')
ON CONFLICT (id) DO NOTHING;


INSERT INTO knowledge_base.services (id, tenant_id, space_id, name, description, domain_type, status, api_key_encrypted)
VALUES
    ('svc_demo_hw_inet_finance', 'tenant_jonex_demo', 'space_demo_test', U&'\786C\4EF6\4E92\8054\7F51\8D22\62A5\9886\57DF\670D\52A1', U&'\786C\4EF6\4E92\8054\7F51\8D22\62A5\89E3\6790\6D4B\8BD5\9886\57DF\670D\52A1', U&'\786C\4EF6\4E92\8054\7F51', 'active', 'demo-hwfin-0123456789abcdef0123456789abcdef')
ON CONFLICT (id) DO NOTHING;


INSERT INTO knowledge_base.service_knowledge_bases (id, tenant_id, service_id, kb_id)
VALUES
    ('skb_demo_hwfin', 'tenant_jonex_demo', 'svc_demo_hw_inet_finance', 'kb_demo_hw_inet_finance')
ON CONFLICT (id) DO NOTHING;


INSERT INTO knowledge_base.service_api_keys (id, tenant_id, service_id, key_prefix, key_encrypted, expires_at, is_active)
VALUES
    ('sak_hwfin_main', 'tenant_jonex_demo', 'svc_demo_hw_inet_finance', 'demo', 'demo-hwfin-0123456789abcdef0123456789abcdef', '2027-12-31'::timestamp, 1),
    ('sak_hwfin_readonly', 'tenant_jonex_demo', 'svc_demo_hw_inet_finance', 'demo', 'demo-ro-hwfin-a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6', '2026-12-31'::timestamp, 1),
    ('sak_hwfin_expired', 'tenant_jonex_demo', 'svc_demo_hw_inet_finance', 'demo', 'demo-expired-hwfin-00000000000000000000000000', '2026-01-01'::timestamp, 0)
ON CONFLICT (id) DO NOTHING;


INSERT INTO knowledge_base.ontology_template_bindings
    (tenant_id, knowledge_base_id, template_domain_id, template_scenario_id, source_type, status)
VALUES
    ('tenant_jonex_demo','kb_demo_hw_inet_finance','tpl_domain_hardware_internet','tpl_scenario_hw_inet_finance','business_template','active')
ON CONFLICT (tenant_id, knowledge_base_id) DO NOTHING;





INSERT INTO knowledge_base.ontology_compiled_schemas
    (tenant_id, knowledge_base_id, template_domain_id, template_scenario_id,
     source_type, source_version, source_hash, schema_version,
     entity_types, relation_types, constraints, disambiguation, prompt_schema,
     status, compiled_at)
VALUES (
    'tenant_jonex_demo', 'kb_demo_hw_inet_finance',
    'tpl_domain_hardware_internet', 'tpl_scenario_hw_inet_finance',
    'business_template', 3, 'd5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6', 3,
    U&'[
        {"name":"listed_company","display_name":"\4E0A\5E02\516C\53F8","aliases":["\4E0A\5E02\516C\53F8","\516C\53F8","\96C6\56E2","\53D1\884C\4EBA","Issuer"],"source_object_id":"tpl_obj_hwfin_company","attributes":[
            {"name":"stock_code","display_name":"\80A1\7968\4EE3\7801","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_co_stock"},
            {"name":"company_name","display_name":"\516C\53F8\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_co_name"},
            {"name":"exchange","display_name":"\4E0A\5E02\4EA4\6613\6240","type":"enum","required":false,"source_attribute_id":"tpl_attr_hwfin_co_exchange"},
            {"name":"industry","display_name":"\6240\5C5E\884C\4E1A","type":"enum","required":false,"source_attribute_id":"tpl_attr_hwfin_co_industry"},
            {"name":"founded_date","display_name":"\6210\7ACB\65E5\671F","type":"date","required":false,"source_attribute_id":"tpl_attr_hwfin_co_founded"},
            {"name":"chairman","display_name":"\8463\4E8B\957F","type":"string","required":false,"source_attribute_id":"tpl_attr_hwfin_co_chairman"},
            {"name":"ceo","display_name":"\9996\5E2D\6267\884C\5B98","type":"string","required":false,"source_attribute_id":"tpl_attr_hwfin_co_ceo"},
            {"name":"headquarters","display_name":"\603B\90E8","type":"string","required":false,"source_attribute_id":"tpl_attr_hwfin_co_hq"},
            {"name":"company_description","display_name":"\516C\53F8\7B80\4ECB","type":"text","required":false,"source_attribute_id":"tpl_attr_hwfin_co_desc"}
        ]},
        {"name":"financial_report","display_name":"\8D22\52A1\62A5\544A","aliases":["\8D22\52A1\62A5\544A","\8D22\62A5","\5E74\62A5","\5E74\5EA6\62A5\544A","\5B63\62A5","\4E2D\671F\62A5\544A","Annual Report"],"source_object_id":"tpl_obj_hwfin_report","attributes":[
            {"name":"report_id","display_name":"\62A5\544AID","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_rpt_id"},
            {"name":"report_type","display_name":"\62A5\544A\7C7B\578B","type":"enum","required":false,"source_attribute_id":"tpl_attr_hwfin_rpt_type"},
            {"name":"fiscal_year","display_name":"\8D22\5E74","type":"number","required":true,"source_attribute_id":"tpl_attr_hwfin_rpt_year"},
            {"name":"reporting_period","display_name":"\62A5\544A\671F","type":"string","required":false,"source_attribute_id":"tpl_attr_hwfin_rpt_period"},
            {"name":"release_date","display_name":"\53D1\5E03\65E5\671F","type":"date","required":false,"source_attribute_id":"tpl_attr_hwfin_rpt_release"},
            {"name":"currency","display_name":"\5E01\79CD","type":"string","required":false,"source_attribute_id":"tpl_attr_hwfin_rpt_currency"},
            {"name":"total_revenue","display_name":"\603B\8425\6536","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_rpt_revenue"},
            {"name":"revenue_yoy","display_name":"\8425\6536\540C\6BD4","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_rpt_rev_yoy"},
            {"name":"cost_of_sales","display_name":"\9500\552E\6210\672C","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_rpt_cogs"},
            {"name":"gross_profit","display_name":"\6BDB\5229","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_rpt_gp"},
            {"name":"gross_margin","display_name":"\6BDB\5229\7387","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_rpt_gm"},
            {"name":"selling_expense","display_name":"\9500\552E\53CA\63A8\5E7F\5F00\652F","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_rpt_selling"},
            {"name":"admin_expense","display_name":"\884C\653F\5F00\652F","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_rpt_admin"},
            {"name":"rnd_expense","display_name":"\7814\53D1\5F00\652F","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_rpt_rnd"},
            {"name":"operating_profit","display_name":"\7ECF\8425\5229\6DA6","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_rpt_op"},
            {"name":"finance_income_net","display_name":"\8D22\52A1\6536\5165\51C0\989D","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_rpt_fincome"},
            {"name":"profit_before_tax","display_name":"\9664\6240\5F97\7A0E\524D\5229\6DA6","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_rpt_pbt"},
            {"name":"income_tax_expense","display_name":"\6240\5F97\7A0E\8D39\7528","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_rpt_tax"},
            {"name":"net_profit","display_name":"\5E74\5EA6\5229\6DA6","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_rpt_np"},
            {"name":"adjusted_net_profit","display_name":"\7ECF\8C03\6574\51C0\5229\6DA6","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_rpt_anp"},
            {"name":"adjusted_net_profit_yoy","display_name":"\7ECF\8C03\6574\51C0\5229\6DA6\540C\6BD4","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_rpt_anp_yoy"}
        ]},
        {"name":"business_segment","display_name":"\4E1A\52A1\5206\90E8","aliases":["\4E1A\52A1\5206\90E8","\5206\90E8","\677F\5757","\4E1A\52A1\7EBF","Segment"],"source_object_id":"tpl_obj_hwfin_segment","attributes":[
            {"name":"segment_code","display_name":"\5206\90E8\4EE3\7801","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_seg_code"},
            {"name":"segment_name","display_name":"\5206\90E8\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_seg_name"},
            {"name":"segment_type","display_name":"\5206\90E8\7C7B\578B","type":"enum","required":false,"source_attribute_id":"tpl_attr_hwfin_seg_type"},
            {"name":"revenue","display_name":"\5206\90E8\8425\6536","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_seg_rev"},
            {"name":"revenue_yoy","display_name":"\8425\6536\540C\6BD4","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_seg_rev_yoy"},
            {"name":"revenue_ratio","display_name":"\8425\6536\5360\6BD4","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_seg_ratio"},
            {"name":"cost_of_sales","display_name":"\5206\90E8\9500\552E\6210\672C","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_seg_cogs"},
            {"name":"gross_profit","display_name":"\5206\90E8\6BDB\5229","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_seg_gp"},
            {"name":"gross_margin","display_name":"\5206\90E8\6BDB\5229\7387","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_seg_gm"},
            {"name":"operating_result","display_name":"\5206\90E8\7ECF\8425\6536\76CA","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_seg_op"},
            {"name":"adjusted_net_profit","display_name":"\7ECF\8C03\6574\51C0\5229\6DA6","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_seg_anp"},
            {"name":"adjusted_net_loss","display_name":"\7ECF\8C03\6574\51C0\4E8F\635F","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_seg_anl"},
            {"name":"segment_description","display_name":"\5206\90E8\63CF\8FF0","type":"text","required":false,"source_attribute_id":"tpl_attr_hwfin_seg_desc"}
        ]},
        {"name":"product_line","display_name":"\4EA7\54C1\7EBF","aliases":["\4EA7\54C1\7EBF","\4E1A\52A1\7C7B\522B","Product Line"],"source_object_id":"tpl_obj_hwfin_line","attributes":[
            {"name":"line_code","display_name":"\4EA7\54C1\7EBF\4EE3\7801","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_ln_code"},
            {"name":"line_name","display_name":"\4EA7\54C1\7EBF\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_ln_name"},
            {"name":"category","display_name":"\7C7B\522B","type":"enum","required":false,"source_attribute_id":"tpl_attr_hwfin_ln_cat"},
            {"name":"revenue","display_name":"\4EA7\54C1\7EBF\8425\6536","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_ln_rev"},
            {"name":"revenue_yoy","display_name":"\8425\6536\540C\6BD4","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_ln_rev_yoy"},
            {"name":"revenue_ratio","display_name":"\8425\6536\5360\6BD4","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_ln_ratio"},
            {"name":"cost_of_sales","display_name":"\4EA7\54C1\7EBF\9500\552E\6210\672C","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_ln_cogs"},
            {"name":"gross_profit","display_name":"\4EA7\54C1\7EBF\6BDB\5229","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_ln_gp"},
            {"name":"gross_margin","display_name":"\4EA7\54C1\7EBF\6BDB\5229\7387","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_ln_gm"},
            {"name":"description","display_name":"\63CF\8FF0","type":"text","required":false,"source_attribute_id":"tpl_attr_hwfin_ln_desc"}
        ]},
        {"name":"product","display_name":"\4EA7\54C1","aliases":["\4EA7\54C1","\673A\578B","\5E94\7528","\670D\52A1","\8F66\578B","Product"],"source_object_id":"tpl_obj_hwfin_product","attributes":[
            {"name":"product_code","display_name":"\4EA7\54C1\4EE3\7801","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_pd_code"},
            {"name":"product_name","display_name":"\4EA7\54C1\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_pd_name"},
            {"name":"product_category","display_name":"\4EA7\54C1\7C7B\522B","type":"enum","required":false,"source_attribute_id":"tpl_attr_hwfin_pd_cat"},
            {"name":"launch_date","display_name":"\4E0A\5E02\65E5\671F","type":"date","required":false,"source_attribute_id":"tpl_attr_hwfin_pd_launch"},
            {"name":"shipment_volume","display_name":"\51FA\8D27\91CF","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_pd_ship"},
            {"name":"shipment_yoy","display_name":"\51FA\8D27\91CF\540C\6BD4","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_pd_ship_yoy"},
            {"name":"asp","display_name":"\5E73\5747\552E\4EF7","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_pd_asp"},
            {"name":"asp_yoy","display_name":"ASP\540C\6BD4","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_pd_asp_yoy"},
            {"name":"gross_margin","display_name":"\6BDB\5229\7387","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_pd_gm"},
            {"name":"market_share","display_name":"\5E02\5360\7387","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_pd_share"},
            {"name":"product_description","display_name":"\4EA7\54C1\63CF\8FF0","type":"text","required":false,"source_attribute_id":"tpl_attr_hwfin_pd_desc"}
        ]},
        {"name":"financial_metric","display_name":"\8D22\52A1\6307\6807","aliases":["\8D22\52A1\6307\6807","\8D22\52A1\6570\636E","Financial Metric"],"source_object_id":"tpl_obj_hwfin_fin_metric","attributes":[
            {"name":"metric_code","display_name":"\6307\6807\4EE3\7801","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_fm_code"},
            {"name":"metric_name","display_name":"\6307\6807\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_fm_name"},
            {"name":"metric_value","display_name":"\6307\6807\503C","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_fm_val"},
            {"name":"metric_unit","display_name":"\5355\4F4D","type":"string","required":false,"source_attribute_id":"tpl_attr_hwfin_fm_unit"},
            {"name":"metric_yoy","display_name":"\540C\6BD4","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_fm_yoy"},
            {"name":"metric_period","display_name":"\6307\6807\671F\95F4","type":"string","required":false,"source_attribute_id":"tpl_attr_hwfin_fm_period"},
            {"name":"metric_category","display_name":"\6307\6807\5206\7C7B","type":"enum","required":false,"source_attribute_id":"tpl_attr_hwfin_fm_cat"}
        ]},
        {"name":"operational_metric","display_name":"\8FD0\8425\6307\6807","aliases":["\8FD0\8425\6307\6807","\7ECF\8425\6570\636E","Operational Metric"],"source_object_id":"tpl_obj_hwfin_op_metric","attributes":[
            {"name":"metric_code","display_name":"\6307\6807\4EE3\7801","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_om_code"},
            {"name":"metric_name","display_name":"\6307\6807\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_om_name"},
            {"name":"metric_value","display_name":"\6307\6807\503C","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_om_val"},
            {"name":"metric_unit","display_name":"\5355\4F4D","type":"string","required":false,"source_attribute_id":"tpl_attr_hwfin_om_unit"},
            {"name":"metric_yoy","display_name":"\540C\6BD4","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_om_yoy"},
            {"name":"metric_category","display_name":"\6307\6807\5206\7C7B","type":"enum","required":false,"source_attribute_id":"tpl_attr_hwfin_om_cat"},
            {"name":"region","display_name":"\7EDF\8BA1\533A\57DF","type":"string","required":false,"source_attribute_id":"tpl_attr_hwfin_om_region"},
            {"name":"metric_description","display_name":"\6307\6807\63CF\8FF0","type":"text","required":false,"source_attribute_id":"tpl_attr_hwfin_om_desc"}
        ]},
        {"name":"rnd_metric","display_name":"\7814\53D1\6307\6807","aliases":["\7814\53D1\6307\6807","\7814\53D1\6295\5165","RnD Metric"],"source_object_id":"tpl_obj_hwfin_rnd_metric","attributes":[
            {"name":"metric_code","display_name":"\6307\6807\4EE3\7801","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_rm_code"},
            {"name":"metric_name","display_name":"\6307\6807\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_rm_name"},
            {"name":"metric_value","display_name":"\6307\6807\503C","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_rm_val"},
            {"name":"metric_unit","display_name":"\5355\4F4D","type":"string","required":false,"source_attribute_id":"tpl_attr_hwfin_rm_unit"},
            {"name":"metric_yoy","display_name":"\540C\6BD4","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_rm_yoy"},
            {"name":"rnd_headcount","display_name":"\7814\53D1\4EBA\5458\6570","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_rm_head"},
            {"name":"cumulative_rnd","display_name":"\7D2F\8BA1\7814\53D1\6295\5165","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_rm_cum"}
        ]},
        {"name":"cost_expense","display_name":"\6210\672C\8D39\7528","aliases":["\6210\672C\8D39\7528","\8D39\7528","\652F\51FA","Cost Expense"],"source_object_id":"tpl_obj_hwfin_cost","attributes":[
            {"name":"expense_code","display_name":"\8D39\7528\4EE3\7801","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_ce_code"},
            {"name":"expense_name","display_name":"\8D39\7528\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_ce_name"},
            {"name":"expense_category","display_name":"\8D39\7528\5206\7C7B","type":"enum","required":false,"source_attribute_id":"tpl_attr_hwfin_ce_cat"},
            {"name":"expense_value","display_name":"\8D39\7528\91D1\989D","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_ce_val"},
            {"name":"expense_yoy","display_name":"\540C\6BD4","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_ce_yoy"},
            {"name":"expense_ratio","display_name":"\5360\8425\6536\6BD4","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_ce_ratio"},
            {"name":"expense_period","display_name":"\8D39\7528\671F\95F4","type":"string","required":false,"source_attribute_id":"tpl_attr_hwfin_ce_period"}
        ]},
        {"name":"shareholder_return","display_name":"\80A1\4E1C\56DE\62A5","aliases":["\80A1\4E1C\56DE\62A5","\80A1\606F","\5206\7EA2","\914D\552E","\56DE\8D2D","Shareholder Return"],"source_object_id":"tpl_obj_hwfin_shareholder","attributes":[
            {"name":"return_code","display_name":"\4E8B\9879\4EE3\7801","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_sr_code"},
            {"name":"return_type","display_name":"\4E8B\9879\7C7B\578B","type":"enum","required":true,"source_attribute_id":"tpl_attr_hwfin_sr_type"},
            {"name":"return_description","display_name":"\4E8B\9879\63CF\8FF0","type":"string","required":false,"source_attribute_id":"tpl_attr_hwfin_sr_desc"},
            {"name":"return_amount","display_name":"\91D1\989D/\89C4\6A21","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_sr_amount"},
            {"name":"per_share_price","display_name":"\6BCF\80A1\4EF7\683C","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_sr_price"},
            {"name":"return_date","display_name":"\4E8B\9879\65E5\671F","type":"date","required":false,"source_attribute_id":"tpl_attr_hwfin_sr_date"},
            {"name":"return_status","display_name":"\4E8B\9879\72B6\6001","type":"enum","required":false,"source_attribute_id":"tpl_attr_hwfin_sr_status"}
        ]},
        {"name":"esg_metric","display_name":"ESG\6307\6807","aliases":["ESG\6307\6807","ESG","\73AF\5883\793E\4F1A\7BA1\6CBB","ESG Metric"],"source_object_id":"tpl_obj_hwfin_esg","attributes":[
            {"name":"metric_code","display_name":"\6307\6807\4EE3\7801","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_eg_code"},
            {"name":"metric_name","display_name":"\6307\6807\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_eg_name"},
            {"name":"metric_category","display_name":"\6307\6807\5206\7C7B","type":"enum","required":false,"source_attribute_id":"tpl_attr_hwfin_eg_cat"},
            {"name":"metric_value","display_name":"\6307\6807\503C","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_eg_val"},
            {"name":"metric_unit","display_name":"\5355\4F4D","type":"string","required":false,"source_attribute_id":"tpl_attr_hwfin_eg_unit"},
            {"name":"metric_yoy","display_name":"\540C\6BD4","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_eg_yoy"},
            {"name":"metric_description","display_name":"\6307\6807\63CF\8FF0","type":"text","required":false,"source_attribute_id":"tpl_attr_hwfin_eg_desc"}
        ]},
        {"name":"key_person","display_name":"\5173\952E\4EBA\5458","aliases":["\5173\952E\4EBA\5458","\9AD8\7BA1","\7BA1\7406\5C42","\8463\4E8B","Key Person"],"source_object_id":"tpl_obj_hwfin_person","attributes":[
            {"name":"person_name","display_name":"\59D3\540D","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_kp_name"},
            {"name":"title","display_name":"\804C\4F4D","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_kp_title"},
            {"name":"role","display_name":"\89D2\8272","type":"enum","required":false,"source_attribute_id":"tpl_attr_hwfin_kp_role"},
            {"name":"director_type","display_name":"\8463\4E8B\7C7B\578B","type":"enum","required":false,"source_attribute_id":"tpl_attr_hwfin_kp_type"},
            {"name":"affiliated_company","display_name":"\6240\5C5E\516C\53F8","type":"string","required":false,"source_attribute_id":"tpl_attr_hwfin_kp_co"}
        ]},
        {"name":"business_event","display_name":"\4E1A\52A1\4E8B\4EF6","aliases":["\4E1A\52A1\4E8B\4EF6","\4E8B\4EF6","\91CC\7A0B\7891","Business Event"],"source_object_id":"tpl_obj_hwfin_event","attributes":[
            {"name":"event_name","display_name":"\4E8B\4EF6\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_ev_name"},
            {"name":"event_type","display_name":"\4E8B\4EF6\7C7B\578B","type":"enum","required":false,"source_attribute_id":"tpl_attr_hwfin_ev_type"},
            {"name":"event_date","display_name":"\4E8B\4EF6\65E5\671F","type":"date","required":false,"source_attribute_id":"tpl_attr_hwfin_ev_date"},
            {"name":"event_description","display_name":"\4E8B\4EF6\63CF\8FF0","type":"text","required":false,"source_attribute_id":"tpl_attr_hwfin_ev_desc"}
        ]},
        {"name":"geographic_market","display_name":"\5730\533A\5E02\573A","aliases":["\5730\533A\5E02\573A","\5E02\573A","\533A\57DF","\5730\533A","Region","Market"],"source_object_id":"tpl_obj_hwfin_market","attributes":[
            {"name":"market_name","display_name":"\5E02\573A\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_mk_name"},
            {"name":"region_type","display_name":"\533A\57DF\7C7B\578B","type":"enum","required":false,"source_attribute_id":"tpl_attr_hwfin_mk_type"},
            {"name":"revenue","display_name":"\5730\533A\8425\6536","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_mk_rev"},
            {"name":"revenue_ratio","display_name":"\8425\6536\5360\6BD4","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_mk_ratio"},
            {"name":"store_count","display_name":"\95E8\5E97\6570","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_mk_store"},
            {"name":"market_description","display_name":"\5E02\573A\63CF\8FF0","type":"text","required":false,"source_attribute_id":"tpl_attr_hwfin_mk_desc"}
        ]},
        {"name":"sales_channel","display_name":"\9500\552E\6E20\9053","aliases":["\9500\552E\6E20\9053","\6E20\9053","\95E8\5E97","\96F6\552E\7F51\7EDC","Channel"],"source_object_id":"tpl_obj_hwfin_channel","attributes":[
            {"name":"channel_name","display_name":"\6E20\9053\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_ch_name"},
            {"name":"channel_type","display_name":"\6E20\9053\7C7B\578B","type":"enum","required":false,"source_attribute_id":"tpl_attr_hwfin_ch_type"},
            {"name":"store_count","display_name":"\95E8\5E97\6570","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_ch_store"},
            {"name":"region","display_name":"\8986\76D6\5730\533A","type":"string","required":false,"source_attribute_id":"tpl_attr_hwfin_ch_region"},
            {"name":"channel_description","display_name":"\6E20\9053\63CF\8FF0","type":"text","required":false,"source_attribute_id":"tpl_attr_hwfin_ch_desc"}
        ]},
        {"name":"subsidiary","display_name":"\5B50\516C\53F8","aliases":["\5B50\516C\53F8","\9644\5C5E\516C\53F8","\96C6\56E2\5B9E\4F53","Subsidiary"],"source_object_id":"tpl_obj_hwfin_subsidiary","attributes":[
            {"name":"subsidiary_name","display_name":"\5B50\516C\53F8\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_sub_name"},
            {"name":"location","display_name":"\6240\5728\5730","type":"string","required":false,"source_attribute_id":"tpl_attr_hwfin_sub_loc"},
            {"name":"ownership","display_name":"\6301\80A1\6BD4\4F8B","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_sub_own"},
            {"name":"business_scope","display_name":"\7ECF\8425\8303\56F4","type":"string","required":false,"source_attribute_id":"tpl_attr_hwfin_sub_scope"},
            {"name":"subsidiary_description","display_name":"\5B50\516C\53F8\63CF\8FF0","type":"text","required":false,"source_attribute_id":"tpl_attr_hwfin_sub_desc"}
        ]},
        {"name":"risk_factor","display_name":"\98CE\9669\56E0\7D20","aliases":["\98CE\9669\56E0\7D20","\98CE\9669","Risk Factor"],"source_object_id":"tpl_obj_hwfin_risk","attributes":[
            {"name":"risk_name","display_name":"\98CE\9669\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_rk_name"},
            {"name":"risk_category","display_name":"\98CE\9669\7C7B\522B","type":"enum","required":false,"source_attribute_id":"tpl_attr_hwfin_rk_cat"},
            {"name":"risk_description","display_name":"\98CE\9669\63CF\8FF0","type":"text","required":false,"source_attribute_id":"tpl_attr_hwfin_rk_desc"},
            {"name":"mitigation","display_name":"\5E94\5BF9\63AA\65BD","type":"text","required":false,"source_attribute_id":"tpl_attr_hwfin_rk_mit"}
        ]},
        {"name":"legal_proceeding","display_name":"\6CD5\5F8B\8BC9\8BBC","aliases":["\6CD5\5F8B\8BC9\8BBC","\8BC9\8BBC","\76D1\7BA1\8C03\67E5","\6216\7136\8D1F\503A","Legal Proceeding"],"source_object_id":"tpl_obj_hwfin_legal","attributes":[
            {"name":"case_name","display_name":"\6848\4EF6\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_lg_name"},
            {"name":"jurisdiction","display_name":"\53F8\6CD5\7BA1\8F96","type":"string","required":false,"source_attribute_id":"tpl_attr_hwfin_lg_juris"},
            {"name":"status","display_name":"\6848\4EF6\72B6\6001","type":"enum","required":false,"source_attribute_id":"tpl_attr_hwfin_lg_status"},
            {"name":"amount_involved","display_name":"\6D89\53CA\91D1\989D","type":"number","required":false,"source_attribute_id":"tpl_attr_hwfin_lg_amount"},
            {"name":"case_description","display_name":"\6848\4EF6\63CF\8FF0","type":"text","required":false,"source_attribute_id":"tpl_attr_hwfin_lg_desc"}
        ]},
        {"name":"sustainability_initiative","display_name":"\53EF\6301\7EED\4E3E\63AA","aliases":["\53EF\6301\7EED\4E3E\63AA","ESG\4E3E\63AA","\53EF\6301\7EED\53D1\5C55","Sustainability Initiative"],"source_object_id":"tpl_obj_hwfin_esginit","attributes":[
            {"name":"initiative_name","display_name":"\4E3E\63AA\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_hwfin_si_name"},
            {"name":"esg_pillar","display_name":"ESG\652F\67F1","type":"enum","required":false,"source_attribute_id":"tpl_attr_hwfin_si_pillar"},
            {"name":"target","display_name":"\76EE\6807","type":"string","required":false,"source_attribute_id":"tpl_attr_hwfin_si_target"},
            {"name":"progress","display_name":"\8FDB\5C55","type":"string","required":false,"source_attribute_id":"tpl_attr_hwfin_si_progress"},
            {"name":"initiative_description","display_name":"\4E3E\63AA\63CF\8FF0","type":"text","required":false,"source_attribute_id":"tpl_attr_hwfin_si_desc"}
        ]}
    ]'::jsonb,
    U&'[
        {"name":"ISSUES_REPORT","display_name":"\53D1\5E03\62A5\544A","aliases":["\53D1\5E03\62A5\544A","\62AB\9732","\51FA\5177"],"source":"listed_company","target":"financial_report","source_relation_id":"tpl_rel_hwfin_issues","cardinality":"one_to_many"},
        {"name":"HAS_SEGMENT","display_name":"\5305\542B\5206\90E8","aliases":["\5305\542B\5206\90E8","\6DB5\76D6\5206\90E8"],"source":"financial_report","target":"business_segment","source_relation_id":"tpl_rel_hwfin_has_seg","cardinality":"one_to_many"},
        {"name":"SEGMENT_INCLUDES_LINE","display_name":"\5206\90E8\542B\4EA7\54C1\7EBF","aliases":["\5305\542B\4EA7\54C1\7EBF","\4E0B\8BBE\4EA7\54C1\7EBF"],"source":"business_segment","target":"product_line","source_relation_id":"tpl_rel_hwfin_seg_line","cardinality":"one_to_many"},
        {"name":"LINE_PRODUCES_PRODUCT","display_name":"\4EA7\54C1\7EBF\4EA7\51FA\4EA7\54C1","aliases":["\4EA7\51FA","\751F\4EA7","\5305\542B\4EA7\54C1"],"source":"product_line","target":"product","source_relation_id":"tpl_rel_hwfin_line_prod","cardinality":"one_to_many"},
        {"name":"REPORT_HAS_FINANCIAL_METRIC","display_name":"\62A5\544A\8D22\52A1\6307\6807","aliases":["\62AB\9732\6307\6807","\542B\6307\6807"],"source":"financial_report","target":"financial_metric","source_relation_id":"tpl_rel_hwfin_rpt_fm","cardinality":"one_to_many"},
        {"name":"SEGMENT_HAS_METRIC","display_name":"\5206\90E8\8D22\52A1\6307\6807","aliases":["\5206\90E8\6307\6807"],"source":"business_segment","target":"financial_metric","source_relation_id":"tpl_rel_hwfin_seg_fm","cardinality":"one_to_many"},
        {"name":"PRODUCT_HAS_OPERATIONAL_METRIC","display_name":"\4EA7\54C1\8FD0\8425\6307\6807","aliases":["\4EA7\54C1\6307\6807"],"source":"product","target":"operational_metric","source_relation_id":"tpl_rel_hwfin_pd_om","cardinality":"one_to_many"},
        {"name":"COMPANY_HAS_KEYPERSON","display_name":"\5173\952E\4EBA\5458","aliases":["\9AD8\7BA1","\7BA1\7406\5C42"],"source":"listed_company","target":"key_person","source_relation_id":"tpl_rel_hwfin_co_kp","cardinality":"one_to_many"},
        {"name":"PARTICIPATES_EVENT","display_name":"\53C2\4E0E\4E8B\4EF6","aliases":["\53C2\4E0E","\62AB\9732\4E8B\4EF6"],"source":"listed_company","target":"business_event","source_relation_id":"tpl_rel_hwfin_co_ev","cardinality":"many_to_many"},
        {"name":"COMPANY_HAS_RND_METRIC","display_name":"\7814\53D1\6307\6807","aliases":["\7814\53D1\6295\5165"],"source":"listed_company","target":"rnd_metric","source_relation_id":"tpl_rel_hwfin_co_rm","cardinality":"one_to_many"},
        {"name":"COMPANY_HAS_OPERATIONAL_METRIC","display_name":"\516C\53F8\8FD0\8425\6307\6807","aliases":["\8FD0\8425\6307\6807"],"source":"listed_company","target":"operational_metric","source_relation_id":"tpl_rel_hwfin_co_om","cardinality":"one_to_many"},
        {"name":"LINE_HAS_METRIC","display_name":"\4EA7\54C1\7EBF\8D22\52A1\6307\6807","aliases":["\4EA7\54C1\7EBF\6307\6807"],"source":"product_line","target":"financial_metric","source_relation_id":"tpl_rel_hwfin_ln_fm","cardinality":"one_to_many"},
        {"name":"REPORT_HAS_COST_EXPENSE","display_name":"\62A5\544A\6210\672C\8D39\7528","aliases":["\542B\8D39\7528","\62AB\9732\8D39\7528"],"source":"financial_report","target":"cost_expense","source_relation_id":"tpl_rel_hwfin_rpt_ce","cardinality":"one_to_many"},
        {"name":"SEGMENT_HAS_COST_EXPENSE","display_name":"\5206\90E8\6210\672C\8D39\7528","aliases":["\5206\90E8\8D39\7528"],"source":"business_segment","target":"cost_expense","source_relation_id":"tpl_rel_hwfin_seg_ce","cardinality":"one_to_many"},
        {"name":"COMPANY_HAS_SHAREHOLDER_RETURN","display_name":"\80A1\4E1C\56DE\62A5","aliases":["\80A1\606F","\914D\552E","\56DE\8D2D"],"source":"listed_company","target":"shareholder_return","source_relation_id":"tpl_rel_hwfin_co_sr","cardinality":"one_to_many"},
        {"name":"COMPANY_HAS_ESG_METRIC","display_name":"ESG\6307\6807","aliases":["ESG","\73AF\5883\793E\4F1A\7BA1\6CBB"],"source":"listed_company","target":"esg_metric","source_relation_id":"tpl_rel_hwfin_co_eg","cardinality":"one_to_many"},
        {"name":"COMPANY_OPERATES_IN_MARKET","display_name":"\5730\533A\7ECF\8425","aliases":["\5730\533A\7ECF\8425","\5206\5730\533A","\5E02\573A\5E03\5C40"],"source":"listed_company","target":"geographic_market","source_relation_id":"tpl_rel_hwfin_co_mkt","cardinality":"one_to_many"},
        {"name":"SEGMENT_SELLS_IN_MARKET","display_name":"\5206\5730\533A\8425\6536","aliases":["\5206\5730\533A\8425\6536","\5730\533A\6536\5165"],"source":"business_segment","target":"geographic_market","source_relation_id":"tpl_rel_hwfin_seg_mkt","cardinality":"many_to_many"},
        {"name":"COMPANY_USES_CHANNEL","display_name":"\9500\552E\6E20\9053","aliases":["\9500\552E\6E20\9053","\6E20\9053\5E03\5C40"],"source":"listed_company","target":"sales_channel","source_relation_id":"tpl_rel_hwfin_co_ch","cardinality":"one_to_many"},
        {"name":"CHANNEL_COVERS_MARKET","display_name":"\6E20\9053\8986\76D6","aliases":["\6E20\9053\8986\76D6","\6E20\9053\5206\5E03"],"source":"sales_channel","target":"geographic_market","source_relation_id":"tpl_rel_hwfin_ch_mkt","cardinality":"many_to_many"},
        {"name":"COMPANY_HAS_SUBSIDIARY","display_name":"\5B50\516C\53F8","aliases":["\5B50\516C\53F8","\9644\5C5E\516C\53F8"],"source":"listed_company","target":"subsidiary","source_relation_id":"tpl_rel_hwfin_co_sub","cardinality":"one_to_many"},
        {"name":"SUBSIDIARY_LOCATED_IN_MARKET","display_name":"\5B50\516C\53F8\6240\5728\5730","aliases":["\6240\5728\5730","\6CE8\518C\5730"],"source":"subsidiary","target":"geographic_market","source_relation_id":"tpl_rel_hwfin_sub_mkt","cardinality":"many_to_one"},
        {"name":"COMPANY_FACES_RISK","display_name":"\9762\4E34\98CE\9669","aliases":["\9762\4E34\98CE\9669","\98CE\9669\62AB\9732"],"source":"listed_company","target":"risk_factor","source_relation_id":"tpl_rel_hwfin_co_risk","cardinality":"one_to_many"},
        {"name":"SUBSIDIARY_INVOLVED_IN_PROCEEDING","display_name":"\6D89\53CA\8BC9\8BBC","aliases":["\6D89\53CA\8BC9\8BBC","\6D89\8BC9"],"source":"subsidiary","target":"legal_proceeding","source_relation_id":"tpl_rel_hwfin_sub_lg","cardinality":"one_to_many"},
        {"name":"COMPANY_UNDERTAKES_INITIATIVE","display_name":"\5F00\5C55\4E3E\63AA","aliases":["\5F00\5C55\4E3E\63AA","\53EF\6301\7EED\884C\52A8"],"source":"listed_company","target":"sustainability_initiative","source_relation_id":"tpl_rel_hwfin_co_si","cardinality":"one_to_many"},
        {"name":"INITIATIVE_IMPROVES_ESG","display_name":"\6539\5584\6307\6807","aliases":["\6539\5584\6307\6807","\652F\6491ESG"],"source":"sustainability_initiative","target":"esg_metric","source_relation_id":"tpl_rel_hwfin_si_esg","cardinality":"many_to_many"}
    ]'::jsonb,
    U&'[
        {"type":"entity","severity":"warning"},
        {"type":"relation","severity":"warning","rule":"relation_source_target_must_exist"},
        {"type":"value","severity":"warning","rule":"currency_unit_consistency","fields":["total_revenue","gross_profit","operating_profit","net_profit","adjusted_net_profit","rnd_expense","cost_of_sales","selling_expense","admin_expense","income_tax_expense"],"expected_unit":"\4E07\5143"}
    ]'::jsonb,
    U&'{"case_insensitive":true,"alias_merge":true,"currency_normalization":"CNY","unit_million":true,"segment_aliases":{"\624B\673A×AIoT":["\624B\673A×AIoT","\624B\673AxAIoT","\624B\673A AIoT","\624B\673AAIoT"],"\667A\80FD\7535\52A8\6C7D\8F66\53CAAI\7B49\521B\65B0\4E1A\52A1":["\667A\80FD\7535\52A8\6C7D\8F66\53CAAI\7B49\521B\65B0\4E1A\52A1","\667A\80FD\7535\52A8\6C7D\8F66","\6C7D\8F66\4E1A\52A1","EV\4E1A\52A1"]}}'::jsonb,
    U&'{
        "entity_types":[
            {"name":"listed_company","aliases":["\4E0A\5E02\516C\53F8","\516C\53F8","\96C6\56E2","\53D1\884C\4EBA"],"attributes":[
                {"name":"stock_code","type":"string","required":true},
                {"name":"company_name","type":"string","required":true},
                {"name":"exchange","type":"enum","required":false},
                {"name":"industry","type":"enum","required":false},
                {"name":"founded_date","type":"date","required":false},
                {"name":"chairman","type":"string","required":false},
                {"name":"ceo","type":"string","required":false},
                {"name":"headquarters","type":"string","required":false},
                {"name":"company_description","type":"text","required":false}
            ]},
            {"name":"financial_report","aliases":["\8D22\52A1\62A5\544A","\8D22\62A5","\5E74\62A5","\5E74\5EA6\62A5\544A","\5B63\62A5"],"attributes":[
                {"name":"report_id","type":"string","required":true},
                {"name":"report_type","type":"enum","required":false},
                {"name":"fiscal_year","type":"number","required":true},
                {"name":"reporting_period","type":"string","required":false},
                {"name":"release_date","type":"date","required":false},
                {"name":"currency","type":"string","required":false},
                {"name":"total_revenue","type":"number","required":false},
                {"name":"revenue_yoy","type":"number","required":false},
                {"name":"cost_of_sales","type":"number","required":false},
                {"name":"gross_profit","type":"number","required":false},
                {"name":"gross_margin","type":"number","required":false},
                {"name":"selling_expense","type":"number","required":false},
                {"name":"admin_expense","type":"number","required":false},
                {"name":"rnd_expense","type":"number","required":false},
                {"name":"operating_profit","type":"number","required":false},
                {"name":"finance_income_net","type":"number","required":false},
                {"name":"profit_before_tax","type":"number","required":false},
                {"name":"income_tax_expense","type":"number","required":false},
                {"name":"net_profit","type":"number","required":false},
                {"name":"adjusted_net_profit","type":"number","required":false},
                {"name":"adjusted_net_profit_yoy","type":"number","required":false}
            ]},
            {"name":"business_segment","aliases":["\4E1A\52A1\5206\90E8","\5206\90E8","\677F\5757","\4E1A\52A1\7EBF"],"attributes":[
                {"name":"segment_code","type":"string","required":true},
                {"name":"segment_name","type":"string","required":true},
                {"name":"segment_type","type":"enum","required":false},
                {"name":"revenue","type":"number","required":false},
                {"name":"revenue_yoy","type":"number","required":false},
                {"name":"revenue_ratio","type":"number","required":false},
                {"name":"cost_of_sales","type":"number","required":false},
                {"name":"gross_profit","type":"number","required":false},
                {"name":"gross_margin","type":"number","required":false},
                {"name":"operating_result","type":"number","required":false},
                {"name":"adjusted_net_profit","type":"number","required":false},
                {"name":"adjusted_net_loss","type":"number","required":false},
                {"name":"segment_description","type":"text","required":false}
            ]},
            {"name":"product_line","aliases":["\4EA7\54C1\7EBF","\4E1A\52A1\7C7B\522B"],"attributes":[
                {"name":"line_code","type":"string","required":true},
                {"name":"line_name","type":"string","required":true},
                {"name":"category","type":"enum","required":false},
                {"name":"revenue","type":"number","required":false},
                {"name":"revenue_yoy","type":"number","required":false},
                {"name":"revenue_ratio","type":"number","required":false},
                {"name":"cost_of_sales","type":"number","required":false},
                {"name":"gross_profit","type":"number","required":false},
                {"name":"gross_margin","type":"number","required":false},
                {"name":"description","type":"text","required":false}
            ]},
            {"name":"product","aliases":["\4EA7\54C1","\673A\578B","\5E94\7528","\670D\52A1","\8F66\578B"],"attributes":[
                {"name":"product_code","type":"string","required":true},
                {"name":"product_name","type":"string","required":true},
                {"name":"product_category","type":"enum","required":false},
                {"name":"launch_date","type":"date","required":false},
                {"name":"shipment_volume","type":"number","required":false},
                {"name":"shipment_yoy","type":"number","required":false},
                {"name":"asp","type":"number","required":false},
                {"name":"asp_yoy","type":"number","required":false},
                {"name":"gross_margin","type":"number","required":false},
                {"name":"market_share","type":"number","required":false},
                {"name":"product_description","type":"text","required":false}
            ]},
            {"name":"financial_metric","aliases":["\8D22\52A1\6307\6807","\8D22\52A1\6570\636E"],"attributes":[
                {"name":"metric_code","type":"string","required":true},
                {"name":"metric_name","type":"string","required":true},
                {"name":"metric_value","type":"number","required":false},
                {"name":"metric_unit","type":"string","required":false},
                {"name":"metric_yoy","type":"number","required":false},
                {"name":"metric_period","type":"string","required":false},
                {"name":"metric_category","type":"enum","required":false}
            ]},
            {"name":"operational_metric","aliases":["\8FD0\8425\6307\6807","\7ECF\8425\6570\636E"],"attributes":[
                {"name":"metric_code","type":"string","required":true},
                {"name":"metric_name","type":"string","required":true},
                {"name":"metric_value","type":"number","required":false},
                {"name":"metric_unit","type":"string","required":false},
                {"name":"metric_yoy","type":"number","required":false},
                {"name":"metric_category","type":"enum","required":false},
                {"name":"region","type":"string","required":false},
                {"name":"metric_description","type":"text","required":false}
            ]},
            {"name":"rnd_metric","aliases":["\7814\53D1\6307\6807","\7814\53D1\6295\5165"],"attributes":[
                {"name":"metric_code","type":"string","required":true},
                {"name":"metric_name","type":"string","required":true},
                {"name":"metric_value","type":"number","required":false},
                {"name":"metric_unit","type":"string","required":false},
                {"name":"metric_yoy","type":"number","required":false},
                {"name":"rnd_headcount","type":"number","required":false},
                {"name":"cumulative_rnd","type":"number","required":false}
            ]},
            {"name":"cost_expense","aliases":["\6210\672C\8D39\7528","\8D39\7528","\652F\51FA"],"attributes":[
                {"name":"expense_code","type":"string","required":true},
                {"name":"expense_name","type":"string","required":true},
                {"name":"expense_category","type":"enum","required":false},
                {"name":"expense_value","type":"number","required":false},
                {"name":"expense_yoy","type":"number","required":false},
                {"name":"expense_ratio","type":"number","required":false},
                {"name":"expense_period","type":"string","required":false}
            ]},
            {"name":"shareholder_return","aliases":["\80A1\4E1C\56DE\62A5","\80A1\606F","\5206\7EA2","\914D\552E","\56DE\8D2D"],"attributes":[
                {"name":"return_code","type":"string","required":true},
                {"name":"return_type","type":"enum","required":true},
                {"name":"return_description","type":"string","required":false},
                {"name":"return_amount","type":"number","required":false},
                {"name":"per_share_price","type":"number","required":false},
                {"name":"return_date","type":"date","required":false},
                {"name":"return_status","type":"enum","required":false}
            ]},
            {"name":"esg_metric","aliases":["ESG\6307\6807","ESG","\73AF\5883\793E\4F1A\7BA1\6CBB"],"attributes":[
                {"name":"metric_code","type":"string","required":true},
                {"name":"metric_name","type":"string","required":true},
                {"name":"metric_category","type":"enum","required":false},
                {"name":"metric_value","type":"number","required":false},
                {"name":"metric_unit","type":"string","required":false},
                {"name":"metric_yoy","type":"number","required":false},
                {"name":"metric_description","type":"text","required":false}
            ]},
            {"name":"key_person","aliases":["\5173\952E\4EBA\5458","\9AD8\7BA1","\7BA1\7406\5C42","\8463\4E8B"],"attributes":[
                {"name":"person_name","type":"string","required":true},
                {"name":"title","type":"string","required":true},
                {"name":"role","type":"enum","required":false},
                {"name":"director_type","type":"enum","required":false},
                {"name":"affiliated_company","type":"string","required":false}
            ]},
            {"name":"business_event","aliases":["\4E1A\52A1\4E8B\4EF6","\4E8B\4EF6","\91CC\7A0B\7891"],"attributes":[
                {"name":"event_name","type":"string","required":true},
                {"name":"event_type","type":"enum","required":false},
                {"name":"event_date","type":"date","required":false},
                {"name":"event_description","type":"text","required":false}
            ]},
            {"name":"geographic_market","aliases":["\5730\533A\5E02\573A","\5E02\573A","\533A\57DF","\5730\533A"],"attributes":[
                {"name":"market_name","type":"string","required":true},
                {"name":"region_type","type":"enum","required":false},
                {"name":"revenue","type":"number","required":false},
                {"name":"revenue_ratio","type":"number","required":false},
                {"name":"store_count","type":"number","required":false},
                {"name":"market_description","type":"text","required":false}
            ]},
            {"name":"sales_channel","aliases":["\9500\552E\6E20\9053","\6E20\9053","\95E8\5E97","\96F6\552E\7F51\7EDC"],"attributes":[
                {"name":"channel_name","type":"string","required":true},
                {"name":"channel_type","type":"enum","required":false},
                {"name":"store_count","type":"number","required":false},
                {"name":"region","type":"string","required":false},
                {"name":"channel_description","type":"text","required":false}
            ]},
            {"name":"subsidiary","aliases":["\5B50\516C\53F8","\9644\5C5E\516C\53F8","\96C6\56E2\5B9E\4F53"],"attributes":[
                {"name":"subsidiary_name","type":"string","required":true},
                {"name":"location","type":"string","required":false},
                {"name":"ownership","type":"number","required":false},
                {"name":"business_scope","type":"string","required":false},
                {"name":"subsidiary_description","type":"text","required":false}
            ]},
            {"name":"risk_factor","aliases":["\98CE\9669\56E0\7D20","\98CE\9669"],"attributes":[
                {"name":"risk_name","type":"string","required":true},
                {"name":"risk_category","type":"enum","required":false},
                {"name":"risk_description","type":"text","required":false},
                {"name":"mitigation","type":"text","required":false}
            ]},
            {"name":"legal_proceeding","aliases":["\6CD5\5F8B\8BC9\8BBC","\8BC9\8BBC","\76D1\7BA1\8C03\67E5","\6216\7136\8D1F\503A"],"attributes":[
                {"name":"case_name","type":"string","required":true},
                {"name":"jurisdiction","type":"string","required":false},
                {"name":"status","type":"enum","required":false},
                {"name":"amount_involved","type":"number","required":false},
                {"name":"case_description","type":"text","required":false}
            ]},
            {"name":"sustainability_initiative","aliases":["\53EF\6301\7EED\4E3E\63AA","ESG\4E3E\63AA","\53EF\6301\7EED\53D1\5C55"],"attributes":[
                {"name":"initiative_name","type":"string","required":true},
                {"name":"esg_pillar","type":"enum","required":false},
                {"name":"target","type":"string","required":false},
                {"name":"progress","type":"string","required":false},
                {"name":"initiative_description","type":"text","required":false}
            ]}
        ],
        "relation_types":[
            {"name":"ISSUES_REPORT","source":"listed_company","target":"financial_report"},
            {"name":"HAS_SEGMENT","source":"financial_report","target":"business_segment"},
            {"name":"SEGMENT_INCLUDES_LINE","source":"business_segment","target":"product_line"},
            {"name":"LINE_PRODUCES_PRODUCT","source":"product_line","target":"product"},
            {"name":"REPORT_HAS_FINANCIAL_METRIC","source":"financial_report","target":"financial_metric"},
            {"name":"SEGMENT_HAS_METRIC","source":"business_segment","target":"financial_metric"},
            {"name":"PRODUCT_HAS_OPERATIONAL_METRIC","source":"product","target":"operational_metric"},
            {"name":"COMPANY_HAS_KEYPERSON","source":"listed_company","target":"key_person"},
            {"name":"PARTICIPATES_EVENT","source":"listed_company","target":"business_event"},
            {"name":"COMPANY_HAS_RND_METRIC","source":"listed_company","target":"rnd_metric"},
            {"name":"COMPANY_HAS_OPERATIONAL_METRIC","source":"listed_company","target":"operational_metric"},
            {"name":"LINE_HAS_METRIC","source":"product_line","target":"financial_metric"},
            {"name":"REPORT_HAS_COST_EXPENSE","source":"financial_report","target":"cost_expense"},
            {"name":"SEGMENT_HAS_COST_EXPENSE","source":"business_segment","target":"cost_expense"},
            {"name":"COMPANY_HAS_SHAREHOLDER_RETURN","source":"listed_company","target":"shareholder_return"},
            {"name":"COMPANY_HAS_ESG_METRIC","source":"listed_company","target":"esg_metric"},
            {"name":"COMPANY_OPERATES_IN_MARKET","source":"listed_company","target":"geographic_market"},
            {"name":"SEGMENT_SELLS_IN_MARKET","source":"business_segment","target":"geographic_market"},
            {"name":"COMPANY_USES_CHANNEL","source":"listed_company","target":"sales_channel"},
            {"name":"CHANNEL_COVERS_MARKET","source":"sales_channel","target":"geographic_market"},
            {"name":"COMPANY_HAS_SUBSIDIARY","source":"listed_company","target":"subsidiary"},
            {"name":"SUBSIDIARY_LOCATED_IN_MARKET","source":"subsidiary","target":"geographic_market"},
            {"name":"COMPANY_FACES_RISK","source":"listed_company","target":"risk_factor"},
            {"name":"SUBSIDIARY_INVOLVED_IN_PROCEEDING","source":"subsidiary","target":"legal_proceeding"},
            {"name":"COMPANY_UNDERTAKES_INITIATIVE","source":"listed_company","target":"sustainability_initiative"},
            {"name":"INITIATIVE_IMPROVES_ESG","source":"sustainability_initiative","target":"esg_metric"}
        ]
    }'::jsonb,
    'active', '2026-06-24T00:00:00+00'::timestamptz
) ON CONFLICT (tenant_id, knowledge_base_id) DO NOTHING;











INSERT INTO business_domain.template_domains (id, tenant_id, name, description, status, version, published_at, structure_hash)
VALUES ('tpl_domain_ai_tech_report', 'tenant_jonex_demo', U&'AI\5927\6A21\578B\6280\672F\62A5\544A', U&'AI\5927\6A21\578B\6280\672F\62A5\544A\7ED3\6784\5316\62BD\53D6\4E0E\5206\6790\6A21\677F\9886\57DF', 'active', 2,
        '2026-06-24T00:00:00+00'::timestamptz,
        'c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5')
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_domain.template_scenarios (id, tenant_id, domain_id, name, description, config_json, version, published_at, structure_hash)
VALUES ('tpl_scenario_llm_tech_report', 'tenant_jonex_demo', 'tpl_domain_ai_tech_report', U&'LLM\6280\672F\62A5\544A', U&'\5927\8BED\8A00\6A21\578B\6280\672F\62A5\544A\7ED3\6784\5316\62BD\53D6\573A\666F（\57FA\4E8E\5C0F\7C73MiMo-V2-Flash\6280\672F\62A5\544A）', '{}'::jsonb, 2,
        '2026-06-24T00:00:00+00'::timestamptz,
        'c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5')
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_domain.template_objects (id, tenant_id, domain_id, scenario_id, name, description, status, ontology_code, aliases)
VALUES
 ('tpl_obj_llm_model','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'AI\6A21\578B',U&'\5927\8BED\8A00\6A21\578B\672C\4F53（\5982 MiMo-V2-Flash）','active','ai_model',U&'["AI\6A21\578B","\5927\6A21\578B","\8BED\8A00\6A21\578B","LLM","Model"]'::jsonb),
 ('tpl_obj_llm_arch','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\6A21\578B\67B6\6784',U&'\6A21\578B\67B6\6784\7279\6027（\6DF7\5408\6CE8\610F\529B、MTP\7B49）','active','model_architecture',U&'["\6A21\578B\67B6\6784","\67B6\6784","Architecture"]'::jsonb),
 ('tpl_obj_llm_train','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\8BAD\7EC3\914D\7F6E',U&'\9884\8BAD\7EC3\9636\6BB5\914D\7F6E（token\6570、\7CBE\5EA6、\5E8F\5217\957F\5EA6）','active','training_config',U&'["\8BAD\7EC3\914D\7F6E","\9884\8BAD\7EC3","Training"]'::jsonb),
 ('tpl_obj_llm_bench','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\57FA\51C6\6D4B\8BD5',U&'\8BC4\6D4B\57FA\51C6\5B9A\4E49（\5982 MMLU-Pro、SWE-Bench）','active','benchmark',U&'["\57FA\51C6\6D4B\8BD5","\8BC4\6D4B\57FA\51C6","Benchmark"]'::jsonb),
 ('tpl_obj_llm_result','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\8BC4\6D4B\7ED3\679C',U&'\6A21\578B\5728\57FA\51C6\4E0A\7684\5177\4F53\5F97\5206','active','benchmark_result',U&'["\8BC4\6D4B\7ED3\679C","\5F97\5206","Result","Score"]'::jsonb),
 ('tpl_obj_llm_comp','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\7ADE\54C1\6A21\578B',U&'\7528\4E8E\5BF9\6BD4\7684\5176\4ED6\6A21\578B（\5982 Kimi-K2、DeepSeek-V3.2）','active','competitor_model',U&'["\7ADE\54C1\6A21\578B","\5BF9\6BD4\6A21\578B","\7ADE\54C1","Competitor"]'::jsonb),
 ('tpl_obj_llm_pt','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\540E\8BAD\7EC3\6280\672F',U&'\540E\8BAD\7EC3\9636\6BB5\6280\672F（\5982 MOPD、Agentic RL）','active','post_training_technique',U&'["\540E\8BAD\7EC3\6280\672F","\8BAD\7EC3\6280\672F","Post-Training"]'::jsonb),
 ('tpl_obj_llm_infra','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'RL\57FA\7840\8BBE\65BD',U&'\5F3A\5316\5B66\4E60\8BAD\7EC3\57FA\7840\8BBE\65BD\7EC4\4EF6','active','rl_infrastructure',U&'["RL\57FA\7840\8BBE\65BD","\8BAD\7EC3\57FA\7840\8BBE\65BD","Infrastructure"]'::jsonb),
 ('tpl_obj_llm_deploy','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\90E8\7F72\914D\7F6E',U&'\63A8\7406\90E8\7F72\914D\7F6E（\6846\67B6、\7CBE\5EA6、\542F\52A8\547D\4EE4）','active','deployment_config',U&'["\90E8\7F72\914D\7F6E","\90E8\7F72","Deployment"]'::jsonb),
 ('tpl_obj_llm_sample','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\91C7\6837\53C2\6570',U&'\63A8\8350\91C7\6837\53C2\6570（top_p、temperature\7B49）','active','sampling_parameter',U&'["\91C7\6837\53C2\6570","\53C2\6570","Sampling"]'::jsonb),
 ('tpl_obj_llm_prompt','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\7CFB\7EDF\63D0\793A\8BCD',U&'\63A8\8350\7684\7CFB\7EDF\63D0\793A\8BCD','active','system_prompt',U&'["\7CFB\7EDF\63D0\793A\8BCD","\63D0\793A\8BCD","System Prompt"]'::jsonb),
 ('tpl_obj_llm_tool','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\5DE5\5177\4F7F\7528\5B9E\8DF5',U&'\5DE5\5177\8C03\7528\6CE8\610F\4E8B\9879\4E0E\6700\4F73\5B9E\8DF5','active','tool_use_practice',U&'["\5DE5\5177\4F7F\7528\5B9E\8DF5","\5DE5\5177\8C03\7528","Tool Use"]'::jsonb),
 ('tpl_obj_llm_org','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\7814\53D1\673A\6784',U&'\6A21\578B\7814\53D1\65B9/\56E2\961F（\5982 Xiaomi、LLM-Core Xiaomi）','active','research_org',U&'["\7814\53D1\673A\6784","\5F00\53D1\65B9","\5382\5546","\56E2\961F","Organization"]'::jsonb),
 ('tpl_obj_llm_report','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\6280\672F\62A5\544A',U&'\6A21\578B\6280\672F\62A5\544A/\8BBA\6587\672C\4F53（\542B arXiv \5F15\7528）','active','technical_report',U&'["\6280\672F\62A5\544A","\8BBA\6587","Technical Report","Paper"]'::jsonb),
 ('tpl_obj_llm_scenario','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\5E94\7528\573A\666F',U&'\6A21\578B\9002\7528\7684\4EFB\52A1/\5E94\7528\573A\666F（\5982 \6570\5B66、\5199\4F5C、Web\5F00\53D1、\667A\80FD\4F53、\5DE5\5177\8C03\7528）','active','application_scenario',U&'["\5E94\7528\573A\666F","\4EFB\52A1\7C7B\578B","\573A\666F","Use Case"]'::jsonb),
 ('tpl_obj_llm_framework','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\8F6F\4EF6\6846\67B6',U&'\63A8\7406/\8BAD\7EC3/\89E3\7801\8F6F\4EF6\6846\67B6（\5982 SGLang、Megatron-LM、DeepEP、EAGLE）','active','software_framework',U&'["\8F6F\4EF6\6846\67B6","\6846\67B6","\5F15\64CE","Framework"]'::jsonb),
 ('tpl_obj_llm_perf','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\6027\80FD\6307\6807',U&'\6A21\578B/\67B6\6784\7684\6027\80FD\4E0E\6548\7387\6307\6807（\5982 KV\7F13\5B58\7F29\51CF、\63A8\7406\52A0\901F、\541E\5410）','active','performance_metric',U&'["\6027\80FD\6307\6807","\6548\7387\6307\6807","Performance Metric"]'::jsonb),
 ('tpl_obj_llm_env','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\8BAD\7EC3\73AF\5883',U&'RL/\667A\80FD\4F53\8BAD\7EC3\73AF\5883\4E0E\6570\636E（\5982 GitHub issue \4EFB\52A1、K8s \96C6\7FA4、\591A\6A21\6001\9A8C\8BC1\5668）','active','training_environment',U&'["\8BAD\7EC3\73AF\5883","\8BAD\7EC3\6570\636E","\73AF\5883","Environment"]'::jsonb)
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_domain.template_attributes
    (id, tenant_id, template_object_id, attr_name, description, attr_type, is_primary_key, constraints_json, sort_order, ontology_code, is_required)
VALUES

    ('tpl_attr_llm_md_name','tenant_jonex_demo','tpl_obj_llm_model',U&'\6A21\578B\540D\79F0',U&'\6A21\578B\540D\79F0（\5982 MiMo-V2-Flash）',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'model_name',1),
    ('tpl_attr_llm_md_family','tenant_jonex_demo','tpl_obj_llm_model',U&'\6A21\578B\7CFB\5217',U&'\6A21\578B\7CFB\5217（\5982 MiMo）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,2,'model_family',0),
    ('tpl_attr_llm_md_type','tenant_jonex_demo','tpl_obj_llm_model',U&'\6A21\578B\7C7B\578B','MoE/Dense',U&'\679A\4E3E',0,'{}'::jsonb,3,'model_type',0),
    ('tpl_attr_llm_md_total','tenant_jonex_demo','tpl_obj_llm_model',U&'\603B\53C2\6570\91CF',U&'\6A21\578B\603B\53C2\6570\91CF（\5982 309B）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,4,'total_params',0),
    ('tpl_attr_llm_md_active','tenant_jonex_demo','tpl_obj_llm_model',U&'\6FC0\6D3B\53C2\6570\91CF',U&'\6A21\578B\6FC0\6D3B\53C2\6570\91CF（\5982 15B）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,5,'active_params',0),
    ('tpl_attr_llm_md_ctx','tenant_jonex_demo','tpl_obj_llm_model',U&'\4E0A\4E0B\6587\957F\5EA6',U&'\6A21\578B\652F\6301\7684\6700\5927\4E0A\4E0B\6587\957F\5EA6（\5982 256k）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,6,'context_length',0),
    ('tpl_attr_llm_md_dev','tenant_jonex_demo','tpl_obj_llm_model',U&'\5F00\53D1\65B9',U&'\6A21\578B\5F00\53D1\65B9（\5982 Xiaomi）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,7,'developer',0),
    ('tpl_attr_llm_md_release','tenant_jonex_demo','tpl_obj_llm_model',U&'\53D1\5E03\65E5\671F',U&'\6A21\578B\53D1\5E03\65E5\671F',U&'\65E5\671F',0,'{}'::jsonb,8,'release_date',0),
    ('tpl_attr_llm_md_hf','tenant_jonex_demo','tpl_obj_llm_model',U&'HuggingFace\5730\5740',U&'HuggingFace \6A21\578B\5730\5740',U&'\5B57\7B26\4E32',0,'{}'::jsonb,9,'huggingface_url',0),
    ('tpl_attr_llm_md_cutoff','tenant_jonex_demo','tpl_obj_llm_model',U&'\77E5\8BC6\622A\6B62\65E5\671F',U&'\6A21\578B\77E5\8BC6\622A\6B62\65E5\671F（\5982 2024-12）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,10,'knowledge_cutoff',0),
    ('tpl_attr_llm_md_license','tenant_jonex_demo','tpl_obj_llm_model',U&'\8BB8\53EF\8BC1',U&'\6A21\578B\8BB8\53EF\8BC1\7C7B\578B',U&'\5B57\7B26\4E32',0,'{}'::jsonb,11,'license_type',0),

    ('tpl_attr_llm_ar_name','tenant_jonex_demo','tpl_obj_llm_arch',U&'\67B6\6784\540D\79F0',U&'\67B6\6784\540D\79F0（\5982 Hybrid Sliding Window Attention）',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'architecture_name',1),
    ('tpl_attr_llm_ar_atype','tenant_jonex_demo','tpl_obj_llm_arch',U&'\6CE8\610F\529B\7C7B\578B','Hybrid/SWA/GA',U&'\679A\4E3E',0,'{}'::jsonb,2,'attention_type',0),
    ('tpl_attr_llm_ar_ratio','tenant_jonex_demo','tpl_obj_llm_arch',U&'SWA:GA\6BD4\4F8B',U&'SWA\4E0EGA\5C42\6BD4\4F8B（\5982 5:1）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,3,'swa_ga_ratio',0),
    ('tpl_attr_llm_ar_win','tenant_jonex_demo','tpl_obj_llm_arch',U&'\7A97\53E3\5927\5C0F',U&'SWA\7A97\53E3\5927\5C0F（token\6570）',U&'\6570\503C',0,'{}'::jsonb,4,'window_size',0),
    ('tpl_attr_llm_ar_blocks','tenant_jonex_demo','tpl_obj_llm_arch',U&'\6DF7\5408\5757\6570',U&'\6DF7\5408\5757\6570\91CF M（\5982 8）',U&'\6570\503C',0,'{}'::jsonb,5,'num_hybrid_blocks',0),
    ('tpl_attr_llm_ar_swa','tenant_jonex_demo','tpl_obj_llm_arch',U&'\6BCF\5757SWA\5C42\6570',U&'\6BCF\4E2A\6DF7\5408\5757\4E2DSWA\5C42\6570 N（\5982 5）',U&'\6570\503C',0,'{}'::jsonb,6,'swa_layers_per_block',0),
    ('tpl_attr_llm_ar_ga','tenant_jonex_demo','tpl_obj_llm_arch',U&'\6BCF\5757GA\5C42\6570',U&'\6BCF\4E2A\6DF7\5408\5757\4E2DGA\5C42\6570（\5982 1）',U&'\6570\503C',0,'{}'::jsonb,7,'ga_layers_per_block',0),
    ('tpl_attr_llm_ar_sink','tenant_jonex_demo','tpl_obj_llm_arch',U&'\542F\7528sink bias',U&'\662F\5426\542F\7528\53EF\5B66\4E60\6CE8\610F\529Bsink bias',U&'\5E03\5C14',0,'{}'::jsonb,8,'sink_bias_enabled',0),
    ('tpl_attr_llm_ar_mtp','tenant_jonex_demo','tpl_obj_llm_arch',U&'\542F\7528MTP',U&'\662F\5426\542F\7528\591AToken\9884\6D4B',U&'\5E03\5C14',0,'{}'::jsonb,9,'mtp_enabled',0),
    ('tpl_attr_llm_ar_mtp_param','tenant_jonex_demo','tpl_obj_llm_arch',U&'MTP\6BCF\5757\53C2\6570\91CF',U&'MTP\6A21\5757\6BCF\5757\53C2\6570\91CF（\5982 0.33B）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,10,'mtp_params_per_block',0),
    ('tpl_attr_llm_ar_mtp_struct','tenant_jonex_demo','tpl_obj_llm_arch',U&'MTP\7ED3\6784',U&'MTP\6A21\5757\7ED3\6784（\5982 dense FFN + SWA）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,11,'mtp_structure',0),
    ('tpl_attr_llm_ar_kv','tenant_jonex_demo','tpl_obj_llm_arch',U&'KV\7F13\5B58\7F29\51CF',U&'KV\7F13\5B58\7F29\51CF\500D\6570（\5982 6x）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,12,'kv_cache_reduction',0),

    ('tpl_attr_llm_tr_name','tenant_jonex_demo','tpl_obj_llm_train',U&'\914D\7F6E\540D\79F0',U&'\8BAD\7EC3\914D\7F6E\540D\79F0',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'config_name',1),
    ('tpl_attr_llm_tr_tokens','tenant_jonex_demo','tpl_obj_llm_train',U&'\8BAD\7EC3token\6570',U&'\9884\8BAD\7EC3token\6570（\5982 27T）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,2,'training_tokens',0),
    ('tpl_attr_llm_tr_prec','tenant_jonex_demo','tpl_obj_llm_train',U&'\7CBE\5EA6',U&'\8BAD\7EC3\7CBE\5EA6（\5982 FP8 mixed）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,3,'precision',0),
    ('tpl_attr_llm_tr_seq','tenant_jonex_demo','tpl_obj_llm_train',U&'\539F\751F\5E8F\5217\957F\5EA6',U&'\539F\751F\5E8F\5217\957F\5EA6（\5982 32000）',U&'\6570\503C',0,'{}'::jsonb,4,'native_seq_length',0),
    ('tpl_attr_llm_tr_maxctx','tenant_jonex_demo','tpl_obj_llm_train',U&'\6700\5927\4E0A\4E0B\6587\957F\5EA6',U&'\652F\6301\7684\6700\5927\4E0A\4E0B\6587\957F\5EA6（\5982 262144）',U&'\6570\503C',0,'{}'::jsonb,5,'max_context_length',0),
    ('tpl_attr_llm_tr_method','tenant_jonex_demo','tpl_obj_llm_train',U&'\8BAD\7EC3\65B9\6CD5',U&'\8BAD\7EC3\65B9\6CD5\8BF4\660E',U&'\6587\672C',0,'{}'::jsonb,6,'training_method',0),

    ('tpl_attr_llm_bm_name','tenant_jonex_demo','tpl_obj_llm_bench',U&'\57FA\51C6\540D\79F0',U&'\57FA\51C6\6D4B\8BD5\540D\79F0（\5982 MMLU-Pro）',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'benchmark_name',1),
    ('tpl_attr_llm_bm_cat','tenant_jonex_demo','tpl_obj_llm_bench',U&'\7C7B\522B',U&'\57FA\51C6\7C7B\522B（General/Math/Code/Chinese/Multilingual/Long Context/Reasoning/Writing/Code Agent/General Agent）',U&'\679A\4E3E',0,'{}'::jsonb,2,'category',0),
    ('tpl_attr_llm_bm_setting','tenant_jonex_demo','tpl_obj_llm_bench',U&'\8BBE\7F6E',U&'\8BC4\6D4B\8BBE\7F6E（\5982 5-shot）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,3,'setting',0),
    ('tpl_attr_llm_bm_shot','tenant_jonex_demo','tpl_obj_llm_bench',U&'shot\6570',U&'few-shot \6570\91CF',U&'\6570\503C',0,'{}'::jsonb,4,'shot_count',0),
    ('tpl_attr_llm_bm_desc','tenant_jonex_demo','tpl_obj_llm_bench',U&'\63CF\8FF0',U&'\57FA\51C6\6D4B\8BD5\8BF4\660E',U&'\6587\672C',0,'{}'::jsonb,5,'description',0),

    ('tpl_attr_llm_rs_id','tenant_jonex_demo','tpl_obj_llm_result',U&'\7ED3\679CID',U&'\8BC4\6D4B\7ED3\679C\552F\4E00\6807\8BC6',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'result_id',1),
    ('tpl_attr_llm_rs_model','tenant_jonex_demo','tpl_obj_llm_result',U&'\6A21\578B\540D\79F0',U&'\88AB\8BC4\6D4B\6A21\578B\540D\79F0',U&'\5B57\7B26\4E32',0,'{}'::jsonb,2,'model_name',1),
    ('tpl_attr_llm_rs_bench','tenant_jonex_demo','tpl_obj_llm_result',U&'\57FA\51C6\540D\79F0',U&'\8BC4\6D4B\57FA\51C6\540D\79F0',U&'\5B57\7B26\4E32',0,'{}'::jsonb,3,'benchmark_name',1),
    ('tpl_attr_llm_rs_score','tenant_jonex_demo','tpl_obj_llm_result',U&'\5F97\5206',U&'\8BC4\6D4B\5F97\5206',U&'\6570\503C',0,'{}'::jsonb,4,'score',1),
    ('tpl_attr_llm_rs_setting','tenant_jonex_demo','tpl_obj_llm_result',U&'\8BBE\7F6E',U&'\8BC4\6D4B\8BBE\7F6E',U&'\5B57\7B26\4E32',0,'{}'::jsonb,5,'setting',0),
    ('tpl_attr_llm_rs_length','tenant_jonex_demo','tpl_obj_llm_result',U&'\957F\5EA6\8BBE\7F6E',U&'\957F\4E0A\4E0B\6587\8BC4\6D4B\957F\5EA6（\5982 32K/64K/128K/256K）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,6,'length',0),
    ('tpl_attr_llm_rs_phase','tenant_jonex_demo','tpl_obj_llm_result',U&'\8BC4\6D4B\9636\6BB5','base/post-training',U&'\679A\4E3E',0,'{}'::jsonb,7,'eval_phase',0),

    ('tpl_attr_llm_cp_name','tenant_jonex_demo','tpl_obj_llm_comp',U&'\6A21\578B\540D\79F0',U&'\7ADE\54C1\6A21\578B\540D\79F0（\5982 Kimi-K2 Thinking）',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'model_name',1),
    ('tpl_attr_llm_cp_dev','tenant_jonex_demo','tpl_obj_llm_comp',U&'\5F00\53D1\65B9',U&'\7ADE\54C1\5F00\53D1\65B9',U&'\5B57\7B26\4E32',0,'{}'::jsonb,2,'developer',0),
    ('tpl_attr_llm_cp_total','tenant_jonex_demo','tpl_obj_llm_comp',U&'\603B\53C2\6570\91CF',U&'\7ADE\54C1\603B\53C2\6570\91CF',U&'\5B57\7B26\4E32',0,'{}'::jsonb,3,'total_params',0),
    ('tpl_attr_llm_cp_active','tenant_jonex_demo','tpl_obj_llm_comp',U&'\6FC0\6D3B\53C2\6570\91CF',U&'\7ADE\54C1\6FC0\6D3B\53C2\6570\91CF',U&'\5B57\7B26\4E32',0,'{}'::jsonb,4,'active_params',0),

    ('tpl_attr_llm_pt_name','tenant_jonex_demo','tpl_obj_llm_pt',U&'\6280\672F\540D\79F0',U&'\540E\8BAD\7EC3\6280\672F\540D\79F0（\5982 MOPD）',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'technique_name',1),
    ('tpl_attr_llm_pt_type','tenant_jonex_demo','tpl_obj_llm_pt',U&'\6280\672F\7C7B\578B','distillation/rl/infrastructure',U&'\679A\4E3E',0,'{}'::jsonb,2,'technique_type',0),
    ('tpl_attr_llm_pt_desc','tenant_jonex_demo','tpl_obj_llm_pt',U&'\63CF\8FF0',U&'\6280\672F\63CF\8FF0',U&'\6587\672C',0,'{}'::jsonb,3,'description',0),
    ('tpl_attr_llm_pt_feat','tenant_jonex_demo','tpl_obj_llm_pt',U&'\6838\5FC3\7279\6027',U&'\6280\672F\6838\5FC3\7279\6027\8BF4\660E',U&'\6587\672C',0,'{}'::jsonb,4,'key_features',0),

    ('tpl_attr_llm_if_name','tenant_jonex_demo','tpl_obj_llm_infra',U&'\7EC4\4EF6\540D\79F0',U&'\57FA\7840\8BBE\65BD\7EC4\4EF6\540D\79F0（\5982 Rollout Routing Replay）',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'component_name',1),
    ('tpl_attr_llm_if_desc','tenant_jonex_demo','tpl_obj_llm_infra',U&'\63CF\8FF0',U&'\7EC4\4EF6\63CF\8FF0',U&'\6587\672C',0,'{}'::jsonb,2,'description',0),
    ('tpl_attr_llm_if_purpose','tenant_jonex_demo','tpl_obj_llm_infra',U&'\7528\9014',U&'\7EC4\4EF6\7528\9014\8BF4\660E',U&'\6587\672C',0,'{}'::jsonb,3,'purpose',0),

    ('tpl_attr_llm_dp_name','tenant_jonex_demo','tpl_obj_llm_deploy',U&'\914D\7F6E\540D\79F0',U&'\90E8\7F72\914D\7F6E\540D\79F0',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'config_name',1),
    ('tpl_attr_llm_dp_fw','tenant_jonex_demo','tpl_obj_llm_deploy',U&'\6846\67B6',U&'\63A8\7406\6846\67B6（\5982 SGLang）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,2,'framework',0),
    ('tpl_attr_llm_dp_prec','tenant_jonex_demo','tpl_obj_llm_deploy',U&'\7CBE\5EA6',U&'\63A8\7406\7CBE\5EA6（\5982 FP8）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,3,'precision',0),
    ('tpl_attr_llm_dp_cmd','tenant_jonex_demo','tpl_obj_llm_deploy',U&'\670D\52A1\542F\52A8\547D\4EE4',U&'\670D\52A1\542F\52A8\547D\4EE4',U&'\6587\672C',0,'{}'::jsonb,4,'server_command',0),
    ('tpl_attr_llm_dp_ver','tenant_jonex_demo','tpl_obj_llm_deploy',U&'\63A8\8350\7248\672C',U&'\63A8\8350\6846\67B6\7248\672C',U&'\5B57\7B26\4E32',0,'{}'::jsonb,5,'recommended_version',0),

    ('tpl_attr_llm_sp_name','tenant_jonex_demo','tpl_obj_llm_sample',U&'\53C2\6570\540D\79F0',U&'\91C7\6837\53C2\6570\540D\79F0（\5982 top_p、temperature）',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'param_name',1),
    ('tpl_attr_llm_sp_val','tenant_jonex_demo','tpl_obj_llm_sample',U&'\63A8\8350\503C',U&'\53C2\6570\63A8\8350\503C（\5982 0.95）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,2,'recommended_value',0),
    ('tpl_attr_llm_sp_case','tenant_jonex_demo','tpl_obj_llm_sample',U&'\4F7F\7528\573A\666F',U&'\53C2\6570\9002\7528\573A\666F（\5982 math/writing/agentic）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,3,'use_case',0),

    ('tpl_attr_llm_sy_lang','tenant_jonex_demo','tpl_obj_llm_prompt',U&'\8BED\8A00',U&'\63D0\793A\8BCD\8BED\8A00（en/zh）',U&'\679A\4E3E',1,'{}'::jsonb,1,'language',1),
    ('tpl_attr_llm_sy_content','tenant_jonex_demo','tpl_obj_llm_prompt',U&'\5185\5BB9',U&'\63D0\793A\8BCD\5185\5BB9',U&'\6587\672C',0,'{}'::jsonb,2,'content',1),
    ('tpl_attr_llm_sy_purpose','tenant_jonex_demo','tpl_obj_llm_prompt',U&'\7528\9014',U&'\63D0\793A\8BCD\7528\9014\8BF4\660E',U&'\5B57\7B26\4E32',0,'{}'::jsonb,3,'purpose',0),

    ('tpl_attr_llm_tl_name','tenant_jonex_demo','tpl_obj_llm_tool',U&'\5B9E\8DF5\540D\79F0',U&'\5DE5\5177\4F7F\7528\5B9E\8DF5\540D\79F0',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'practice_name',1),
    ('tpl_attr_llm_tl_desc','tenant_jonex_demo','tpl_obj_llm_tool',U&'\63CF\8FF0',U&'\5B9E\8DF5\63CF\8FF0',U&'\6587\672C',0,'{}'::jsonb,2,'description',0),
    ('tpl_attr_llm_tl_req','tenant_jonex_demo','tpl_obj_llm_tool',U&'\8981\6C42',U&'\5B9E\8DF5\8981\6C42\8BF4\660E',U&'\6587\672C',0,'{}'::jsonb,3,'requirement',0),

    ('tpl_attr_llm_org_name','tenant_jonex_demo','tpl_obj_llm_org',U&'\673A\6784\540D\79F0',U&'\7814\53D1\673A\6784/\56E2\961F\540D\79F0（\5982 Xiaomi、LLM-Core Xiaomi）',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'org_name',1),
    ('tpl_attr_llm_org_type','tenant_jonex_demo','tpl_obj_llm_org',U&'\673A\6784\7C7B\578B',U&'\516C\53F8/\7814\7A76\56E2\961F/\5B9E\9A8C\5BA4',U&'\679A\4E3E',0,'{}'::jsonb,2,'org_type',0),
    ('tpl_attr_llm_org_contact','tenant_jonex_demo','tpl_obj_llm_org',U&'\8054\7CFB\65B9\5F0F',U&'\90AE\7BB1/\5B98\7F51\7B49\8054\7CFB\65B9\5F0F（\5982 mimo@xiaomi.com）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,3,'contact',0),

    ('tpl_attr_llm_rp_title','tenant_jonex_demo','tpl_obj_llm_report',U&'\62A5\544A\6807\9898',U&'\6280\672F\62A5\544A/\8BBA\6587\6807\9898（\5982 MiMo-V2-Flash Technical Report）',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'report_title',1),
    ('tpl_attr_llm_rp_arxiv','tenant_jonex_demo','tpl_obj_llm_report',U&'arXiv\7F16\53F7',U&'arXiv \9884\5370\672C\7F16\53F7（\5982 2601.02780）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,2,'arxiv_id',0),
    ('tpl_attr_llm_rp_authors','tenant_jonex_demo','tpl_obj_llm_report',U&'\4F5C\8005',U&'\62A5\544A\4F5C\8005（\5982 LLM-Core Xiaomi）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,3,'authors',0),
    ('tpl_attr_llm_rp_year','tenant_jonex_demo','tpl_obj_llm_report',U&'\5E74\4EFD',U&'\62A5\544A\53D1\8868\5E74\4EFD（\5982 2026）',U&'\6570\503C',0,'{}'::jsonb,4,'year',0),
    ('tpl_attr_llm_rp_url','tenant_jonex_demo','tpl_obj_llm_report',U&'\94FE\63A5',U&'\62A5\544A/\8BBA\6587\8BBF\95EE\94FE\63A5',U&'\5B57\7B26\4E32',0,'{}'::jsonb,5,'url',0),
    ('tpl_attr_llm_rp_class','tenant_jonex_demo','tpl_obj_llm_report',U&'\4E3B\9898\5206\7C7B',U&'arXiv \4E3B\9898\5206\7C7B（\5982 cs.CL）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,6,'primary_class',0),

    ('tpl_attr_llm_sc_name','tenant_jonex_demo','tpl_obj_llm_scenario',U&'\573A\666F\540D\79F0',U&'\5E94\7528/\4EFB\52A1\573A\666F\540D\79F0（\5982 \6570\5B66、\5199\4F5C、Web\5F00\53D1、\667A\80FD\4F53、\5DE5\5177\8C03\7528）',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'scenario_name',1),
    ('tpl_attr_llm_sc_type','tenant_jonex_demo','tpl_obj_llm_scenario',U&'\573A\666F\7C7B\578B','reasoning/coding/writing/agentic/tool_use/math',U&'\679A\4E3E',0,'{}'::jsonb,2,'scenario_type',0),
    ('tpl_attr_llm_sc_desc','tenant_jonex_demo','tpl_obj_llm_scenario',U&'\63CF\8FF0',U&'\573A\666F\8BF4\660E',U&'\6587\672C',0,'{}'::jsonb,3,'description',0),

    ('tpl_attr_llm_fw_name','tenant_jonex_demo','tpl_obj_llm_framework',U&'\6846\67B6\540D\79F0',U&'\8F6F\4EF6\6846\67B6\540D\79F0（\5982 SGLang、Megatron-LM、DeepEP、EAGLE）',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'framework_name',1),
    ('tpl_attr_llm_fw_type','tenant_jonex_demo','tpl_obj_llm_framework',U&'\6846\67B6\7C7B\578B',U&'\63A8\7406/\8BAD\7EC3/\89E3\7801/\901A\4FE1',U&'\679A\4E3E',0,'{}'::jsonb,2,'framework_type',0),
    ('tpl_attr_llm_fw_version','tenant_jonex_demo','tpl_obj_llm_framework',U&'\7248\672C',U&'\6846\67B6\7248\672C（\5982 sglang==0.5.6.post2...）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,3,'version',0),
    ('tpl_attr_llm_fw_purpose','tenant_jonex_demo','tpl_obj_llm_framework',U&'\7528\9014',U&'\6846\67B6\7528\9014\8BF4\660E',U&'\6587\672C',0,'{}'::jsonb,4,'purpose',0),

    ('tpl_attr_llm_pf_name','tenant_jonex_demo','tpl_obj_llm_perf',U&'\6307\6807\540D\79F0',U&'\6027\80FD/\6548\7387\6307\6807\540D\79F0（\5982 KV\7F13\5B58\7F29\51CF、\63A8\7406\52A0\901F、\8BAD\7EC3\541E\5410）',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'metric_name',1),
    ('tpl_attr_llm_pf_value','tenant_jonex_demo','tpl_obj_llm_perf',U&'\6307\6807\503C',U&'\6307\6807\6570\503C/\500D\6570（\5982 6x、3x、70%）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,2,'metric_value',0),
    ('tpl_attr_llm_pf_baseline','tenant_jonex_demo','tpl_obj_llm_perf',U&'\57FA\7EBF/\5BF9\6BD4',U&'\5BF9\6BD4\57FA\7EBF\6216\5BF9\7167\5BF9\8C61',U&'\5B57\7B26\4E32',0,'{}'::jsonb,3,'baseline',0),
    ('tpl_attr_llm_pf_desc','tenant_jonex_demo','tpl_obj_llm_perf',U&'\63CF\8FF0',U&'\6307\6807\8BF4\660E',U&'\6587\672C',0,'{}'::jsonb,4,'description',0),

    ('tpl_attr_llm_ev_name','tenant_jonex_demo','tpl_obj_llm_env',U&'\73AF\5883\540D\79F0',U&'\8BAD\7EC3\73AF\5883/\6570\636E\540D\79F0（\5982 Code Agent \73AF\5883、WebDev \591A\6A21\6001\9A8C\8BC1\5668）',U&'\5B57\7B26\4E32',1,'{}'::jsonb,1,'env_name',1),
    ('tpl_attr_llm_ev_type','tenant_jonex_demo','tpl_obj_llm_env',U&'\73AF\5883\7C7B\578B','code_agent/webdev/general/dataset',U&'\679A\4E3E',0,'{}'::jsonb,2,'env_type',0),
    ('tpl_attr_llm_ev_scale','tenant_jonex_demo','tpl_obj_llm_env',U&'\89C4\6A21',U&'\73AF\5883/\6570\636E\89C4\6A21（\5982 100,000 \53EF\9A8C\8BC1\4EFB\52A1、10,000 \5E76\53D1 pod）',U&'\5B57\7B26\4E32',0,'{}'::jsonb,3,'scale',0),
    ('tpl_attr_llm_ev_desc','tenant_jonex_demo','tpl_obj_llm_env',U&'\63CF\8FF0',U&'\73AF\5883\8BF4\660E',U&'\6587\672C',0,'{}'::jsonb,4,'description',0)
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_domain.template_relations
    (id, tenant_id, domain_id, scenario_id, name, description, source_object_id, target_object_id, relation_type, status, ontology_code, aliases)
VALUES
 ('tpl_rel_llm_md_arch','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\91C7\7528\67B6\6784',U&'AI\6A21\578B\91C7\7528\7684\6A21\578B\67B6\6784','tpl_obj_llm_model','tpl_obj_llm_arch',U&'\4E00\5BF9\4E00','active','MODEL_HAS_ARCHITECTURE',U&'["\91C7\7528\67B6\6784","\4F7F\7528\67B6\6784"]'::jsonb),
 ('tpl_rel_llm_md_train','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\8BAD\7EC3\914D\7F6E',U&'AI\6A21\578B\7684\9884\8BAD\7EC3\914D\7F6E','tpl_obj_llm_model','tpl_obj_llm_train',U&'\4E00\5BF9\591A','active','MODEL_TRAINED_WITH',U&'["\8BAD\7EC3\914D\7F6E","\9884\8BAD\7EC3\914D\7F6E"]'::jsonb),
 ('tpl_rel_llm_md_result','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\8BC4\6D4B\7ED3\679C',U&'AI\6A21\578B\5728\57FA\51C6\4E0A\7684\8BC4\6D4B\7ED3\679C','tpl_obj_llm_model','tpl_obj_llm_result',U&'\4E00\5BF9\591A','active','MODEL_EVALUATED_ON',U&'["\8BC4\6D4B\7ED3\679C","\5F97\5206"]'::jsonb),
 ('tpl_rel_llm_rs_bench','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\6240\5C5E\57FA\51C6',U&'\8BC4\6D4B\7ED3\679C\5BF9\5E94\7684\57FA\51C6\6D4B\8BD5','tpl_obj_llm_result','tpl_obj_llm_bench',U&'\591A\5BF9\4E00','active','RESULT_MEASURED_BY',U&'["\6240\5C5E\57FA\51C6","\5BF9\5E94\57FA\51C6"]'::jsonb),
 ('tpl_rel_llm_rs_comp','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\5BF9\6BD4\7ADE\54C1',U&'\8BC4\6D4B\7ED3\679C\5BF9\6BD4\7684\7ADE\54C1\6A21\578B','tpl_obj_llm_result','tpl_obj_llm_comp',U&'\591A\5BF9\591A','active','RESULT_COMPARED_WITH',U&'["\5BF9\6BD4\7ADE\54C1","\7ADE\54C1\5BF9\6BD4"]'::jsonb),
 ('tpl_rel_llm_md_pt','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\540E\8BAD\7EC3\6280\672F',U&'AI\6A21\578B\4F7F\7528\7684\540E\8BAD\7EC3\6280\672F','tpl_obj_llm_model','tpl_obj_llm_pt',U&'\4E00\5BF9\591A','active','MODEL_USES_TECHNIQUE',U&'["\540E\8BAD\7EC3\6280\672F","\4F7F\7528\6280\672F"]'::jsonb),
 ('tpl_rel_llm_pt_infra','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\4F9D\8D56\57FA\7840\8BBE\65BD',U&'\540E\8BAD\7EC3\6280\672F\4F9D\8D56\7684RL\57FA\7840\8BBE\65BD','tpl_obj_llm_pt','tpl_obj_llm_infra',U&'\591A\5BF9\591A','active','TECHNIQUE_USES_INFRA',U&'["\4F9D\8D56\57FA\7840\8BBE\65BD","\4F7F\7528\57FA\7840\8BBE\65BD"]'::jsonb),
 ('tpl_rel_llm_md_deploy','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\90E8\7F72\914D\7F6E',U&'AI\6A21\578B\7684\63A8\7406\90E8\7F72\914D\7F6E','tpl_obj_llm_model','tpl_obj_llm_deploy',U&'\4E00\5BF9\591A','active','MODEL_DEPLOYED_WITH',U&'["\90E8\7F72\914D\7F6E","\90E8\7F72"]'::jsonb),
 ('tpl_rel_llm_dp_sp','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\91C7\6837\53C2\6570',U&'\90E8\7F72\914D\7F6E\63A8\8350\7684\91C7\6837\53C2\6570','tpl_obj_llm_deploy','tpl_obj_llm_sample',U&'\4E00\5BF9\591A','active','DEPLOYMENT_HAS_SAMPLING_PARAM',U&'["\91C7\6837\53C2\6570","\63A8\8350\53C2\6570"]'::jsonb),
 ('tpl_rel_llm_dp_sy','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\7CFB\7EDF\63D0\793A\8BCD',U&'\90E8\7F72\914D\7F6E\63A8\8350\7684\7CFB\7EDF\63D0\793A\8BCD','tpl_obj_llm_deploy','tpl_obj_llm_prompt',U&'\4E00\5BF9\591A','active','DEPLOYMENT_HAS_SYSTEM_PROMPT',U&'["\7CFB\7EDF\63D0\793A\8BCD","\63D0\793A\8BCD"]'::jsonb),
 ('tpl_rel_llm_dp_tl','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\5DE5\5177\4F7F\7528\5B9E\8DF5',U&'\90E8\7F72\914D\7F6E\7684\5DE5\5177\4F7F\7528\5B9E\8DF5','tpl_obj_llm_deploy','tpl_obj_llm_tool',U&'\4E00\5BF9\591A','active','DEPLOYMENT_HAS_TOOL_PRACTICE',U&'["\5DE5\5177\4F7F\7528\5B9E\8DF5","\5DE5\5177\5B9E\8DF5"]'::jsonb),
 ('tpl_rel_llm_md_org','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\7814\53D1\65B9',U&'AI\6A21\578B\7531\7814\53D1\673A\6784\5F00\53D1','tpl_obj_llm_model','tpl_obj_llm_org',U&'\591A\5BF9\4E00','active','MODEL_DEVELOPED_BY',U&'["\7814\53D1\65B9","\5F00\53D1\65B9","\7531...\7814\53D1"]'::jsonb),
 ('tpl_rel_llm_org_rp','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\53D1\5E03\62A5\544A',U&'\7814\53D1\673A\6784\53D1\5E03\6280\672F\62A5\544A','tpl_obj_llm_org','tpl_obj_llm_report',U&'\4E00\5BF9\591A','active','ORG_PUBLISHES_REPORT',U&'["\53D1\5E03\62A5\544A","\53D1\8868"]'::jsonb),
 ('tpl_rel_llm_rp_md','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\63CF\8FF0\6A21\578B',U&'\6280\672F\62A5\544A\63CF\8FF0\7684AI\6A21\578B','tpl_obj_llm_report','tpl_obj_llm_model',U&'\4E00\5BF9\4E00','active','REPORT_DESCRIBES_MODEL',U&'["\63CF\8FF0\6A21\578B","\4ECB\7ECD\6A21\578B"]'::jsonb),
 ('tpl_rel_llm_md_sc','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\9002\7528\573A\666F',U&'AI\6A21\578B\9002\7528\7684\5E94\7528/\4EFB\52A1\573A\666F','tpl_obj_llm_model','tpl_obj_llm_scenario',U&'\591A\5BF9\591A','active','MODEL_TARGETS_SCENARIO',U&'["\9002\7528\573A\666F","\9762\5411\573A\666F"]'::jsonb),
 ('tpl_rel_llm_sp_sc','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\9002\7528\573A\666F',U&'\91C7\6837\53C2\6570\63A8\8350\9002\7528\7684\573A\666F','tpl_obj_llm_sample','tpl_obj_llm_scenario',U&'\591A\5BF9\591A','active','SAMPLING_PARAM_FOR_SCENARIO',U&'["\9002\7528\573A\666F","\63A8\8350\573A\666F"]'::jsonb),
 ('tpl_rel_llm_dp_fw','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\4F7F\7528\6846\67B6',U&'\90E8\7F72\914D\7F6E\4F7F\7528\7684\8F6F\4EF6\6846\67B6','tpl_obj_llm_deploy','tpl_obj_llm_framework',U&'\591A\5BF9\591A','active','DEPLOYMENT_USES_FRAMEWORK',U&'["\4F7F\7528\6846\67B6","\57FA\4E8E\6846\67B6"]'::jsonb),
 ('tpl_rel_llm_if_fw','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\57FA\4E8E\6846\67B6',U&'RL\57FA\7840\8BBE\65BD\6784\5EFA\4E8E\8F6F\4EF6\6846\67B6\4E4B\4E0A','tpl_obj_llm_infra','tpl_obj_llm_framework',U&'\591A\5BF9\591A','active','INFRA_BUILT_ON_FRAMEWORK',U&'["\57FA\4E8E\6846\67B6","\6784\5EFA\4E8E"]'::jsonb),
 ('tpl_rel_llm_ar_pf','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\6027\80FD\8868\73B0',U&'\6A21\578B\67B6\6784\5E26\6765\7684\6027\80FD/\6548\7387\6307\6807','tpl_obj_llm_arch','tpl_obj_llm_perf',U&'\4E00\5BF9\591A','active','ARCHITECTURE_HAS_METRIC',U&'["\6027\80FD\8868\73B0","\6548\7387\6307\6807"]'::jsonb),
 ('tpl_rel_llm_pt_ev','tenant_jonex_demo','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report',U&'\4F7F\7528\73AF\5883',U&'\540E\8BAD\7EC3\6280\672F\4F7F\7528\7684\8BAD\7EC3\73AF\5883/\6570\636E','tpl_obj_llm_pt','tpl_obj_llm_env',U&'\591A\5BF9\591A','active','TECHNIQUE_USES_ENVIRONMENT',U&'["\4F7F\7528\73AF\5883","\4F9D\8D56\73AF\5883"]'::jsonb)
ON CONFLICT (id) DO NOTHING;




INSERT INTO knowledge_base.knowledge_info (id, tenant_id, space_id, name, description, data_source_types, document_count, status, owner_id) VALUES
    ('kb_demo_llm_tech_report', 'tenant_jonex_demo', 'space_demo_test', U&'AI\5927\6A21\578B\6280\672F\62A5\544A\77E5\8BC6\5E93', U&'AI\5927\6A21\578B\6280\672F\62A5\544A\7ED3\6784\5316\62BD\53D6\6F14\793A（\57FA\4E8E\5C0F\7C73MiMo-V2-Flash\6280\672F\62A5\544A）', '["file"]'::jsonb, 0, 'synced', '1')
ON CONFLICT (id) DO NOTHING;


INSERT INTO knowledge_base.knowledge_data_sources
    (id, tenant_id, knowledge_base_id, access_method_id,access_type, name, config_json, sync_mode, status)
VALUES
    ('ds_demo_llm_file', 'tenant_jonex_demo', 'kb_demo_llm_tech_report', 'dam_demo_file', 'file', U&'\6587\4EF6\4E0A\4F20', '{}'::jsonb, 'manual', 'active')
ON CONFLICT (id) DO NOTHING;


INSERT INTO knowledge_base.services (id, tenant_id, space_id, name, description, domain_type, status, api_key_encrypted)
VALUES
    ('svc_demo_llm_tech_report', 'tenant_jonex_demo', 'space_demo_test', U&'AI\5927\6A21\578B\6280\672F\62A5\544A\9886\57DF\670D\52A1', U&'AI\5927\6A21\578B\6280\672F\62A5\544A\89E3\6790\6D4B\8BD5\9886\57DF\670D\52A1', U&'AI\5927\6A21\578B', 'active', 'demo-llmtr-0123456789abcdef0123456789abcdef')
ON CONFLICT (id) DO NOTHING;


INSERT INTO knowledge_base.service_knowledge_bases (id, tenant_id, service_id, kb_id)
VALUES
    ('skb_demo_llmtr', 'tenant_jonex_demo', 'svc_demo_llm_tech_report', 'kb_demo_llm_tech_report')
ON CONFLICT (id) DO NOTHING;


INSERT INTO knowledge_base.service_api_keys (id, tenant_id, service_id, key_prefix, key_encrypted, expires_at, is_active)
VALUES
    ('sak_llmtr_main', 'tenant_jonex_demo', 'svc_demo_llm_tech_report', 'demo', 'demo-llmtr-0123456789abcdef0123456789abcdef', '2027-12-31'::timestamp, 1),
    ('sak_llmtr_readonly', 'tenant_jonex_demo', 'svc_demo_llm_tech_report', 'demo', 'demo-ro-llmtr-a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6', '2026-12-31'::timestamp, 1),
    ('sak_llmtr_expired', 'tenant_jonex_demo', 'svc_demo_llm_tech_report', 'demo', 'demo-expired-llmtr-000000000000000000000000', '2026-01-01'::timestamp, 0)
ON CONFLICT (id) DO NOTHING;


INSERT INTO knowledge_base.ontology_template_bindings
    (tenant_id, knowledge_base_id, template_domain_id, template_scenario_id, source_type, status)
VALUES
    ('tenant_jonex_demo','kb_demo_llm_tech_report','tpl_domain_ai_tech_report','tpl_scenario_llm_tech_report','business_template','active')
ON CONFLICT (tenant_id, knowledge_base_id) DO NOTHING;





INSERT INTO knowledge_base.ontology_compiled_schemas
    (tenant_id, knowledge_base_id, template_domain_id, template_scenario_id,
     source_type, source_version, source_hash, schema_version,
     entity_types, relation_types, constraints, disambiguation, prompt_schema,
     status, compiled_at)
VALUES (
    'tenant_jonex_demo', 'kb_demo_llm_tech_report',
    'tpl_domain_ai_tech_report', 'tpl_scenario_llm_tech_report',
    'business_template', 2, 'c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5', 2,
    U&'[
        {"name":"ai_model","display_name":"AI\6A21\578B","aliases":["AI\6A21\578B","\5927\6A21\578B","\8BED\8A00\6A21\578B","LLM","Model"],"source_object_id":"tpl_obj_llm_model","attributes":[
            {"name":"model_name","display_name":"\6A21\578B\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_llm_md_name"},
            {"name":"model_family","display_name":"\6A21\578B\7CFB\5217","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_md_family"},
            {"name":"model_type","display_name":"\6A21\578B\7C7B\578B","type":"enum","required":false,"source_attribute_id":"tpl_attr_llm_md_type"},
            {"name":"total_params","display_name":"\603B\53C2\6570\91CF","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_md_total"},
            {"name":"active_params","display_name":"\6FC0\6D3B\53C2\6570\91CF","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_md_active"},
            {"name":"context_length","display_name":"\4E0A\4E0B\6587\957F\5EA6","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_md_ctx"},
            {"name":"developer","display_name":"\5F00\53D1\65B9","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_md_dev"},
            {"name":"release_date","display_name":"\53D1\5E03\65E5\671F","type":"date","required":false,"source_attribute_id":"tpl_attr_llm_md_release"},
            {"name":"huggingface_url","display_name":"HuggingFace\5730\5740","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_md_hf"},
            {"name":"knowledge_cutoff","display_name":"\77E5\8BC6\622A\6B62\65E5\671F","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_md_cutoff"},
            {"name":"license_type","display_name":"\8BB8\53EF\8BC1","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_md_license"}
        ]},
        {"name":"model_architecture","display_name":"\6A21\578B\67B6\6784","aliases":["\6A21\578B\67B6\6784","\67B6\6784","Architecture"],"source_object_id":"tpl_obj_llm_arch","attributes":[
            {"name":"architecture_name","display_name":"\67B6\6784\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_llm_ar_name"},
            {"name":"attention_type","display_name":"\6CE8\610F\529B\7C7B\578B","type":"enum","required":false,"source_attribute_id":"tpl_attr_llm_ar_atype"},
            {"name":"swa_ga_ratio","display_name":"SWA:GA\6BD4\4F8B","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_ar_ratio"},
            {"name":"window_size","display_name":"\7A97\53E3\5927\5C0F","type":"number","required":false,"source_attribute_id":"tpl_attr_llm_ar_win"},
            {"name":"num_hybrid_blocks","display_name":"\6DF7\5408\5757\6570","type":"number","required":false,"source_attribute_id":"tpl_attr_llm_ar_blocks"},
            {"name":"swa_layers_per_block","display_name":"\6BCF\5757SWA\5C42\6570","type":"number","required":false,"source_attribute_id":"tpl_attr_llm_ar_swa"},
            {"name":"ga_layers_per_block","display_name":"\6BCF\5757GA\5C42\6570","type":"number","required":false,"source_attribute_id":"tpl_attr_llm_ar_ga"},
            {"name":"sink_bias_enabled","display_name":"\542F\7528sink bias","type":"boolean","required":false,"source_attribute_id":"tpl_attr_llm_ar_sink"},
            {"name":"mtp_enabled","display_name":"\542F\7528MTP","type":"boolean","required":false,"source_attribute_id":"tpl_attr_llm_ar_mtp"},
            {"name":"mtp_params_per_block","display_name":"MTP\6BCF\5757\53C2\6570\91CF","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_ar_mtp_param"},
            {"name":"mtp_structure","display_name":"MTP\7ED3\6784","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_ar_mtp_struct"},
            {"name":"kv_cache_reduction","display_name":"KV\7F13\5B58\7F29\51CF","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_ar_kv"}
        ]},
        {"name":"training_config","display_name":"\8BAD\7EC3\914D\7F6E","aliases":["\8BAD\7EC3\914D\7F6E","\9884\8BAD\7EC3","Training"],"source_object_id":"tpl_obj_llm_train","attributes":[
            {"name":"config_name","display_name":"\914D\7F6E\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_llm_tr_name"},
            {"name":"training_tokens","display_name":"\8BAD\7EC3token\6570","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_tr_tokens"},
            {"name":"precision","display_name":"\7CBE\5EA6","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_tr_prec"},
            {"name":"native_seq_length","display_name":"\539F\751F\5E8F\5217\957F\5EA6","type":"number","required":false,"source_attribute_id":"tpl_attr_llm_tr_seq"},
            {"name":"max_context_length","display_name":"\6700\5927\4E0A\4E0B\6587\957F\5EA6","type":"number","required":false,"source_attribute_id":"tpl_attr_llm_tr_maxctx"},
            {"name":"training_method","display_name":"\8BAD\7EC3\65B9\6CD5","type":"text","required":false,"source_attribute_id":"tpl_attr_llm_tr_method"}
        ]},
        {"name":"benchmark","display_name":"\57FA\51C6\6D4B\8BD5","aliases":["\57FA\51C6\6D4B\8BD5","\8BC4\6D4B\57FA\51C6","Benchmark"],"source_object_id":"tpl_obj_llm_bench","attributes":[
            {"name":"benchmark_name","display_name":"\57FA\51C6\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_llm_bm_name"},
            {"name":"category","display_name":"\7C7B\522B","type":"enum","required":false,"source_attribute_id":"tpl_attr_llm_bm_cat"},
            {"name":"setting","display_name":"\8BBE\7F6E","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_bm_setting"},
            {"name":"shot_count","display_name":"shot\6570","type":"number","required":false,"source_attribute_id":"tpl_attr_llm_bm_shot"},
            {"name":"description","display_name":"\63CF\8FF0","type":"text","required":false,"source_attribute_id":"tpl_attr_llm_bm_desc"}
        ]},
        {"name":"benchmark_result","display_name":"\8BC4\6D4B\7ED3\679C","aliases":["\8BC4\6D4B\7ED3\679C","\5F97\5206","Result","Score"],"source_object_id":"tpl_obj_llm_result","attributes":[
            {"name":"result_id","display_name":"\7ED3\679CID","type":"string","required":true,"source_attribute_id":"tpl_attr_llm_rs_id"},
            {"name":"model_name","display_name":"\6A21\578B\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_llm_rs_model"},
            {"name":"benchmark_name","display_name":"\57FA\51C6\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_llm_rs_bench"},
            {"name":"score","display_name":"\5F97\5206","type":"number","required":true,"source_attribute_id":"tpl_attr_llm_rs_score"},
            {"name":"setting","display_name":"\8BBE\7F6E","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_rs_setting"},
            {"name":"length","display_name":"\957F\5EA6\8BBE\7F6E","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_rs_length"},
            {"name":"eval_phase","display_name":"\8BC4\6D4B\9636\6BB5","type":"enum","required":false,"source_attribute_id":"tpl_attr_llm_rs_phase"}
        ]},
        {"name":"competitor_model","display_name":"\7ADE\54C1\6A21\578B","aliases":["\7ADE\54C1\6A21\578B","\5BF9\6BD4\6A21\578B","\7ADE\54C1","Competitor"],"source_object_id":"tpl_obj_llm_comp","attributes":[
            {"name":"model_name","display_name":"\6A21\578B\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_llm_cp_name"},
            {"name":"developer","display_name":"\5F00\53D1\65B9","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_cp_dev"},
            {"name":"total_params","display_name":"\603B\53C2\6570\91CF","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_cp_total"},
            {"name":"active_params","display_name":"\6FC0\6D3B\53C2\6570\91CF","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_cp_active"}
        ]},
        {"name":"post_training_technique","display_name":"\540E\8BAD\7EC3\6280\672F","aliases":["\540E\8BAD\7EC3\6280\672F","\8BAD\7EC3\6280\672F","Post-Training"],"source_object_id":"tpl_obj_llm_pt","attributes":[
            {"name":"technique_name","display_name":"\6280\672F\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_llm_pt_name"},
            {"name":"technique_type","display_name":"\6280\672F\7C7B\578B","type":"enum","required":false,"source_attribute_id":"tpl_attr_llm_pt_type"},
            {"name":"description","display_name":"\63CF\8FF0","type":"text","required":false,"source_attribute_id":"tpl_attr_llm_pt_desc"},
            {"name":"key_features","display_name":"\6838\5FC3\7279\6027","type":"text","required":false,"source_attribute_id":"tpl_attr_llm_pt_feat"}
        ]},
        {"name":"rl_infrastructure","display_name":"RL\57FA\7840\8BBE\65BD","aliases":["RL\57FA\7840\8BBE\65BD","\8BAD\7EC3\57FA\7840\8BBE\65BD","Infrastructure"],"source_object_id":"tpl_obj_llm_infra","attributes":[
            {"name":"component_name","display_name":"\7EC4\4EF6\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_llm_if_name"},
            {"name":"description","display_name":"\63CF\8FF0","type":"text","required":false,"source_attribute_id":"tpl_attr_llm_if_desc"},
            {"name":"purpose","display_name":"\7528\9014","type":"text","required":false,"source_attribute_id":"tpl_attr_llm_if_purpose"}
        ]},
        {"name":"deployment_config","display_name":"\90E8\7F72\914D\7F6E","aliases":["\90E8\7F72\914D\7F6E","\90E8\7F72","Deployment"],"source_object_id":"tpl_obj_llm_deploy","attributes":[
            {"name":"config_name","display_name":"\914D\7F6E\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_llm_dp_name"},
            {"name":"framework","display_name":"\6846\67B6","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_dp_fw"},
            {"name":"precision","display_name":"\7CBE\5EA6","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_dp_prec"},
            {"name":"server_command","display_name":"\670D\52A1\542F\52A8\547D\4EE4","type":"text","required":false,"source_attribute_id":"tpl_attr_llm_dp_cmd"},
            {"name":"recommended_version","display_name":"\63A8\8350\7248\672C","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_dp_ver"}
        ]},
        {"name":"sampling_parameter","display_name":"\91C7\6837\53C2\6570","aliases":["\91C7\6837\53C2\6570","\53C2\6570","Sampling"],"source_object_id":"tpl_obj_llm_sample","attributes":[
            {"name":"param_name","display_name":"\53C2\6570\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_llm_sp_name"},
            {"name":"recommended_value","display_name":"\63A8\8350\503C","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_sp_val"},
            {"name":"use_case","display_name":"\4F7F\7528\573A\666F","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_sp_case"}
        ]},
        {"name":"system_prompt","display_name":"\7CFB\7EDF\63D0\793A\8BCD","aliases":["\7CFB\7EDF\63D0\793A\8BCD","\63D0\793A\8BCD","System Prompt"],"source_object_id":"tpl_obj_llm_prompt","attributes":[
            {"name":"language","display_name":"\8BED\8A00","type":"enum","required":true,"source_attribute_id":"tpl_attr_llm_sy_lang"},
            {"name":"content","display_name":"\5185\5BB9","type":"text","required":true,"source_attribute_id":"tpl_attr_llm_sy_content"},
            {"name":"purpose","display_name":"\7528\9014","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_sy_purpose"}
        ]},
        {"name":"tool_use_practice","display_name":"\5DE5\5177\4F7F\7528\5B9E\8DF5","aliases":["\5DE5\5177\4F7F\7528\5B9E\8DF5","\5DE5\5177\8C03\7528","Tool Use"],"source_object_id":"tpl_obj_llm_tool","attributes":[
            {"name":"practice_name","display_name":"\5B9E\8DF5\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_llm_tl_name"},
            {"name":"description","display_name":"\63CF\8FF0","type":"text","required":false,"source_attribute_id":"tpl_attr_llm_tl_desc"},
            {"name":"requirement","display_name":"\8981\6C42","type":"text","required":false,"source_attribute_id":"tpl_attr_llm_tl_req"}
        ]},
        {"name":"research_org","display_name":"\7814\53D1\673A\6784","aliases":["\7814\53D1\673A\6784","\5F00\53D1\65B9","\5382\5546","\56E2\961F","Organization"],"source_object_id":"tpl_obj_llm_org","attributes":[
            {"name":"org_name","display_name":"\673A\6784\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_llm_org_name"},
            {"name":"org_type","display_name":"\673A\6784\7C7B\578B","type":"enum","required":false,"source_attribute_id":"tpl_attr_llm_org_type"},
            {"name":"contact","display_name":"\8054\7CFB\65B9\5F0F","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_org_contact"}
        ]},
        {"name":"technical_report","display_name":"\6280\672F\62A5\544A","aliases":["\6280\672F\62A5\544A","\8BBA\6587","Technical Report","Paper"],"source_object_id":"tpl_obj_llm_report","attributes":[
            {"name":"report_title","display_name":"\62A5\544A\6807\9898","type":"string","required":true,"source_attribute_id":"tpl_attr_llm_rp_title"},
            {"name":"arxiv_id","display_name":"arXiv\7F16\53F7","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_rp_arxiv"},
            {"name":"authors","display_name":"\4F5C\8005","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_rp_authors"},
            {"name":"year","display_name":"\5E74\4EFD","type":"number","required":false,"source_attribute_id":"tpl_attr_llm_rp_year"},
            {"name":"url","display_name":"\94FE\63A5","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_rp_url"},
            {"name":"primary_class","display_name":"\4E3B\9898\5206\7C7B","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_rp_class"}
        ]},
        {"name":"application_scenario","display_name":"\5E94\7528\573A\666F","aliases":["\5E94\7528\573A\666F","\4EFB\52A1\7C7B\578B","\573A\666F","Use Case"],"source_object_id":"tpl_obj_llm_scenario","attributes":[
            {"name":"scenario_name","display_name":"\573A\666F\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_llm_sc_name"},
            {"name":"scenario_type","display_name":"\573A\666F\7C7B\578B","type":"enum","required":false,"source_attribute_id":"tpl_attr_llm_sc_type"},
            {"name":"description","display_name":"\63CF\8FF0","type":"text","required":false,"source_attribute_id":"tpl_attr_llm_sc_desc"}
        ]},
        {"name":"software_framework","display_name":"\8F6F\4EF6\6846\67B6","aliases":["\8F6F\4EF6\6846\67B6","\6846\67B6","\5F15\64CE","Framework"],"source_object_id":"tpl_obj_llm_framework","attributes":[
            {"name":"framework_name","display_name":"\6846\67B6\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_llm_fw_name"},
            {"name":"framework_type","display_name":"\6846\67B6\7C7B\578B","type":"enum","required":false,"source_attribute_id":"tpl_attr_llm_fw_type"},
            {"name":"version","display_name":"\7248\672C","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_fw_version"},
            {"name":"purpose","display_name":"\7528\9014","type":"text","required":false,"source_attribute_id":"tpl_attr_llm_fw_purpose"}
        ]},
        {"name":"performance_metric","display_name":"\6027\80FD\6307\6807","aliases":["\6027\80FD\6307\6807","\6548\7387\6307\6807","Performance Metric"],"source_object_id":"tpl_obj_llm_perf","attributes":[
            {"name":"metric_name","display_name":"\6307\6807\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_llm_pf_name"},
            {"name":"metric_value","display_name":"\6307\6807\503C","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_pf_value"},
            {"name":"baseline","display_name":"\57FA\7EBF/\5BF9\6BD4","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_pf_baseline"},
            {"name":"description","display_name":"\63CF\8FF0","type":"text","required":false,"source_attribute_id":"tpl_attr_llm_pf_desc"}
        ]},
        {"name":"training_environment","display_name":"\8BAD\7EC3\73AF\5883","aliases":["\8BAD\7EC3\73AF\5883","\8BAD\7EC3\6570\636E","\73AF\5883","Environment"],"source_object_id":"tpl_obj_llm_env","attributes":[
            {"name":"env_name","display_name":"\73AF\5883\540D\79F0","type":"string","required":true,"source_attribute_id":"tpl_attr_llm_ev_name"},
            {"name":"env_type","display_name":"\73AF\5883\7C7B\578B","type":"enum","required":false,"source_attribute_id":"tpl_attr_llm_ev_type"},
            {"name":"scale","display_name":"\89C4\6A21","type":"string","required":false,"source_attribute_id":"tpl_attr_llm_ev_scale"},
            {"name":"description","display_name":"\63CF\8FF0","type":"text","required":false,"source_attribute_id":"tpl_attr_llm_ev_desc"}
        ]}
    ]'::jsonb,
    U&'[
        {"name":"MODEL_HAS_ARCHITECTURE","display_name":"\91C7\7528\67B6\6784","aliases":["\91C7\7528\67B6\6784","\4F7F\7528\67B6\6784"],"source":"ai_model","target":"model_architecture","source_relation_id":"tpl_rel_llm_md_arch","cardinality":"one_to_one"},
        {"name":"MODEL_TRAINED_WITH","display_name":"\8BAD\7EC3\914D\7F6E","aliases":["\8BAD\7EC3\914D\7F6E","\9884\8BAD\7EC3\914D\7F6E"],"source":"ai_model","target":"training_config","source_relation_id":"tpl_rel_llm_md_train","cardinality":"one_to_many"},
        {"name":"MODEL_EVALUATED_ON","display_name":"\8BC4\6D4B\7ED3\679C","aliases":["\8BC4\6D4B\7ED3\679C","\5F97\5206"],"source":"ai_model","target":"benchmark_result","source_relation_id":"tpl_rel_llm_md_result","cardinality":"one_to_many"},
        {"name":"RESULT_MEASURED_BY","display_name":"\6240\5C5E\57FA\51C6","aliases":["\6240\5C5E\57FA\51C6","\5BF9\5E94\57FA\51C6"],"source":"benchmark_result","target":"benchmark","source_relation_id":"tpl_rel_llm_rs_bench","cardinality":"many_to_one"},
        {"name":"RESULT_COMPARED_WITH","display_name":"\5BF9\6BD4\7ADE\54C1","aliases":["\5BF9\6BD4\7ADE\54C1","\7ADE\54C1\5BF9\6BD4"],"source":"benchmark_result","target":"competitor_model","source_relation_id":"tpl_rel_llm_rs_comp","cardinality":"many_to_many"},
        {"name":"MODEL_USES_TECHNIQUE","display_name":"\540E\8BAD\7EC3\6280\672F","aliases":["\540E\8BAD\7EC3\6280\672F","\4F7F\7528\6280\672F"],"source":"ai_model","target":"post_training_technique","source_relation_id":"tpl_rel_llm_md_pt","cardinality":"one_to_many"},
        {"name":"TECHNIQUE_USES_INFRA","display_name":"\4F9D\8D56\57FA\7840\8BBE\65BD","aliases":["\4F9D\8D56\57FA\7840\8BBE\65BD","\4F7F\7528\57FA\7840\8BBE\65BD"],"source":"post_training_technique","target":"rl_infrastructure","source_relation_id":"tpl_rel_llm_pt_infra","cardinality":"many_to_many"},
        {"name":"MODEL_DEPLOYED_WITH","display_name":"\90E8\7F72\914D\7F6E","aliases":["\90E8\7F72\914D\7F6E","\90E8\7F72"],"source":"ai_model","target":"deployment_config","source_relation_id":"tpl_rel_llm_md_deploy","cardinality":"one_to_many"},
        {"name":"DEPLOYMENT_HAS_SAMPLING_PARAM","display_name":"\91C7\6837\53C2\6570","aliases":["\91C7\6837\53C2\6570","\63A8\8350\53C2\6570"],"source":"deployment_config","target":"sampling_parameter","source_relation_id":"tpl_rel_llm_dp_sp","cardinality":"one_to_many"},
        {"name":"DEPLOYMENT_HAS_SYSTEM_PROMPT","display_name":"\7CFB\7EDF\63D0\793A\8BCD","aliases":["\7CFB\7EDF\63D0\793A\8BCD","\63D0\793A\8BCD"],"source":"deployment_config","target":"system_prompt","source_relation_id":"tpl_rel_llm_dp_sy","cardinality":"one_to_many"},
        {"name":"DEPLOYMENT_HAS_TOOL_PRACTICE","display_name":"\5DE5\5177\4F7F\7528\5B9E\8DF5","aliases":["\5DE5\5177\4F7F\7528\5B9E\8DF5","\5DE5\5177\5B9E\8DF5"],"source":"deployment_config","target":"tool_use_practice","source_relation_id":"tpl_rel_llm_dp_tl","cardinality":"one_to_many"},
        {"name":"MODEL_DEVELOPED_BY","display_name":"\7814\53D1\65B9","aliases":["\7814\53D1\65B9","\5F00\53D1\65B9","\7531...\7814\53D1"],"source":"ai_model","target":"research_org","source_relation_id":"tpl_rel_llm_md_org","cardinality":"many_to_one"},
        {"name":"ORG_PUBLISHES_REPORT","display_name":"\53D1\5E03\62A5\544A","aliases":["\53D1\5E03\62A5\544A","\53D1\8868"],"source":"research_org","target":"technical_report","source_relation_id":"tpl_rel_llm_org_rp","cardinality":"one_to_many"},
        {"name":"REPORT_DESCRIBES_MODEL","display_name":"\63CF\8FF0\6A21\578B","aliases":["\63CF\8FF0\6A21\578B","\4ECB\7ECD\6A21\578B"],"source":"technical_report","target":"ai_model","source_relation_id":"tpl_rel_llm_rp_md","cardinality":"one_to_one"},
        {"name":"MODEL_TARGETS_SCENARIO","display_name":"\9002\7528\573A\666F","aliases":["\9002\7528\573A\666F","\9762\5411\573A\666F"],"source":"ai_model","target":"application_scenario","source_relation_id":"tpl_rel_llm_md_sc","cardinality":"many_to_many"},
        {"name":"SAMPLING_PARAM_FOR_SCENARIO","display_name":"\9002\7528\573A\666F","aliases":["\9002\7528\573A\666F","\63A8\8350\573A\666F"],"source":"sampling_parameter","target":"application_scenario","source_relation_id":"tpl_rel_llm_sp_sc","cardinality":"many_to_many"},
        {"name":"DEPLOYMENT_USES_FRAMEWORK","display_name":"\4F7F\7528\6846\67B6","aliases":["\4F7F\7528\6846\67B6","\57FA\4E8E\6846\67B6"],"source":"deployment_config","target":"software_framework","source_relation_id":"tpl_rel_llm_dp_fw","cardinality":"many_to_many"},
        {"name":"INFRA_BUILT_ON_FRAMEWORK","display_name":"\57FA\4E8E\6846\67B6","aliases":["\57FA\4E8E\6846\67B6","\6784\5EFA\4E8E"],"source":"rl_infrastructure","target":"software_framework","source_relation_id":"tpl_rel_llm_if_fw","cardinality":"many_to_many"},
        {"name":"ARCHITECTURE_HAS_METRIC","display_name":"\6027\80FD\8868\73B0","aliases":["\6027\80FD\8868\73B0","\6548\7387\6307\6807"],"source":"model_architecture","target":"performance_metric","source_relation_id":"tpl_rel_llm_ar_pf","cardinality":"one_to_many"},
        {"name":"TECHNIQUE_USES_ENVIRONMENT","display_name":"\4F7F\7528\73AF\5883","aliases":["\4F7F\7528\73AF\5883","\4F9D\8D56\73AF\5883"],"source":"post_training_technique","target":"training_environment","source_relation_id":"tpl_rel_llm_pt_ev","cardinality":"many_to_many"}
    ]'::jsonb,
    '[
        {"type":"entity","severity":"warning"},
        {"type":"relation","severity":"warning","rule":"relation_source_target_must_exist"},
        {"type":"value","severity":"warning","rule":"score_range_consistency","fields":["score"],"expected_range":[0,100]}
    ]'::jsonb,
    U&'{
        "case_insensitive":true,
        "alias_merge":true,
        "model_name_aliases":{"MiMo-V2-Flash":["MiMo-V2-Flash","MiMo V2 Flash","MiMo-V2","mimo-v2-flash"],"MiMo-V2-Flash-Base":["MiMo-V2-Flash-Base","MiMo-V2-Flash Base","MiMo-V2 Base"]},
        "benchmark_category_aliases":{"Code Agent":["Code Agent","\4EE3\7801\667A\80FD\4F53"],"General Agent":["General Agent","\901A\7528\667A\80FD\4F53"],"Long Context":["Long Context","\957F\4E0A\4E0B\6587"]}
    }'::jsonb,
    U&'{
        "entity_types":[
            {"name":"ai_model","aliases":["AI\6A21\578B","\5927\6A21\578B","\8BED\8A00\6A21\578B","LLM","Model"],"attributes":[
                {"name":"model_name","type":"string","required":true},
                {"name":"model_family","type":"string","required":false},
                {"name":"model_type","type":"enum","required":false},
                {"name":"total_params","type":"string","required":false},
                {"name":"active_params","type":"string","required":false},
                {"name":"context_length","type":"string","required":false},
                {"name":"developer","type":"string","required":false},
                {"name":"release_date","type":"date","required":false},
                {"name":"huggingface_url","type":"string","required":false},
                {"name":"knowledge_cutoff","type":"string","required":false},
                {"name":"license_type","type":"string","required":false}
            ]},
            {"name":"model_architecture","aliases":["\6A21\578B\67B6\6784","\67B6\6784","Architecture"],"attributes":[
                {"name":"architecture_name","type":"string","required":true},
                {"name":"attention_type","type":"enum","required":false},
                {"name":"swa_ga_ratio","type":"string","required":false},
                {"name":"window_size","type":"number","required":false},
                {"name":"num_hybrid_blocks","type":"number","required":false},
                {"name":"swa_layers_per_block","type":"number","required":false},
                {"name":"ga_layers_per_block","type":"number","required":false},
                {"name":"sink_bias_enabled","type":"boolean","required":false},
                {"name":"mtp_enabled","type":"boolean","required":false},
                {"name":"mtp_params_per_block","type":"string","required":false},
                {"name":"mtp_structure","type":"string","required":false},
                {"name":"kv_cache_reduction","type":"string","required":false}
            ]},
            {"name":"training_config","aliases":["\8BAD\7EC3\914D\7F6E","\9884\8BAD\7EC3","Training"],"attributes":[
                {"name":"config_name","type":"string","required":true},
                {"name":"training_tokens","type":"string","required":false},
                {"name":"precision","type":"string","required":false},
                {"name":"native_seq_length","type":"number","required":false},
                {"name":"max_context_length","type":"number","required":false},
                {"name":"training_method","type":"text","required":false}
            ]},
            {"name":"benchmark","aliases":["\57FA\51C6\6D4B\8BD5","\8BC4\6D4B\57FA\51C6","Benchmark"],"attributes":[
                {"name":"benchmark_name","type":"string","required":true},
                {"name":"category","type":"enum","required":false},
                {"name":"setting","type":"string","required":false},
                {"name":"shot_count","type":"number","required":false},
                {"name":"description","type":"text","required":false}
            ]},
            {"name":"benchmark_result","aliases":["\8BC4\6D4B\7ED3\679C","\5F97\5206","Result","Score"],"attributes":[
                {"name":"result_id","type":"string","required":true},
                {"name":"model_name","type":"string","required":true},
                {"name":"benchmark_name","type":"string","required":true},
                {"name":"score","type":"number","required":true},
                {"name":"setting","type":"string","required":false},
                {"name":"length","type":"string","required":false},
                {"name":"eval_phase","type":"enum","required":false}
            ]},
            {"name":"competitor_model","aliases":["\7ADE\54C1\6A21\578B","\5BF9\6BD4\6A21\578B","\7ADE\54C1","Competitor"],"attributes":[
                {"name":"model_name","type":"string","required":true},
                {"name":"developer","type":"string","required":false},
                {"name":"total_params","type":"string","required":false},
                {"name":"active_params","type":"string","required":false}
            ]},
            {"name":"post_training_technique","aliases":["\540E\8BAD\7EC3\6280\672F","\8BAD\7EC3\6280\672F","Post-Training"],"attributes":[
                {"name":"technique_name","type":"string","required":true},
                {"name":"technique_type","type":"enum","required":false},
                {"name":"description","type":"text","required":false},
                {"name":"key_features","type":"text","required":false}
            ]},
            {"name":"rl_infrastructure","aliases":["RL\57FA\7840\8BBE\65BD","\8BAD\7EC3\57FA\7840\8BBE\65BD","Infrastructure"],"attributes":[
                {"name":"component_name","type":"string","required":true},
                {"name":"description","type":"text","required":false},
                {"name":"purpose","type":"text","required":false}
            ]},
            {"name":"deployment_config","aliases":["\90E8\7F72\914D\7F6E","\90E8\7F72","Deployment"],"attributes":[
                {"name":"config_name","type":"string","required":true},
                {"name":"framework","type":"string","required":false},
                {"name":"precision","type":"string","required":false},
                {"name":"server_command","type":"text","required":false},
                {"name":"recommended_version","type":"string","required":false}
            ]},
            {"name":"sampling_parameter","aliases":["\91C7\6837\53C2\6570","\53C2\6570","Sampling"],"attributes":[
                {"name":"param_name","type":"string","required":true},
                {"name":"recommended_value","type":"string","required":false},
                {"name":"use_case","type":"string","required":false}
            ]},
            {"name":"system_prompt","aliases":["\7CFB\7EDF\63D0\793A\8BCD","\63D0\793A\8BCD","System Prompt"],"attributes":[
                {"name":"language","type":"enum","required":true},
                {"name":"content","type":"text","required":true},
                {"name":"purpose","type":"string","required":false}
            ]},
            {"name":"tool_use_practice","aliases":["\5DE5\5177\4F7F\7528\5B9E\8DF5","\5DE5\5177\8C03\7528","Tool Use"],"attributes":[
                {"name":"practice_name","type":"string","required":true},
                {"name":"description","type":"text","required":false},
                {"name":"requirement","type":"text","required":false}
            ]},
            {"name":"research_org","aliases":["\7814\53D1\673A\6784","\5F00\53D1\65B9","\5382\5546","\56E2\961F","Organization"],"attributes":[
                {"name":"org_name","type":"string","required":true},
                {"name":"org_type","type":"enum","required":false},
                {"name":"contact","type":"string","required":false}
            ]},
            {"name":"technical_report","aliases":["\6280\672F\62A5\544A","\8BBA\6587","Technical Report","Paper"],"attributes":[
                {"name":"report_title","type":"string","required":true},
                {"name":"arxiv_id","type":"string","required":false},
                {"name":"authors","type":"string","required":false},
                {"name":"year","type":"number","required":false},
                {"name":"url","type":"string","required":false},
                {"name":"primary_class","type":"string","required":false}
            ]},
            {"name":"application_scenario","aliases":["\5E94\7528\573A\666F","\4EFB\52A1\7C7B\578B","\573A\666F","Use Case"],"attributes":[
                {"name":"scenario_name","type":"string","required":true},
                {"name":"scenario_type","type":"enum","required":false},
                {"name":"description","type":"text","required":false}
            ]},
            {"name":"software_framework","aliases":["\8F6F\4EF6\6846\67B6","\6846\67B6","\5F15\64CE","Framework"],"attributes":[
                {"name":"framework_name","type":"string","required":true},
                {"name":"framework_type","type":"enum","required":false},
                {"name":"version","type":"string","required":false},
                {"name":"purpose","type":"text","required":false}
            ]},
            {"name":"performance_metric","aliases":["\6027\80FD\6307\6807","\6548\7387\6307\6807","Performance Metric"],"attributes":[
                {"name":"metric_name","type":"string","required":true},
                {"name":"metric_value","type":"string","required":false},
                {"name":"baseline","type":"string","required":false},
                {"name":"description","type":"text","required":false}
            ]},
            {"name":"training_environment","aliases":["\8BAD\7EC3\73AF\5883","\8BAD\7EC3\6570\636E","\73AF\5883","Environment"],"attributes":[
                {"name":"env_name","type":"string","required":true},
                {"name":"env_type","type":"enum","required":false},
                {"name":"scale","type":"string","required":false},
                {"name":"description","type":"text","required":false}
            ]}
        ],
        "relation_types":[
            {"name":"MODEL_HAS_ARCHITECTURE","source":"ai_model","target":"model_architecture"},
            {"name":"MODEL_TRAINED_WITH","source":"ai_model","target":"training_config"},
            {"name":"MODEL_EVALUATED_ON","source":"ai_model","target":"benchmark_result"},
            {"name":"RESULT_MEASURED_BY","source":"benchmark_result","target":"benchmark"},
            {"name":"RESULT_COMPARED_WITH","source":"benchmark_result","target":"competitor_model"},
            {"name":"MODEL_USES_TECHNIQUE","source":"ai_model","target":"post_training_technique"},
            {"name":"TECHNIQUE_USES_INFRA","source":"post_training_technique","target":"rl_infrastructure"},
            {"name":"MODEL_DEPLOYED_WITH","source":"ai_model","target":"deployment_config"},
            {"name":"DEPLOYMENT_HAS_SAMPLING_PARAM","source":"deployment_config","target":"sampling_parameter"},
            {"name":"DEPLOYMENT_HAS_SYSTEM_PROMPT","source":"deployment_config","target":"system_prompt"},
            {"name":"DEPLOYMENT_HAS_TOOL_PRACTICE","source":"deployment_config","target":"tool_use_practice"},
            {"name":"MODEL_DEVELOPED_BY","source":"ai_model","target":"research_org"},
            {"name":"ORG_PUBLISHES_REPORT","source":"research_org","target":"technical_report"},
            {"name":"REPORT_DESCRIBES_MODEL","source":"technical_report","target":"ai_model"},
            {"name":"MODEL_TARGETS_SCENARIO","source":"ai_model","target":"application_scenario"},
            {"name":"SAMPLING_PARAM_FOR_SCENARIO","source":"sampling_parameter","target":"application_scenario"},
            {"name":"DEPLOYMENT_USES_FRAMEWORK","source":"deployment_config","target":"software_framework"},
            {"name":"INFRA_BUILT_ON_FRAMEWORK","source":"rl_infrastructure","target":"software_framework"},
            {"name":"ARCHITECTURE_HAS_METRIC","source":"model_architecture","target":"performance_metric"},
            {"name":"TECHNIQUE_USES_ENVIRONMENT","source":"post_training_technique","target":"training_environment"}
        ]
    }'::jsonb,
    'active', '2026-06-22T00:00:00+00'::timestamptz
) ON CONFLICT (tenant_id, knowledge_base_id) DO NOTHING;







INSERT INTO business_domain.prompt_templates (id, tenant_id, name, category, scope, description, status, current_version, versions_json, created_by, created_at, updated_at)
VALUES ('1a1e4899eaad48ae822254aa41b47d13', 'tenant_jonex_demo', U&'\5408\540C\6761\6B3E\5408\89C4\5BA1\67E5 (\526F\672C)', U&'\5408\540C\5BA1\67E5', 'domain', U&'\8BC6\522B\5408\540C\4E2D\7684\98CE\9669\6761\6B3E\4E0E\5408\89C4\95EE\9898，\7ED9\51FA\4FEE\6539\5EFA\8BAE。', 'enabled', '1.1', U&'[{"remark": "\5185\5BB9\66F4\65B0", "content": "\8BF7\4F5C\4E3A\6CD5\5F8B\5408\89C4\4E13\5BB6\5BA1\67E5\4EE5\4E0B\5408\540C\6761\6B3E，\8F93\51FA：\\\\n- \98CE\9669\6761\6B3E\6E05\5355（\6807\6CE8\4F4D\7F6E）\\\\n- \5408\89C4\95EE\9898\8BF4\660E\\\\n- \4FEE\6539\5EFA\8BAE\\\\n\\\\\8428\82ACn\5408\540C\6587\672C：{{\5408\540C\5185\5BB9}}\963F\8870daWnQWD ADFWE \5427", "version": "1.1", "updated_at": "2026-07-07 10:47", "updated_by": "\7CFB\7EDF\7528\6237"}, {"remark": "\4ECE\9886\57DF\6A21\677F\590D\5236", "content": "\8BF7\4F5C\4E3A\6CD5\5F8B\5408\89C4\4E13\5BB6\5BA1\67E5\4EE5\4E0B\5408\540C\6761\6B3E，\8F93\51FA：\\\\n- \98CE\9669\6761\6B3E\6E05\5355（\6807\6CE8\4F4D\7F6E）\\\\n- \5408\89C4\95EE\9898\8BF4\660E\\\\n- \4FEE\6539\5EFA\8BAE\\\\n\\\\\8428\82ACn\5408\540C\6587\672C：{{\5408\540C\5185\5BB9}}\963F\8870daWnQWD ADFWE ", "version": "1.0", "updated_at": "2026-07-07 10:46", "updated_by": "\7CFB\7EDF\7528\6237"}]'::jsonb, U&'\7CFB\7EDF\7528\6237', '2026-07-07 02:46:17', '2026-07-07 02:47:04')
ON CONFLICT (id) DO NOTHING;

INSERT INTO business_domain.prompt_templates (id, tenant_id, name, category, scope, description, status, current_version, versions_json, created_by, created_at, updated_at)
VALUES ('seed_pt_dom_contract', 'tenant_jonex_demo', U&'\5408\540C\6761\6B3E\5408\89C4\5BA1\67E5', U&'\5408\540C\5BA1\67E5', 'domain', U&'\8BC6\522B\5408\540C\4E2D\7684\98CE\9669\6761\6B3E\4E0E\5408\89C4\95EE\9898，\7ED9\51FA\4FEE\6539\5EFA\8BAE。', 'enabled', '1.3', U&'[{"remark": "TIANJAINEIRONG", "content": "\8BF7\4F5C\4E3A\6CD5\5F8B\5408\89C4\4E13\5BB6\5BA1\67E5\4EE5\4E0B\5408\540C\6761\6B3E，\8F93\51FA：\\\\n- \98CE\9669\6761\6B3E\6E05\5355（\6807\6CE8\4F4D\7F6E）\\\\n- \5408\89C4\95EE\9898\8BF4\660E\\\\n- \4FEE\6539\5EFA\8BAE\\\\n\\\\\8428\82ACn\5408\540C\6587\672C：{{\5408\540C\5185\5BB9}}\963F\8870daWnQWD ADFWE ", "version": "1.3", "updated_at": "2026-07-07 10:27", "updated_by": "\7CFB\7EDF\7528\6237"}, {"remark": "\5565\5730\65B9", "content": "\8BF7\4F5C\4E3A\6CD5\5F8B\5408\89C4\4E13\5BB6\5BA1\67E5\4EE5\4E0B\5408\540C\6761\6B3E，\8F93\51FA：\\\\n- \98CE\9669\6761\6B3E\6E05\5355（\6807\6CE8\4F4D\7F6E）\\\\n- \5408\89C4\95EE\9898\8BF4\660E\\\\n- \4FEE\6539\5EFA\8BAE\\\\n\\\\\8428\82ACn\5408\540C\6587\672C：{{\5408\540C\5185\5BB9}}", "version": "1.2", "updated_at": "2026-07-07 10:26", "updated_by": "\7CFB\7EDF\7528\6237"}, {"remark": "?? prompt_text ????", "content": "\8BF7\4F5C\4E3A\6CD5\5F8B\5408\89C4\4E13\5BB6\5BA1\67E5\4EE5\4E0B\5408\540C\6761\6B3E，\8F93\51FA：\\\\n- \98CE\9669\6761\6B3E\6E05\5355（\6807\6CE8\4F4D\7F6E）\\\\n- \5408\89C4\95EE\9898\8BF4\660E\\\\n- \4FEE\6539\5EFA\8BAE\\\\n\\\\n\5408\540C\6587\672C：{{\5408\540C\5185\5BB9}}", "version": "1.1", "updated_at": "2026-07-06 18:42", "updated_by": "????"}]'::jsonb, '????', '2026-07-06 18:42:58', '2026-07-07 02:27:40')
ON CONFLICT (id) DO NOTHING;

INSERT INTO business_domain.prompt_templates (id, tenant_id, name, category, scope, description, status, current_version, versions_json, created_by, created_at, updated_at)
VALUES ('seed_pt_dom_report', 'tenant_jonex_demo', U&'\6570\636E\62A5\8868\89E3\8BFB', U&'\6587\6863\5904\7406', 'domain', U&'\57FA\4E8E\6570\636E\62A5\8868\81EA\52A8\751F\6210\4E1A\52A1\6D1E\5BDF\4E0E\8D8B\52BF\89E3\8BFB。', 'enabled', '1.2', U&'[{"remark": "\6DFB\52A0\5185\5BB9", "content": "\8BF7\57FA\4E8E\4EE5\4E0B\62A5\8868\6570\636E，\751F\6210\4E1A\52A1\89E3\8BFB\62A5\544A：\\\\n1. \5173\952E\6307\6807\540C\6BD4/\73AF\6BD4\53D8\5316；\\\\n2. \5F02\5E38\6CE2\52A8\5F52\56E0；\\\\n3. \8D8B\52BF\9884\6D4B\4E0E\5EFA\8BAE。\\\\n\\\\n\62A5\8868\6570\636E：\963F\8870\5565\5730\65B9\963F\5FB7\6316\65B9\963F\65AF\8482\82AC\989D\5916", "version": "1.2", "updated_at": "2026-07-07 10:27", "updated_by": "\7CFB\7EDF\7528\6237"}, {"remark": "\5185\5BB9\66F4\65B0", "content": "\8BF7\57FA\4E8E\4EE5\4E0B\62A5\8868\6570\636E，\751F\6210\4E1A\52A1\89E3\8BFB\62A5\544A：\\\\n1. \5173\952E\6307\6807\540C\6BD4/\73AF\6BD4\53D8\5316；\\\\n2. \5F02\5E38\6CE2\52A8\5F52\56E0；\\\\n3. \8D8B\52BF\9884\6D4B\4E0E\5EFA\8BAE。\\\\n\\\\n\62A5\8868\6570\636E：", "version": "1.1", "updated_at": "2026-07-07 10:25", "updated_by": "\7CFB\7EDF\7528\6237"}, {"remark": "?? prompt_text ????", "content": "\8BF7\57FA\4E8E\4EE5\4E0B\62A5\8868\6570\636E，\751F\6210\4E1A\52A1\89E3\8BFB\62A5\544A：\\\\n1. \5173\952E\6307\6807\540C\6BD4/\73AF\6BD4\53D8\5316；\\\\n2. \5F02\5E38\6CE2\52A8\5F52\56E0；\\\\n3. \8D8B\52BF\9884\6D4B\4E0E\5EFA\8BAE。\\\\n\\\\n\62A5\8868\6570\636E：{{\62A5\8868\6570\636E}}", "version": "1.0", "updated_at": "2026-07-06 18:42", "updated_by": "????"}]'::jsonb, '????', '2026-07-06 18:42:58', '2026-07-07 02:27:17')
ON CONFLICT (id) DO NOTHING;

INSERT INTO business_domain.prompt_templates (id, tenant_id, name, category, scope, description, status, current_version, versions_json, created_by, created_at, updated_at)
VALUES ('seed_pt_sys_docsum', NULL, U&'\6587\6863\6458\8981\751F\6210', U&'\6587\6863\5904\7406', 'system', U&'\5BF9\957F\6587\6863\8FDB\884C\81EA\52A8\6458\8981，\8F93\51FA\6838\5FC3\89C2\70B9\4E0E\5173\952E\4FE1\606F。', 'enabled', '1.1', U&'[{"remark": "?? prompt_text ????", "content": "\8BF7\9605\8BFB\4EE5\4E0B\6587\6863，\751F\6210\4E00\6BB5\4E0D\8D85\8FC7 200 \5B57\7684\6458\8981，\5305\542B：\\\\n- \6838\5FC3\4E3B\9898\\\\n- \5173\952E\8BBA\70B9（3 \6761）\\\\n- \7ED3\8BBA\5EFA\8BAE\\\\n\\\\n\6587\6863\5185\5BB9：{{\6587\6863\5185\5BB9}}", "version": "1.1", "updated_at": "2026-07-06 18:42", "updated_by": "????"}]'::jsonb, '????', '2026-07-06 18:42:58', '2026-07-06 18:42:58')
ON CONFLICT (id) DO NOTHING;

INSERT INTO business_domain.prompt_templates (id, tenant_id, name, category, scope, description, status, current_version, versions_json, created_by, created_at, updated_at)
VALUES ('seed_pt_sys_email', NULL, U&'\90AE\4EF6\667A\80FD\56DE\590D', U&'\901A\7528\95EE\7B54', 'system', U&'\6839\636E\90AE\4EF6\5185\5BB9\751F\6210\4E13\4E1A、\5F97\4F53\7684\56DE\590D\8349\7A3F。', 'enabled', '1.0', U&'[{"remark": "?? prompt_text ????", "content": "\8BF7\6839\636E\6536\5230\7684\90AE\4EF6\5185\5BB9，\64B0\5199\4E00\5C01\5F97\4F53\7684\56DE\590D\90AE\4EF6，\8981\6C42：\\\\n- \8BED\6C14\4E13\4E1A、\793C\8C8C；\\\\n- \8986\76D6\5BF9\65B9\6240\6709\95EE\9898；\\\\n- 200 \5B57\4EE5\5185。\\\\n\\\\n\6536\4EF6\90AE\4EF6：{{\90AE\4EF6\5185\5BB9}}", "version": "1.0", "updated_at": "2026-07-06 18:42", "updated_by": "????"}]'::jsonb, '????', '2026-07-06 18:42:58', '2026-07-06 18:42:58')
ON CONFLICT (id) DO NOTHING;

INSERT INTO business_domain.prompt_templates (id, tenant_id, name, category, scope, description, status, current_version, versions_json, created_by, created_at, updated_at)
VALUES ('seed_pt_sys_qa', NULL, U&'\667A\80FD\95EE\7B54\52A9\624B', U&'\901A\7528\95EE\7B54', 'system', U&'\9762\5411\901A\7528\77E5\8BC6\95EE\7B54\573A\666F，\7ED3\5408\4E0A\4E0B\6587\7ED9\51FA\51C6\786E、\7ED3\6784\5316\7684\56DE\7B54。', 'enabled', '1.2', U&'[{"remark": "?? prompt_text ????", "content": "\4F60\662F\4E00\4E2A\4E13\4E1A、\4E25\8C28\7684\77E5\8BC6\95EE\7B54\52A9\624B。\8BF7\6839\636E\4EE5\4E0B\4E0A\4E0B\6587\56DE\7B54\7528\6237\95EE\9898，\8981\6C42：\\\\n1. \4EC5\4F9D\636E\7ED9\5B9A\4E0A\4E0B\6587\4F5C\7B54，\4E0D\7F16\9020\4FE1\606F；\\\\n2. \7B54\6848\7ED3\6784\5316、\6761\7406\6E05\6670；\\\\n3. \5982\4E0A\4E0B\6587\4E0D\8DB3，\8BF7\5982\5B9E\8BF4\660E。\\\\n\\\\n\4E0A\4E0B\6587：{{\68C0\7D22\5185\5BB9}}\\\\n\7528\6237\95EE\9898：{{\7528\6237\95EE\9898}}", "version": "1.2", "updated_at": "2026-07-06 18:42", "updated_by": "????"}]'::jsonb, '????', '2026-07-06 18:42:58', '2026-07-06 18:42:58')
ON CONFLICT (id) DO NOTHING;
