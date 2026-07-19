







ALTER TABLE knowledge_base.knowledge_documents
    ADD COLUMN IF NOT EXISTS storage_backend VARCHAR(16) NOT NULL DEFAULT 'local';

ALTER TABLE knowledge_base.knowledge_documents
    ADD COLUMN IF NOT EXISTS storage_key VARCHAR(1024);
