#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create necessary schemas
    CREATE SCHEMA IF NOT EXISTS public;
    CREATE SCHEMA IF NOT EXISTS auth;
    CREATE SCHEMA IF NOT EXISTS _analytics;
    CREATE SCHEMA IF NOT EXISTS _realtime;

    -- Create schema_migrations table
    CREATE TABLE IF NOT EXISTS public.schema_migrations (
        version bigint PRIMARY KEY,
        inserted_at timestamp without time zone NOT NULL DEFAULT now()
    );

    -- Create sources table
    CREATE TABLE IF NOT EXISTS public.sources (
        id SERIAL PRIMARY KEY,
        name TEXT,
        token TEXT,
        public_token TEXT,
        favorite BOOLEAN,
        bigquery_table_ttl INTEGER,
        api_quota INTEGER,
        webhook_notification_url TEXT,
        slack_hook_url TEXT,
        bq_table_partition_type TEXT,
        custom_event_message_keys TEXT[],
        log_events_updated_at TIMESTAMP,
        notifications_every INTEGER,
        lock_schema BOOLEAN,
        validate_schema BOOLEAN,
        drop_lql_filters TEXT[],
        drop_lql_string TEXT,
        v2_pipeline BOOLEAN,
        suggested_keys TEXT[],
        user_id UUID,
        notifications JSONB,
        inserted_at TIMESTAMP,
        updated_at TIMESTAMP
    );

    -- Create system_metrics table
    CREATE TABLE IF NOT EXISTS public.system_metrics (
        id SERIAL PRIMARY KEY,
        all_logs_logged BIGINT,
        node TEXT,
        inserted_at TIMESTAMP,
        updated_at TIMESTAMP
    );

    -- Enable logical replication
    ALTER SYSTEM SET wal_level = logical;

    -- Create publication for logical replication
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'logflare_pub') THEN
            CREATE PUBLICATION logflare_pub FOR ALL TABLES;
        END IF;
    END
    \$\$;

    -- Grant necessary permissions
    GRANT ALL PRIVILEGES ON SCHEMA public TO ${POSTGRES_USER};
    GRANT ALL PRIVILEGES ON SCHEMA auth TO ${POSTGRES_USER};
    GRANT ALL PRIVILEGES ON SCHEMA _analytics TO ${POSTGRES_USER};
    GRANT ALL PRIVILEGES ON SCHEMA _realtime TO ${POSTGRES_USER};
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ${POSTGRES_USER};
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA auth TO ${POSTGRES_USER};
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA _analytics TO ${POSTGRES_USER};
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA _realtime TO ${POSTGRES_USER};
EOSQL
echo "Database has been initialized."