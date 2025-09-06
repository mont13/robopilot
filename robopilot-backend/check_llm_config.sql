-- Check LLM Configuration Query
-- Run this to see what's in your llm_connections table

SELECT
    id,
    name,
    provider,
    model_name,
    base_url,
    CASE
        WHEN api_key IS NOT NULL THEN CONCAT('Present (', LENGTH(api_key), ' chars)')
        ELSE 'Not set'
    END as api_key_status,
    api_version,
    is_active,
    created_at,
    updated_at
FROM llm_connections
ORDER BY is_active DESC, updated_at DESC;

-- Check if there's an active connection
SELECT
    'Active Connection Status' as check_type,
    CASE
        WHEN COUNT(*) = 0 THEN 'NO ACTIVE CONNECTION FOUND!'
        WHEN COUNT(*) > 1 THEN 'MULTIPLE ACTIVE CONNECTIONS (ERROR!)'
        ELSE 'OK - One active connection found'
    END as status,
    COUNT(*) as active_count
FROM llm_connections
WHERE is_active = true;

-- Show the active connection details
SELECT
    'ACTIVE CONNECTION DETAILS' as info,
    name,
    provider,
    model_name,
    base_url,
    CASE
        WHEN api_key IS NOT NULL THEN 'API Key Present'
        ELSE 'No API Key'
    END as api_key_info,
    api_version
FROM llm_connections
WHERE is_active = true;

-- Check for suspicious model names
SELECT
    'SUSPICIOUS MODEL NAMES' as warning,
    name,
    model_name,
    provider,
    CASE
        WHEN model_name IN ('0.6b', '1.0', '2.0', '0.5', '1.5') THEN 'SUSPICIOUS - This looks like a version number, not a model name!'
        WHEN model_name LIKE '%.%b' THEN 'SUSPICIOUS - Ends with .Xb pattern'
        WHEN LENGTH(model_name) < 3 THEN 'SUSPICIOUS - Very short model name'
        ELSE 'OK'
    END as assessment
FROM llm_connections;
