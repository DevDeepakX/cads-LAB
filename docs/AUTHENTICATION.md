# Authentication

CADS Phase 5 uses Flask signed sessions and Werkzeug password hashing.

## Account flow

- `GET/POST /register` creates a `STUDENT` account.
- `GET/POST /login` authenticates by username or email.
- `POST/GET /logout` clears the session.
- `GET /api/me` returns safe user profile fields only.

Passwords are stored as Werkzeug password hashes. Password hashes are never serialized to API responses. Login failures use one generic message for unknown users and incorrect passwords.

## CSRF

State-changing requests require the session-bound token from the `csrf_token` form field or `X-CSRFToken` header. This covers account actions, lab start/reset, terminal commands, investigation, remediation, and logout.

## Ownership

Authenticated user identity comes from the signed Flask session. Lab APIs resolve the active lab session from that identity and verify `lab_sessions.user_id` before reading resources, events, findings, or progress. Browser-supplied user IDs and simulator session IDs are not accepted as authority.
