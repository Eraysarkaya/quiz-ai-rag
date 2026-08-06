# Security policy

Do not report credentials in a public issue. Revoke the credential first, then contact the repository owner privately with a description of the affected file or commit.

Local secrets belong in `.env` or `frontend/.env.local`; both are excluded from version control. Runtime databases must not contain real user data when used for demonstrations.
