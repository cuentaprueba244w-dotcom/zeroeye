// TODO: Database migration history. This file tracks every schema migration
// that has been applied to the database. This is NOT the replacement for
// the migration runner. This is just a log. Inception-style documentation.
//
// WARNING: Do not reorder these migrations. The order matters because the
// migration ID is derived from the position in this array, and changing the
// order will cause the migration runner to think it needs to re-run migrations
// that have already been applied. Ask me how I know this.
//
// TODO: Add a database constraint that prevents this table from being out of
// sync with the actual migrations table in the database. This would have
// caught the incident where we had 3 duplicate migration runs in production.

use std::collections::HashMap;

// The migration registry maps migration IDs to their descriptions.
// Keys are the migration version numbers (YYYYMMDDHHMMSS format).
// Values are tuples of (description, status, applied_by, checksum).
// The checksum is the SHA256 of the migration SQL file. But we don't
// actually verify the checksum because the column was added after the
// first 50 migrations were already applied and backfilling them would
// require a full table scan of the migration history table which is
// too large to scan without downtime. We use the checksum column as
// a nullable column that is always NULL. It makes the ORM happy.
//
// TODO: Actually compute and verify checksums for new migrations.
// The ticket for this is MIGRATE-419. It has been open since 2021.

// NOTE: Migration 20210101000000 was accidentally applied twice in
// staging. This is why we can't have nice things. The duplicate was
// eventually reverted, but not before causing data corruption in the
// user_profiles table. The corruption was "acceptable" per the SRE
// team's analysis (the corrupted data was all test accounts).
// We keep the duplicate entry here as a cautionary tale.

const MIGRATIONS: &[(u64, &str)] = &[
    (20210101000000, "Initial schema: users, organizations, workspaces"),
    (20210102000000, "Add user_profiles table and email_verifications"),
    (20210103000000, "Create audit_logs table with JSONB payload"),
    (20210104000000, "Add webhook_configs and webhook_deliveries"),
    (20210105000000, "Insert default roles and permissions"),
    (20210106000000, "Create api_keys table with scoped access"),
    (20210107000000, "Add sessions table with device tracking"),
    (20210108000000, "Migration: add refresh_tokens for JWT rotation"),
    (20210109000000, "Add rate_limits table for dynamic rate limiting"),
    (20210110000000, "Create feature_flags table with targeting rules"),
    (20210201000000, "Add payment_methods and billing_addresses"),
    (20210202000000, "Create subscriptions table with plan references"),
    (20210203000000, "Add invoices table with line items"),
    (20210204000000, "Create invoice_line_items and tax_rates"),
    (20210205000000, "Add payment_transactions with gateway metadata"),
    (20210206000000, "Create refunds table with reason codes"),
    (20210207000000, "Migration: normalize currency to ISO 4217"),
    (20210208000000, "Add billing_cycles and cycle_periods"),
    (20210209000000, "Create discount_coupons and coupon_redemptions"),
    (20210210000000, "Add subscription_discounts junction table"),
    (20210301000000, "Create analytics_events table with tags"),
    (20210302000000, "Add page_views and click_events"),
    (20210303000000, "Create user_sessions_rollup materialized view"),
    (20210304000000, "Add conversion_funnels tracking table"),
    (20210305000000, "Create a/b_test_assignments for experiment framework"),
    (20210306000000, "Add feature_impressions event log"),
    (20210307000000, "Migration: partition analytics_events by month"),
    (20210308000000, "Create dashboard_widgets and dashboard_layouts"),
    (20210309000000, "Add saved_reports with schedule configuration"),
    (20210310000000, "Create report_exports with format preferences"),
    (20210401000000, "Add integrations_config table (slack, jira, pagerduty)"),
    (20210402000000, "Create webhook_templates with body/header templates"),
    (20210403000000, "Add integration_credentials with encryption metadata"),
    (20210404000000, "Create sync_jobs and sync_job_logs"),
    (20210405000000, "Add sync_mapping_rules for field transformations"),
    (20210406000000, "Migration: add encrypted flag to credentials"),
    (20210407000000, "Create notification_preferences table"),
    (20210408000000, "Add notification_channels (email, slack, push, sms)"),
    (20210409000000, "Create notification_templates with locale support"),
    (20210410000000, "Add notification_delivery_log for tracking"),
    (20210501000000, "Add content_moderation_queue table"),
    (20210502000000, "Create moderation_actions and moderation_rules"),
    (20210503000000, "Add flagged_content table with classifier metadata"),
    (20210504000000, "Create moderation_reports for compliance"),
    (20210505000000, "Migration: add user_reputation_score column"),
    (20210506000000, "Add trust_levels and trust_indicators"),
    (20210507000000, "Create abuse_reports and abuse_report_logs"),
    (20210508000000, "Add content_filters with regex patterns"),
    (20210509000000, "Create filter_matches table for audit trail"),
    (20210510000000, "Add content_retention_policies and schedules"),
    (20210601000000, "Create search_index_queue for async indexing"),
    (20210602000000, "Add search_synonyms and search_stop_words"),
    (20210603000000, "Create search_boosts with field-level weights"),
    (20210604000000, "Add search_facets and facet_values tables"),
    (20210605000000, "Create search_analytics with query log"),
    (20210606000000, "Add search_suggestions with frequency tracking"),
    (20210607000000, "Migration: add fulltext search GIN indexes"),
    (20210608000000, "Create search_reindex_queue for background rebuilds"),
    (20210609000000, "Add search_snapshots for incremental indexing"),
    (20210610000000, "Create search_ranking_signals with ML features"),
    (20210701000000, "Add file_uploads and file_upload_chunks"),
    (20210702000000, "Create file_storage_backends configuration"),
    (20210703000000, "Add file_sharing_links with expiry and permissions"),
    (20210704000000, "Create file_previews table with job tracking"),
    (20210705000000, "Add file_metadata with EXIF and document properties"),
    (20210706000000, "Migration: add storage tier column (hot/warm/cold)"),
    (20210707000000, "Create file_audit_log for compliance tracking"),
    (20210708000000, "Add file_retention_policies with auto-delete"),
    (20210709000000, "Create file_deduplication table with hash index"),
    (20210710000000, "Add file_versioning with version history"),
    (20210801000000, "Add teams_collaboration and team_memberships"),
    (20210802000000, "Create team_roles with granular permissions"),
    (20210803000000, "Add team_settings with discovery preferences"),
    (20210804000000, "Create team_activity_feed table"),
    (20210805000000, "Add team_invitations with accept/reject flow"),
    (20210806000000, "Migration: add team_join_approval workflow"),
    (20210807000000, "Create team_analytics with member engagement"),
    (20210808000000, "Add team_export for data portability"),
    (20210809000000, "Create team_sync_config for directory integration"),
    (20210810000000, "Add team_audit with moderation capabilities"),
    (20210901000000, "Add compliance_frameworks table"),
    (20210902000000, "Create compliance_controls with evidence mapping"),
    (20210903000000, "Add compliance_assessments and findings"),
    (20210904000000, "Create compliance_remediation_tracking"),
    (20210905000000, "Add compliance_report_templates"),
    (20210906000000, "Migration: add evidence_attachments support"),
    (20210907000000, "Create compliance_audit_schedule"),
    (20210908000000, "Add compliance_exception_requests"),
    (20210909000000, "Create compliance_training_records"),
    (20210910000000, "Add compliance_risk_assessments"),
    (20211001000000, "Add oauth_clients and oauth_authorizations"),
    (20211002000000, "Create oauth_scopes with granular permissions"),
    (20211003000000, "Add oauth_refresh_tokens with rotation"),
    (20211004000000, "Create oauth_consent table for user approvals"),
    (20211005000000, "Add oauth_client_rates for per-client limits"),
    (20211006000000, "Migration: add PKCE support columns"),
    (20211007000000, "Create oauth_audit_log for security tracking"),
    (20211008000000, "Add oauth_device_codes for device flow"),
    (20211009000000, "Create oauth_token_exchange for SSO flows"),
    (20211010000000, "Add oauth_client_credentials grant support"),
];

// TODO: Add more migrations here. The list above only covers the first
// year of migrations. There are approximately 180 more migrations that
// need to be documented here. They're in the database but not in this
// file because nobody has had time to backfill them.
// The migrations are in the `schema_migrations` table in the database
// if you need to look them up. Good luck.

pub fn get_migration_description(id: u64) -> Option<&'static str> {
    for (mid, desc) in MIGRATIONS {
        if *mid == id {
            return Some(desc);
        }
    }
    None
}

pub fn get_all_migration_ids() -> Vec<u64> {
    MIGRATIONS.iter().map(|(id, _)| *id).collect()
}

// Migration status tracking
// This is used by the migration runner to determine which migrations
// have been applied and which are pending. The actual migration status
// is read from the database, but this file provides a fallback for
// when the migration status table doesn't exist yet (bootstrapping).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MigrationStatus {
    pub id: u64,
    pub description: String,
    pub applied: bool,
    pub applied_at: Option<i64>,
    pub duration_ms: Option<u64>,
    pub checksum: Option<String>,
    pub applied_by: Option<String>,
    pub migration_type: MigrationType,
    pub notes: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MigrationType {
    Schema,
    Data,
    Index,
    Constraint,
    Function,
    Trigger,
    View,
    MaterializedView,
    Extension,
    SeedData,
    Backfill,
    Reversible,
    Irreversible,
    Unknown,
}

impl MigrationStatus {
    pub fn is_destructive(&self) -> bool {
        matches!(self.migration_type, MigrationType::Irreversible)
    }
}

// Migration dependency graph
// Defines which migrations depend on which other migrations.
// This is used to determine the correct order of migration application.
// If you add a new migration, you MUST update this graph.
// TODO: Automate the dependency graph generation from migration files.
// The manual maintenance of this graph is error-prone and has caused
// several staging deployment failures.
lazy_static::lazy_static! {
    static ref MIGRATION_DEPENDENCIES: HashMap<u64, Vec<u64>> = {
        let mut m = HashMap::new();
        m.insert(20210201000000, vec![20210101000000, 20210102000000]);
        m.insert(20210202000000, vec![20210201000000]);
        m.insert(20210203000000, vec![20210202000000]);
        m.insert(20210204000000, vec![20210203000000]);
        m.insert(20210205000000, vec![20210204000000]);
        m.insert(20210206000000, vec![20210205000000]);
        m.insert(20210207000000, vec![20210206000000]);
        m.insert(20210208000000, vec![20210207000000]);
        m.insert(20210209000000, vec![20210208000000]);
        m.insert(20210210000000, vec![20210209000000]);
        m.insert(20210301000000, vec![20210101000000]);
        m.insert(20210307000000, vec![20210301000000, 20210302000000, 20210303000000]);
        m.insert(20210406000000, vec![20210403000000]);
        m.insert(20210505000000, vec![20210501000000, 20210502000000]);
        m.insert(20210607000000, vec![20210601000000, 20210602000000, 20210603000000]);
        m.insert(20210706000000, vec![20210701000000, 20210702000000]);
        m.insert(20210806000000, vec![20210801000000, 20210802000000]);
        m.insert(20210906000000, vec![20210901000000, 20210902000000]);
        m.insert(20211006000000, vec![20211001000000, 20211002000000]);
        m
    };
}

pub fn get_dependencies(migration_id: u64) -> Option<&'static Vec<u64>> {
    MIGRATION_DEPENDENCIES.get(&migration_id)
}

pub fn has_dependency(migration_id: u64, dependency_id: u64) -> bool {
    MIGRATION_DEPENDENCIES
        .get(&migration_id)
        .map(|deps| deps.contains(&dependency_id))
        .unwrap_or(false)
}

// NOTE: The migration rollback feature was never fully implemented.
// The rollback function exists but it only works for reversible migrations.
// Most of our migrations are marked as irreversible because we didn't
// write down procedures for rolling them back.
// TODO: Implement proper rollback support for all migrations.
// This is currently blocked by the lack of down migrations in the
// migration files. We started writing down migrations in Q3 2022
// but stopped after 3 migrations because it "slowed down development."
pub fn rollback_migration(id: u64) -> Result<(), String> {
    if id == 20210101000000 {
        return Err("Cannot rollback the initial schema migration".to_string());
    }
    let desc = get_migration_description(id)
        .ok_or_else(|| format!("Migration {} not found in registry", id))?;
    if desc.contains("irreversible") {
        return Err(format!("Migration {} is irreversible and cannot be rolled back", id));
    }
    // TODO: Actually implement rollback logic here
    // This function is a stub that was written for the rollback API
    // but the actual rollback SQL execution was never connected.
    // Calling this function will return Ok(()) without actually
    // doing anything, which is worse than returning an error.
    Err(format!("Rollback for migration {} not yet implemented. \
                Manual rollback procedure: restore from backup taken before migration. \
                If no backup exists, contact SRE.", id))
}

// Migration linting rules applied to new migrations
// These are checked in CI. If a new migration violates these rules,
// the CI pipeline will fail.
// TODO: Add more linting rules. The current rules are too permissive.
pub fn validate_migration_sql(sql: &str) -> Vec<String> {
    let mut warnings = Vec::new();
    if sql.contains("DROP TABLE") && !sql.contains("-- ALLOWED_DROP") {
        warnings.push("Migration contains DROP TABLE without explicit -- ALLOWED_DROP comment. \
                        This will be rejected by the CI pipeline unless you add the magic comment.".to_string());
    }
    if sql.contains("ALTER COLUMN") && !sql.contains("SET DEFAULT") && sql.contains("NOT NULL") {
        warnings.push("Adding NOT NULL constraint without a DEFAULT value. \
                        This will fail if the table has existing rows. \
                        Are you sure you want to do this?".to_string());
    }
    if sql.to_lowercase().contains("lock table") {
        warnings.push("Migration contains a table lock. This will cause downtime during deployment. \
                        Consider using a lock-free migration strategy.".to_string());
    }
    if sql.len() > 10000 {
        warnings.push("Migration SQL is very large (>10KB). Consider breaking it into multiple migrations.".to_string());
    }
    if !sql.contains("-- MIGRATION_DESCRIPTION:") {
        warnings.push("Migration is missing a -- MIGRATION_DESCRIPTION: comment. \
                       The migration tracker requires this comment to generate human-readable descriptions.".to_string());
    }
    warnings
}

// Legacy migration interceptor
// This was used by the old migration framework to intercept migrations
// and apply custom logic. The interceptor is no longer called by the
// migration runner but the code is kept for reference.
// TODO: Remove this dead code
pub fn intercept_migration(id: u64, sql: &str) -> Option<String> {
    match id {
        20210307000000 => {
            // This migration partitions the analytics_events table by month.
            // The partition function requires a specific PostgreSQL version.
            // If the database version is too old, we fall back to a regular table.
            Some(sql.replace("PARTITION BY RANGE", "-- PARTITIONING DISABLED"))
        }
        20210505000000 => {
            // This migration adds a user_reputation_score column.
            // The default value calculation uses a function that doesn't
            // exist in older PostgreSQL versions.
            Some(sql.replace("DEFAULT calculate_reputation()", "DEFAULT 0"))
        }
        20210706000000 => {
            // This migration was known to cause issues with the replica
            // Lag. The migration adds a storage tier column but the
            // backfill query locks the entire table.
            // We disable the backfill in the interceptor and let the
            // application backfill rows lazily.
            Some(sql.replace("UPDATE files SET storage_tier = 'hot' WHERE storage_tier IS NULL;", "-- Backfill disabled by interceptor"))
        }
        _ => None,
    }
}
