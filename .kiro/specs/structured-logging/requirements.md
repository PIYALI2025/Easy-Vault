# Requirements Document

## Introduction

The Private Cloud application currently has inconsistent and incomplete logging across its modules. Some critical paths use bare `print()` statements, many endpoints have no log output at all, auth events are untracked, and the `user_id` context is not reliably injected into log records. This feature improves logging to be structured, consistent, and complete so that the system is observable in production.

## Glossary

- **Logger**: The `UserLoggerAdapter` instance returned by `get_logger()` in `logger.py`
- **user_id**: The username of the authenticated user performing an action, or `"SYSTEM"` for background/unauthenticated operations
- **Structured Log Record**: A log entry that includes timestamp, level, user_id, module, and message in a consistent format
- **HTTP Access Log**: A log record emitted per HTTP request containing method, path, status code, and duration
- **Auth Event**: Any signup, login success, login failure, or token validation failure
- **File Event**: Any upload, download, preview, rename, slug regeneration, or delete operation on a file
- **Access Event**: Any access request creation, approval, or denial
- **Background Task**: Any operation run by the Janitor service outside of an HTTP request context

## Requirements

### Requirement 1: Consistent Log Format

**User Story:** As a developer, I want all log records to follow a consistent format, so that I can parse and filter logs reliably in production.

#### Acceptance Criteria

1. THE Logger SHALL emit every log record in the format: `[YYYY-MM-DD HH:MM:SS] LEVEL - User: <user_id> - <module> - <message>`
2. THE Logger SHALL include `user_id` in every log record, defaulting to `"SYSTEM"` when no authenticated user is present
3. THE Logger SHALL write all log output to stdout
4. IF the `LOG_LEVEL` environment variable is set, THEN THE Logger SHALL use that level; otherwise THE Logger SHALL default to `INFO`

---

### Requirement 2: HTTP Request Logging

**User Story:** As a developer, I want every HTTP request to be logged, so that I can trace activity and diagnose issues.

#### Acceptance Criteria

1. WHEN an HTTP request is received, THE System SHALL log the request method, path, and the authenticated user's username (or `"anonymous"` if unauthenticated)
2. WHEN an HTTP response is sent, THE System SHALL log the request method, path, status code, and elapsed time in milliseconds
3. THE HTTP access log SHALL be emitted at `INFO` level for 2xx and 3xx responses
4. THE HTTP access log SHALL be emitted at `WARNING` level for 4xx responses
5. THE HTTP access log SHALL be emitted at `ERROR` level for 5xx responses

---

### Requirement 3: Authentication Event Logging

**User Story:** As a developer, I want all authentication events to be logged, so that I can detect unauthorized access attempts.

#### Acceptance Criteria

1. WHEN a user successfully registers, THE System SHALL log an `INFO` record containing the new username
2. WHEN a user successfully logs in, THE System SHALL log an `INFO` record containing the username
3. WHEN a login attempt fails due to incorrect credentials, THE System SHALL log a `WARNING` record containing the attempted username
4. WHEN a JWT token cannot be validated, THE System SHALL log a `WARNING` record indicating the token failure

---

### Requirement 4: File Operation Logging

**User Story:** As a developer, I want all file operations to be logged with the acting user's identity, so that I can audit file activity.

#### Acceptance Criteria

1. WHEN a file is uploaded, THE System SHALL log an `INFO` record containing the filename, content hash, and user_id
2. WHEN a file is downloaded, THE System SHALL log an `INFO` record containing the share slug and user_id
3. WHEN a file is previewed, THE System SHALL log an `INFO` record containing the share slug and user_id
4. WHEN a file is renamed, THE System SHALL log an `INFO` record containing the file id, old name, new name, and user_id
5. WHEN a share slug is regenerated, THE System SHALL log an `INFO` record containing the file id, old slug, new slug, and user_id
6. WHEN a file access check fails due to missing or expired permissions, THE System SHALL log a `WARNING` record containing the slug and reason

---

### Requirement 5: Access Request Event Logging

**User Story:** As a developer, I want access request lifecycle events to be logged, so that I can audit sharing activity.

#### Acceptance Criteria

1. WHEN an access request is created, THE System SHALL log an `INFO` record containing the requester's username, the file name, and the duration
2. WHEN an access request is approved, THE System SHALL log an `INFO` record containing the approver's username, the requester's username, and the file name
3. WHEN an access request is denied, THE System SHALL log an `INFO` record containing the denier's username, the requester's username, and the file name

---

### Requirement 6: Storage Engine Logging

**User Story:** As a developer, I want the storage engine to use the application logger instead of print statements, so that storage errors appear in the structured log output.

#### Acceptance Criteria

1. THE Storage_Engine SHALL use the Logger from `get_logger()` for all log output instead of `print()`
2. WHEN a file is successfully written to disk, THE Storage_Engine SHALL log an `INFO` record containing the file hash and size in bytes
3. WHEN a file write fails, THE Storage_Engine SHALL log an `ERROR` record containing the file hash and the exception message
4. WHEN a de-duplicated file is skipped, THE Storage_Engine SHALL log a `DEBUG` record containing the file hash

---

### Requirement 7: Background Task Logging

**User Story:** As a developer, I want the Janitor service logs to include structured context, so that maintenance events are traceable.

#### Acceptance Criteria

1. WHEN the Janitor starts, THE Janitor SHALL log an `INFO` record with `user_id` set to `"SYSTEM"`
2. WHEN the Janitor deletes an orphaned file, THE Janitor SHALL log an `INFO` record containing the file hash and size
3. WHEN a Janitor file deletion fails, THE Janitor SHALL log an `ERROR` record containing the file hash and exception message
4. WHEN the Janitor completes, THE Janitor SHALL log an `INFO` summary containing the count of deleted files and total space reclaimed in MB
