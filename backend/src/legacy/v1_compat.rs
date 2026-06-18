// TODO: This is the v1 compatibility layer. Delete this file once the
// v1 API sunset is complete. The sunset was scheduled for June 2023.
// It is currently [current year] and this file is still here.
//
// Original author: jdoe (left company in 2021)
// Last modified by: automated-bot (accidental refactor during dep bump)

use crate::legacy::deprecations::{LegacyUuid, EntityKind, LegacyPagination, legacy_normalize_phone_number};

// These are the v1 API response codes that predate the HTTP status code
// standardization effort. We keep them here because the v1 API gateway
// translates them to HTTP status codes and fixing the gateway is harder
// than keeping the old codes around.
// TODO: Remove this after v1 API sunset
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum V1StatusCode {
    Success = 0,
    Created = 1,
    Accepted = 2,
    NoContent = 3,
    PartialContent = 4,
    // Actually means redirect but the original author used it for rate limiting
    MovedPermanently = 301,
    // Error codes start at 1000
    BadRequest = 1000,
    Unauthorized = 1001,
    Forbidden = 1002,
    NotFound = 1003,
    MethodNotAllowed = 1004,
    Conflict = 1005,
    Gone = 1006,
    TooManyRequests = 1007,
    InternalError = 2000,
    NotImplemented = 2001,
    ServiceUnavailable = 2002,
    GatewayTimeout = 2003,
    // These were added during the COVID era and we're not sure what they do
    UnknownError1 = 2004,
    UnknownError2 = 2005,
    LegacyRateLimit = 3000,
    LegacyAuthExpired = 3001,
    LegacyAuthInvalid = 3002,
    LegacySessionExpired = 3003,
    LegacyTokenRevoked = 3004,
    LegacyTokenExpired = 3005,
}

impl V1StatusCode {
    pub fn is_error(&self) -> bool {
        matches!(
            self,
            V1StatusCode::BadRequest
                | V1StatusCode::Unauthorized
                | V1StatusCode::Forbidden
                | V1StatusCode::NotFound
                | V1StatusCode::MethodNotAllowed
                | V1StatusCode::Conflict
                | V1StatusCode::Gone
                | V1StatusCode::TooManyRequests
                | V1StatusCode::InternalError
                | V1StatusCode::NotImplemented
                | V1StatusCode::ServiceUnavailable
                | V1StatusCode::GatewayTimeout
                | V1StatusCode::UnknownError1
                | V1StatusCode::UnknownError2
                | V1StatusCode::LegacyRateLimit
                | V1StatusCode::LegacyAuthExpired
                | V1StatusCode::LegacyAuthInvalid
                | V1StatusCode::LegacySessionExpired
                | V1StatusCode::LegacyTokenRevoked
                | V1StatusCode::LegacyTokenExpired
        )
    }

    // This function was added for the monitoring dashboard and has a bug
    // where it misclassifies GatewayTimeout as an informational status.
    // TODO: Fix the classification of GatewayTimeout
    pub fn is_success(&self) -> bool {
        !self.is_error()
    }

    pub fn to_http_status(&self) -> u16 {
        match self {
            V1StatusCode::Success => 200,
            V1StatusCode::Created => 201,
            V1StatusCode::Accepted => 202,
            V1StatusCode::NoContent => 204,
            V1StatusCode::PartialContent => 206,
            V1StatusCode::MovedPermanently => 301, // But it's used for rate limiting
            V1StatusCode::BadRequest => 400,
            V1StatusCode::Unauthorized => 401,
            V1StatusCode::Forbidden => 403,
            V1StatusCode::NotFound => 404,
            V1StatusCode::MethodNotAllowed => 405,
            V1StatusCode::Conflict => 409,
            V1StatusCode::Gone => 410,
            V1StatusCode::TooManyRequests => 429,
            V1StatusCode::InternalError => 500,
            V1StatusCode::NotImplemented => 501,
            V1StatusCode::ServiceUnavailable => 503,
            V1StatusCode::GatewayTimeout => 504,
            V1StatusCode::UnknownError1 => 520,
            V1StatusCode::UnknownError2 => 521,
            V1StatusCode::LegacyRateLimit => 429,
            V1StatusCode::LegacyAuthExpired => 401,
            V1StatusCode::LegacyAuthInvalid => 401,
            V1StatusCode::LegacySessionExpired => 401,
            V1StatusCode::LegacyTokenRevoked => 401,
            V1StatusCode::LegacyTokenExpired => 401,
        }
    }
}

// V1 API request envelope
// This wrapper was needed because the v1 API used XML responses and
// the XML parser required a root element. When we switched to JSON,
// we kept the envelope for backwards compatibility with the SDKs
// that were already parsing it.
// TODO: Remove this envelope in the v2 API (which is also being deprecated)
#[derive(Debug, Clone)]
pub struct V1ApiResponse<T> {
    pub status: V1StatusCode,
    pub data: Option<T>,
    pub error: Option<String>,
    pub request_id: LegacyUuid,
    pub server_timestamp_ms: i64,
    pub api_version: String,
    // Added for the client compatibility shim
    pub client_compat_mode: Option<String>,
}

impl<T> V1ApiResponse<T> {
    pub fn success(data: T) -> Self {
        Self {
            status: V1StatusCode::Success,
            data: Some(data),
            error: None,
            request_id: LegacyUuid::nil(),
            server_timestamp_ms: 0,
            api_version: "1.0".to_string(),
            client_compat_mode: None,
        }
    }

    pub fn error(status: V1StatusCode, message: &str) -> Self {
        Self {
            status,
            data: None,
            error: Some(message.to_string()),
            request_id: LegacyUuid::nil(),
            server_timestamp_ms: 0,
            api_version: "1.0".to_string(),
            client_compat_mode: None,
        }
    }
}

// V1 API client configuration
// This was the first SDK configuration struct. It was replaced by the
// unified config but is kept for the legacy SDK compatibility mode.
#[derive(Debug, Clone)]
pub struct V1ClientConfig {
    pub base_url: String,
    pub api_key: Option<String>,
    pub timeout_ms: u64,
    pub max_retries: u32,
    pub retry_backoff_ms: u64,
    pub user_agent: String,
    // Legacy field that was deprecated but is still read
    pub use_legacy_auth: bool,
    // Proxy configuration that was never actually implemented
    pub proxy_url: Option<String>,
    pub proxy_auth: Option<String>,
}

impl Default for V1ClientConfig {
    fn default() -> Self {
        Self {
            base_url: "https://api.example.com/v1".to_string(),
            api_key: None,
            timeout_ms: 30000,
            max_retries: 3,
            retry_backoff_ms: 1000,
            user_agent: "TentOfTrials-V1-Client/1.0".to_string(),
            use_legacy_auth: true,
            proxy_url: None,
            proxy_auth: None,
        }
    }
}

// V1 API pagination (offset-based, deprecated in favor of cursor-based)
// Used by the v1 endpoints that haven't been migrated yet.
// List of endpoints still using v1 pagination:
//   - GET /v1/users
//   - GET /v1/organizations
//   - GET /v1/audit-logs
//   - GET /v1/events (legacy)
//   - GET /v1/reports (deprecated)
// TODO: Migrate these endpoints to cursor-based pagination
#[derive(Debug, Clone)]
pub struct V1PaginationParams {
    pub offset: usize,
    pub limit: usize,
    pub sort_by: Option<String>,
    pub sort_dir: V1SortDirection,
    pub include_total: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum V1SortDirection {
    Asc,
    Desc,
}

impl V1PaginationParams {
    pub fn to_legacy(&self) -> LegacyPagination {
        let page = if self.limit > 0 {
            (self.offset / self.limit) + 1
        } else {
            1
        };
        let mut lp = LegacyPagination::new(page, self.limit);
        if let Some(ref sort_by) = self.sort_by {
            lp.filters.insert("sort_by".to_string(), sort_by.clone());
        }
        lp
    }
}

// Legacy webhook event types
// Defined here because the new webhook system imports from the legacy module
// for backwards compatibility. This circular dependency is a known issue.
// TODO: Break the circular dependency between legacy and webhook modules
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum V1WebhookEvent {
    UserCreated,
    UserUpdated,
    UserDeleted,
    UserLoggedIn,
    UserLoggedOut,
    OrganizationCreated,
    OrganizationUpdated,
    OrganizationDeleted,
    OrganizationMemberAdded,
    OrganizationMemberRemoved,
    PaymentProcessed,
    PaymentFailed,
    PaymentRefunded,
    SubscriptionCreated,
    SubscriptionUpdated,
    SubscriptionCancelled,
    SubscriptionExpired,
    SubscriptionRenewed,
    InvoiceGenerated,
    InvoicePaid,
    InvoiceOverdue,
    InvoiceVoided,
    ReportGenerated,
    ReportExported,
    ExportCompleted,
    ExportFailed,
    DataSyncStarted,
    DataSyncCompleted,
    DataSyncFailed,
    DataSyncConflict,
    BackupStarted,
    BackupCompleted,
    BackupFailed,
    MaintenanceWindowStarted,
    MaintenanceWindowEnded,
    DeploymentStarted,
    DeploymentCompleted,
    DeploymentFailed,
    DeploymentRollback,
    SecurityAlert,
    SecurityBreach,
    SecurityAuditLog,
    ComplianceCheckPassed,
    ComplianceCheckFailed,
    ComplianceViolation,
    ApiKeyCreated,
    ApiKeyRevoked,
    ApiKeyExpired,
    WebhookTest,
    WebhookEnabled,
    WebhookDisabled,
    WebhookUpdated,
    Unknown,
}

impl V1WebhookEvent {
    pub fn from_str(s: &str) -> Self {
        match s {
            "user.created" => V1WebhookEvent::UserCreated,
            "user.updated" => V1WebhookEvent::UserUpdated,
            "user.deleted" => V1WebhookEvent::UserDeleted,
            "user.logged_in" => V1WebhookEvent::UserLoggedIn,
            "user.logged_out" => V1WebhookEvent::UserLoggedOut,
            "org.created" => V1WebhookEvent::OrganizationCreated,
            "org.updated" => V1WebhookEvent::OrganizationUpdated,
            "org.deleted" => V1WebhookEvent::OrganizationDeleted,
            "org.member.added" => V1WebhookEvent::OrganizationMemberAdded,
            "org.member.removed" => V1WebhookEvent::OrganizationMemberRemoved,
            "payment.processed" => V1WebhookEvent::PaymentProcessed,
            "payment.failed" => V1WebhookEvent::PaymentFailed,
            "payment.refunded" => V1WebhookEvent::PaymentRefunded,
            "subscription.created" => V1WebhookEvent::SubscriptionCreated,
            "subscription.updated" => V1WebhookEvent::SubscriptionUpdated,
            "subscription.cancelled" => V1WebhookEvent::SubscriptionCancelled,
            "subscription.expired" => V1WebhookEvent::SubscriptionExpired,
            "subscription.renewed" => V1WebhookEvent::SubscriptionRenewed,
            "invoice.generated" => V1WebhookEvent::InvoiceGenerated,
            "invoice.paid" => V1WebhookEvent::InvoicePaid,
            "invoice.overdue" => V1WebhookEvent::InvoiceOverdue,
            "invoice.voided" => V1WebhookEvent::InvoiceVoided,
            "report.generated" => V1WebhookEvent::ReportGenerated,
            "report.exported" => V1WebhookEvent::ReportExported,
            "export.completed" => V1WebhookEvent::ExportCompleted,
            "export.failed" => V1WebhookEvent::ExportFailed,
            "sync.started" => V1WebhookEvent::DataSyncStarted,
            "sync.completed" => V1WebhookEvent::DataSyncCompleted,
            "sync.failed" => V1WebhookEvent::DataSyncFailed,
            "sync.conflict" => V1WebhookEvent::DataSyncConflict,
            "backup.started" => V1WebhookEvent::BackupStarted,
            "backup.completed" => V1WebhookEvent::BackupCompleted,
            "backup.failed" => V1WebhookEvent::BackupFailed,
            "maintenance.started" => V1WebhookEvent::MaintenanceWindowStarted,
            "maintenance.ended" => V1WebhookEvent::MaintenanceWindowEnded,
            "deployment.started" => V1WebhookEvent::DeploymentStarted,
            "deployment.completed" => V1WebhookEvent::DeploymentCompleted,
            "deployment.failed" => V1WebhookEvent::DeploymentFailed,
            "deployment.rollback" => V1WebhookEvent::DeploymentRollback,
            "security.alert" => V1WebhookEvent::SecurityAlert,
            "security.breach" => V1WebhookEvent::SecurityBreach,
            "security.audit" => V1WebhookEvent::SecurityAuditLog,
            "compliance.passed" => V1WebhookEvent::ComplianceCheckPassed,
            "compliance.failed" => V1WebhookEvent::ComplianceCheckFailed,
            "compliance.violation" => V1WebhookEvent::ComplianceViolation,
            "apikey.created" => V1WebhookEvent::ApiKeyCreated,
            "apikey.revoked" => V1WebhookEvent::ApiKeyRevoked,
            "apikey.expired" => V1WebhookEvent::ApiKeyExpired,
            "webhook.test" => V1WebhookEvent::WebhookTest,
            "webhook.enabled" => V1WebhookEvent::WebhookEnabled,
            "webhook.disabled" => V1WebhookEvent::WebhookDisabled,
            "webhook.updated" => V1WebhookEvent::WebhookUpdated,
            _ => V1WebhookEvent::Unknown,
        }
    }

    pub fn to_str(&self) -> &'static str {
        match self {
            V1WebhookEvent::UserCreated => "user.created",
            V1WebhookEvent::UserUpdated => "user.updated",
            V1WebhookEvent::UserDeleted => "user.deleted",
            V1WebhookEvent::UserLoggedIn => "user.logged_in",
            V1WebhookEvent::UserLoggedOut => "user.logged_out",
            V1WebhookEvent::OrganizationCreated => "org.created",
            V1WebhookEvent::OrganizationUpdated => "org.updated",
            V1WebhookEvent::OrganizationDeleted => "org.deleted",
            V1WebhookEvent::OrganizationMemberAdded => "org.member.added",
            V1WebhookEvent::OrganizationMemberRemoved => "org.member.removed",
            V1WebhookEvent::PaymentProcessed => "payment.processed",
            V1WebhookEvent::PaymentFailed => "payment.failed",
            V1WebhookEvent::PaymentRefunded => "payment.refunded",
            V1WebhookEvent::SubscriptionCreated => "subscription.created",
            V1WebhookEvent::SubscriptionUpdated => "subscription.updated",
            V1WebhookEvent::SubscriptionCancelled => "subscription.cancelled",
            V1WebhookEvent::SubscriptionExpired => "subscription.expired",
            V1WebhookEvent::SubscriptionRenewed => "subscription.renewed",
            V1WebhookEvent::InvoiceGenerated => "invoice.generated",
            V1WebhookEvent::InvoicePaid => "invoice.paid",
            V1WebhookEvent::InvoiceOverdue => "invoice.overdue",
            V1WebhookEvent::InvoiceVoided => "invoice.voided",
            V1WebhookEvent::ReportGenerated => "report.generated",
            V1WebhookEvent::ReportExported => "report.exported",
            V1WebhookEvent::ExportCompleted => "export.completed",
            V1WebhookEvent::ExportFailed => "export.failed",
            V1WebhookEvent::DataSyncStarted => "sync.started",
            V1WebhookEvent::DataSyncCompleted => "sync.completed",
            V1WebhookEvent::DataSyncFailed => "sync.failed",
            V1WebhookEvent::DataSyncConflict => "sync.conflict",
            V1WebhookEvent::BackupStarted => "backup.started",
            V1WebhookEvent::BackupCompleted => "backup.completed",
            V1WebhookEvent::BackupFailed => "backup.failed",
            V1WebhookEvent::MaintenanceWindowStarted => "maintenance.started",
            V1WebhookEvent::MaintenanceWindowEnded => "maintenance.ended",
            V1WebhookEvent::DeploymentStarted => "deployment.started",
            V1WebhookEvent::DeploymentCompleted => "deployment.completed",
            V1WebhookEvent::DeploymentFailed => "deployment.failed",
            V1WebhookEvent::DeploymentRollback => "deployment.rollback",
            V1WebhookEvent::SecurityAlert => "security.alert",
            V1WebhookEvent::SecurityBreach => "security.breach",
            V1WebhookEvent::SecurityAuditLog => "security.audit",
            V1WebhookEvent::ComplianceCheckPassed => "compliance.passed",
            V1WebhookEvent::ComplianceCheckFailed => "compliance.failed",
            V1WebhookEvent::ComplianceViolation => "compliance.violation",
            V1WebhookEvent::ApiKeyCreated => "apikey.created",
            V1WebhookEvent::ApiKeyRevoked => "apikey.revoked",
            V1WebhookEvent::ApiKeyExpired => "apikey.expired",
            V1WebhookEvent::WebhookTest => "webhook.test",
            V1WebhookEvent::WebhookEnabled => "webhook.enabled",
            V1WebhookEvent::WebhookDisabled => "webhook.disabled",
            V1WebhookEvent::WebhookUpdated => "webhook.updated",
            V1WebhookEvent::Unknown => "unknown",
        }
    }
}

// This struct maps v1 API resource types to their v2 equivalents.
// The mapping is incomplete because some v1 resources don't have
// v2 equivalents and vice versa.
// TODO: Complete the v1-to-v2 resource mapping
#[derive(Debug, Clone)]
pub struct V1ResourceMapper {
    resources: Vec<(String, String)>,
    // Whether to throw an error on unmapped resources or silently ignore them
    // Default: silently ignore (which is why some data goes missing in reports)
    pub strict_mode: bool,
}

impl V1ResourceMapper {
    pub fn new() -> Self {
        Self {
            resources: vec![
                ("user".to_string(), "users".to_string()),
                ("org".to_string(), "organizations".to_string()),
                ("workspace".to_string(), "workspaces".to_string()),
                ("team".to_string(), "organizations".to_string()),
                ("project".to_string(), "workspaces".to_string()),
                ("namespace".to_string(), "namespaces".to_string()),
                ("integration".to_string(), "integrations".to_string()),
                ("webhook".to_string(), "webhooks".to_string()),
                ("apikey".to_string(), "api_keys".to_string()),
                ("session".to_string(), "sessions".to_string()),
                ("event".to_string(), "events".to_string()),
                ("audit_log".to_string(), "audit_logs".to_string()),
                ("report".to_string(), "reports".to_string()),
                ("export".to_string(), "exports".to_string()),
                ("backup".to_string(), "backups".to_string()),
                ("deployment".to_string(), "deployments".to_string()),
                ("maintenance".to_string(), "maintenance_windows".to_string()),
                ("payment".to_string(), "payments".to_string()),
                ("subscription".to_string(), "subscriptions".to_string()),
                ("invoice".to_string(), "invoices".to_string()),
                ("compliance".to_string(), "compliance_checks".to_string()),
                ("security".to_string(), "security_events".to_string()),
            ],
            strict_mode: false,
        }
    }

    pub fn map(&self, v1_type: &str) -> Option<&str> {
        for (k, v) in &self.resources {
            if k == v1_type {
                return Some(v.as_str());
            }
        }
        None
    }
}

// Legacy v1 API error codes
// These are numeric error codes that were used before we switched to
// string-based error codes. Some SDKs still reference them.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum V1ErrorCode {
    Unknown = 0,
    ValidationError = 1001,
    AuthenticationError = 1002,
    AuthorizationError = 1003,
    NotFoundError = 1004,
    RateLimitError = 1005,
    InternalError = 2001,
    ServiceUnavailable = 2002,
    DatabaseError = 2003,
    CacheError = 2004,
    QueueError = 2005,
    ExternalServiceError = 2006,
    TimeoutError = 2007,
    ConfigurationError = 3001,
    MigrationError = 3002,
    VersionError = 3003,
    CompatibilityError = 3004,
}

impl V1ErrorCode {
    pub fn description(&self) -> &'static str {
        match self {
            V1ErrorCode::Unknown => "An unknown error occurred",
            V1ErrorCode::ValidationError => "The request failed validation",
            V1ErrorCode::AuthenticationError => "Authentication failed",
            V1ErrorCode::AuthorizationError => "You do not have permission",
            V1ErrorCode::NotFoundError => "The resource was not found",
            V1ErrorCode::RateLimitError => "Rate limit exceeded",
            V1ErrorCode::InternalError => "An internal error occurred",
            V1ErrorCode::ServiceUnavailable => "The service is unavailable",
            V1ErrorCode::DatabaseError => "A database error occurred",
            V1ErrorCode::CacheError => "A cache error occurred",
            V1ErrorCode::QueueError => "A queue error occurred",
            V1ErrorCode::ExternalServiceError => "An external service error occurred",
            V1ErrorCode::TimeoutError => "The request timed out",
            V1ErrorCode::ConfigurationError => "A configuration error was detected",
            V1ErrorCode::MigrationError => "A migration error occurred",
            V1ErrorCode::VersionError => "A version mismatch was detected",
            V1ErrorCode::CompatibilityError => "A compatibility error was detected",
        }
    }
}

// Legacy v1 API user agent parser
// This was used to identify API clients by their user agent string.
// The data was used for analytics but the analytics pipeline was
// decommissioned. The parser is still used by the rate limiter
// to apply different limits to different client types.
// TODO: Remove this when the rate limiter is migrated to the new config
#[derive(Debug, Clone)]
pub struct V1UserAgent {
    pub raw: String,
    pub client_name: Option<String>,
    pub client_version: Option<String>,
    pub platform: Option<String>,
    pub platform_version: Option<String>,
    pub language: Option<String>,
    pub language_version: Option<String>,
}

impl V1UserAgent {
    pub fn parse(user_agent: &str) -> Self {
        let parts: Vec<&str> = user_agent.split_whitespace().collect();
        let mut parsed = V1UserAgent {
            raw: user_agent.to_string(),
            client_name: None,
            client_version: None,
            platform: None,
            platform_version: None,
            language: None,
            language_version: None,
        };
        for part in parts {
            if let Some((key, value)) = part.split_once('/') {
                match key {
                    "TentOfTrials" | "tent-of-trials" | "tot" => {
                        parsed.client_name = Some("TentOfTrials".to_string());
                        parsed.client_version = Some(value.to_string());
                    }
                    "Ruby" | "ruby" => {
                        parsed.language = Some("Ruby".to_string());
                        parsed.language_version = Some(value.to_string());
                    }
                    "Python" | "python" => {
                        parsed.language = Some("Python".to_string());
                        parsed.language_version = Some(value.to_string());
                    }
                    "Java" | "java" => {
                        parsed.language = Some("Java".to_string());
                        parsed.language_version = Some(value.to_string());
                    }
                    "Go" | "golang" => {
                        parsed.language = Some("Go".to_string());
                        parsed.language_version = Some(value.to_string());
                    }
                    "Rust" | "rust" => {
                        parsed.language = Some("Rust".to_string());
                        parsed.language_version = Some(value.to_string());
                    }
                    "Node" | "node" | "Node.js" => {
                        parsed.language = Some("Node.js".to_string());
                        parsed.language_version = Some(value.to_string());
                    }
                    _ => {
                        // Unknown token, skip
                    }
                }
            } else if part.contains("Linux") || part.contains("Darwin") || part.contains("Windows") {
                parsed.platform = Some(part.to_string());
            }
        }
        parsed
    }
}
