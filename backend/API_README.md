# REST API (APIView)

This version uses DRF `APIView` classes, not routers/viewsets.
Existing Django templates and models are retained.

Base URL:
`/api/`

Endpoints:
- GET/POST `/api/employees/`
- GET/PUT/PATCH/DELETE `/api/employees/<id>/`
- GET/POST `/api/departments/`
- GET/PUT/PATCH/DELETE `/api/departments/<id>/`
- GET/POST `/api/teams/`
- GET/PUT/PATCH/DELETE `/api/teams/<id>/`
- GET/POST `/api/attendance/`
- GET/PUT/PATCH/DELETE `/api/attendance/<id>/`
- GET/POST `/api/leaves/`
- GET/PUT/PATCH `/api/leaves/<id>/`
- GET `/api/notifications/`
- GET/PATCH `/api/notifications/<id>/`

Authentication uses DRF `IsAuthenticated` (register/login/firebase are `AllowAny`).
Every endpoint's permissions mirror the equivalent normal Django view — see below.

## Added API features
- `POST /api/auth/register/`: email, name, password, city. Role is always EMPLOYEE.
  Creates the account only, exactly like the normal Django register page — it does
  **not** return tokens. Call `/api/auth/login/` next to get a token.
- `POST /api/auth/login/`: returns JWT access and refresh tokens.
- `POST /api/auth/firebase/`: accepts a Firebase `id_token`; backend requires
  `FIREBASE_SERVICE_ACCOUNT_JSON`. This is a login flow, so it does return tokens.
- Role-scoped access mirrors the normal Django views exactly:
  - Employees / Departments / Attendance edits (mark/edit/delete): HR only.
  - Teams: create/update/delete by the owning MANAGER only (HR is read-only here too,
    since there's no HR team-management screen on the site).
  - Leave requests: EMPLOYEE creates their own request; the assigned MANAGER
    approves/rejects it with `PATCH {"action":"approve"}` or `{"action":"reject"}`
    (optional `manager_comment`); HR is read-only.
  - Notifications: `PATCH /api/notifications/<id>/` marks your own notification read.
- `POST /api/attendance/` checks in the authenticated HR/manager/employee in IST.
- `PATCH /api/attendance/<id>/` with `{"action":"check_out"}` checks out.
- Django timezone changed to `Asia/Kolkata`.
- Employee form manager field only lists employees with MANAGER role.

Install: `pip install -r requirements.txt`; run `python manage.py migrate` and `python manage.py runserver`.



