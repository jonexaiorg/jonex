















\set tenant '1'
\set kb     '1'


SELECT ontology_status, count(*)
FROM knowledge_base.knowledge_documents
WHERE tenant_id = :'tenant'
  AND knowledge_base_id = :'kb'
  AND status = 'ready'
  AND is_deleted = 0
GROUP BY ontology_status;


UPDATE knowledge_base.knowledge_documents
SET ontology_status    = 'pending',
    ontology_retry_count = 0,
    ontology_error     = NULL,
    rag_task_id        = NULL,
    updated_at         = now()
WHERE tenant_id = :'tenant'
  AND knowledge_base_id = :'kb'
  AND status = 'ready'
  AND is_deleted = 0;


SELECT ontology_status, count(*)
FROM knowledge_base.knowledge_documents
WHERE tenant_id = :'tenant'
  AND knowledge_base_id = :'kb'
  AND is_deleted = 0
GROUP BY ontology_status;
