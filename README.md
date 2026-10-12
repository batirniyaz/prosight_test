# 🧬 RNAcentral Locus API

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?style=flat&logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-3.18-A30000?style=flat)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-RNAcentral-316192?style=flat&logo=postgresql&logoColor=white)

A read-only REST API with a single `GET /locus` endpoint over the public **RNAcentral** PostgreSQL database
(`rnc_locus` + `rnc_locus_members`). It has JWT authentication with three predefined roles, filtering,
sideloading of locus members, pagination, multi-field sorting and auto-generated OpenAPI docs.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [Authentication](#-authentication)
- [API](#-api)
- [Tests](#-tests)
- [Project Structure](#-project-structure)
- [Decisions](#-decisions)
- [AI Usage](#-ai-usage)

---


- **Two databases.** RNAcentral is external and read-only, so users and roles live in a local SQLite DB.
  A DB router (`config/db_router.py`) sends the `loci` app to `rnacentral` and everything else to `default`.
- **Unmanaged models.** `Locus` and `LocusMember` use `managed = False`, so Django never tries to create
  or alter the RNAcentral tables. The `rlm.locus_id = rl.id` relation is a `ForeignKey`, and all queries go
  through the ORM. The project contains no raw SQL.

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| **Django 5.2** | Web framework, ORM, multi-DB routing |
| **Django REST Framework** | API views, serializers, permissions, pagination |
| **djangorestframework-simplejwt** | JWT authentication |
| **django-filter** | Query filters and multi-field ordering |
| **drf-spectacular** | OpenAPI 3 schema and Swagger UI |
| **psycopg2** | PostgreSQL driver |
| **python-dotenv** | Loads settings from `.env` |
| **Docker / Compose** | One-command setup on any OS |

---

## 🚀 Getting Started

### 1. Configure

```bash
git clone https://github.com/batirniyaz/prosight_test.git
cd prosight_test
cp .env.example .env               # Windows: copy .env.example .env
```

Fill in `.env`: a `SECRET_KEY` and the RNAcentral connection (`DB_*`, values are in the task description).
`.env` is git-ignored, so no secrets are stored in the repository.

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key (also signs JWTs) |
| `DEBUG` | Django debug mode, `1` / `0` (off if unset) |
| `ALLOWED_HOSTS` | Comma-separated host names |
| `DB_HOST`, `DB_PORT`, `DB_NAME` | RNAcentral PostgreSQL server |
| `DB_USER`, `DB_PASS` | Read-only credentials |
| `PORT` | Host port for the API (Docker only, default `8000`) |

### 2a. Run with Docker

```bash
docker compose up --build
```

The API is now at http://localhost:8000, with Swagger UI at http://localhost:8000/docs/.
On start the container runs `migrate`. This touches only the local SQLite (auth tables + predefined users),
and nothing is ever written to RNAcentral.

| Command | What it does |
|---------|--------------|
| `docker compose up --build` | Build and start the API |
| `docker compose run --rm api python manage.py test --settings=config.settings_test` | Run the tests |
| `docker compose run --rm api python manage.py check_rna` | Check the RNAcentral connection and both tables |
| `docker compose down` | Stop and remove the container |

### 2b. Run without Docker

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Tests: `python manage.py test --settings=config.settings_test` (no `.env` needed).

---

## 🔐 Authentication

Three predefined users are created by a data migration (`accounts/migrations/0001_seed_users.py`).
Each user's role is a Django group with the same name.

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin` | All columns, sideloading allowed |
| `normal` | `normal` | `rl` table data only, sideloading **not** allowed |
| `limited` | `limited` | Only loci with `regionId` in (86118093, 86696489, 88186467) |

Get a token:

```bash
curl -X POST http://127.0.0.1:8000/auth/token \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "admin"}'
```

Use it as `Authorization: Bearer <access>`. Refresh the token with `POST /auth/token/refresh`.

---

## 📡 API

### Documentation

| Documentation | URL |
|---------------|-----|
| **Swagger UI** | http://127.0.0.1:8000/docs/ |
| **OpenAPI schema** | http://127.0.0.1:8000/schema/ |

In Swagger, click **Authorize** and paste the access token.

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/token` | Obtain JWT access/refresh pair |
| `POST` | `/auth/token/refresh` | Refresh access token |
| `GET` | `/locus` | List loci (auth required) |

### `GET /locus` query parameters

| Parameter | Type | Table | Example | Description |
|-----------|------|-------|---------|-------------|
| `id` | integer, multiple | rl | `id=1,2,3` | Filter by locus ids |
| `assemblyId` | string, single | rl | `assemblyId=GRCh38` | Filter by genome assembly |
| `regionId` | integer, multiple | rlm | `regionId=86118093,86696489` | Loci having a member in these regions |
| `membershipStatus` | string, single | rlm | `membershipStatus=member` | Loci having a member with this status |

`regionId` and `membershipStatus` together match loci where **one and the same member** satisfies both.
| `sideloading` | enum: `locusMembers` | rlm | `sideloading=locusMembers` | Embed `locusMembers` in each locus |
| `sort` | string, multiple | rl | `sort=assemblyId,-locusStart` | Comma-separated fields, `-` = descending |
| `page` | integer | – | `page=2` | Page number (default `1`) |
| `limit` | integer | – | `limit=100` | Page size (default and max `1000`) |

Sortable fields: `id`, `assemblyId`, `locusName`, `publicLocusName`, `chromosome`, `strand`,
`locusStart`, `locusStop`, `memberCount`. Default order is `id`, and `id` is always the last sort key.

### Example

```bash
curl "http://127.0.0.1:8000/locus?assemblyId=GRCh38&sideloading=locusMembers&sort=-locusStart&limit=2" \
     -H "Authorization: Bearer <access>"
```

```json
{
  "data": [
    {
      "id": 1,
      "assemblyId": "GRCh38",
      "locusName": "...",
      "publicLocusName": "...",
      "chromosome": "1",
      "strand": "+",
      "locusStart": 0,
      "locusStop": 0,
      "memberCount": 1,
      "locusMembers": [
        { "locusMemberId": 0, "ursTaxid": "URS..._9606", "regionId": 86118093, "membershipStatus": "..." }
      ]
    }
  ],
  "meta": { "page": 1, "limit": 2, "total": 1 }
}
```

Without `sideloading`, the response has the same shape but without `locusMembers`.

### Status codes

| Code | When |
|------|------|
| `200` | Success |
| `400` | Invalid parameter value (e.g. `id=abc`, `sort=foo`, `sideloading=foo`) |
| `401` | No / invalid / expired token |
| `403` | `normal` user requests `sideloading`, or the user has no role |
| `404` | `page` out of range |
| `503` | Database error (e.g. RNAcentral is unreachable or the tables are missing), see [Decisions](#-decisions) |

---

## 🧪 Tests

```bash
docker compose run --rm api python manage.py test --settings=config.settings_test
```

The tests don't need the remote database. Django can't create a test database on the read-only RNAcentral
server, so `config/settings_test.py` points the `rnacentral` alias to an in-memory SQLite. A small runner
(`config/test_runner.py`) then makes the unmanaged models managed for the test run, so their tables get created.

**Coverage (33 tests, `loci/tests.py`):**

| Area | What is checked |
|------|-----------------|
| Auth | token issuing, wrong password, anonymous and invalid token → `401` |
| Response format | camelCase fields, `data`/`meta` shape, default limit `1000`, nested `locusMembers`, unknown `sideloading` → `400`, database error → `503` |
| Performance | sideloading runs a constant number of queries (no N+1) |
| Permissions | `admin` sees all; `normal` gets no members and `403` on sideloading; `limited` sees only allowed regions, including in nested members, when filtering by id, and when filtering by hidden members' region or status; a user without a role → `403` |
| Filters | `id` (multiple), `assemblyId`, `regionId` (multiple), `membershipStatus`, no duplicate loci on member filters, member filters match the same member, invalid value → `400` |
| Sorting | ascending, descending, multiple fields, `id` as tie-breaker, unknown field → `400` |
| Pagination | `page` + `limit`, `limit` capped at `1000` |
| Docs | OpenAPI schema is served |

---

## 📁 Project Structure

```
prosight_test/
├── Dockerfile
├── docker-compose.yml
├── .env.example             # settings for running without Docker
├── manage.py
├── requirements.txt
├── config/
│   ├── settings.py          # two DBs, DRF, JWT, Swagger
│   ├── settings_test.py     # in-memory DB for tests
│   ├── test_runner.py       # makes unmanaged models managed in tests
│   ├── db_router.py         # loci → rnacentral, everything else → default
│   ├── exceptions.py        # database errors → 503 JSON
│   └── urls.py
├── accounts/
│   ├── roles.py             # role names, limited region ids, get_role()
│   └── migrations/
│       └── 0001_seed_users.py   # predefined users + groups
└── loci/
    ├── models.py            # Locus (rnc_locus), LocusMember (rnc_locus_members)
    ├── serializers.py       # camelCase output, with/without members
    ├── filters.py           # filters + multi-field sort
    ├── permissions.py       # role checks + loci/members visible to the user
    ├── pagination.py        # {data, meta} response, default 1000
    ├── views.py             # LocusListView: role scoping + prefetch
    ├── tests.py
    └── management/commands/check_rna.py   # RNAcentral connectivity check
```

---

## 🤔 Decisions

Places where the task was unclear and what I assumed:

1. **`assemblyId` is a string.** The task says integer, but the column is text (`GRCh38`), and the example
   response shows a string too.
2. **Parameter formats.** "Enum" filters take comma-separated values (`?id=1,2,3`). Sorting takes
   comma-separated fields with `-` for descending (`?sort=assemblyId,-locusStart`).
3. **`normal`** gets `403` for any `sideloading` instead of a silently trimmed response. It may still filter
   by `regionId` / `membershipStatus`, but the response has `rl` columns only.
4. **`limited`** sees only loci with at least one member in the allowed regions. Sideloading is allowed, but
   nested members and member filters cover only the allowed regions, so hidden members can't be seen or searched.
5. **Member filters** (`regionId`, `membershipStatus`) return loci where one and the same member matches all
   of them. They don't narrow the nested `locusMembers`.
6. **RNAcentral was unavailable** during the work (the reviewers confirmed problems with the DB):
   `rnc_locus` / `rnc_locus_members` were missing, and the `rnacen` schema returned `permission denied`.
   The models follow the schema from the task, the tests run on a local DB, and `/locus` returns `503`
   until the DB is back. `python manage.py check_rna` shows the current state.

---

## 🤖 AI Usage

I used Claude as an assistant during this task:

- **Debugging the database:** finding out why `inspectdb` and `information_schema` returned nothing,
  and reading table structure from the PostgreSQL catalog.
- **Code review** of my code, and **writing the test suite** and this README.

Cases where I corrected or rejected its output:

- **Redundant `source`:** its serializer example used `source="id"` (and the same for `chromosome` / `strand`),
  and DRF failed with *"It is redundant to specify `source`..."*. I removed those declarations.
- **`inspectdb` didn't work:** it suggested `inspectdb` to generate models, but it fails on this server
  (`permission denied for table pg_am`), so I wrote the models by hand.
- **Rejected a local fake DB:** when RNAcentral was unavailable, it proposed switching the app to a local
  SQLite with generated fake data. I rejected this because it moves away from the task. The app stays on the
  real DB, and SQLite is used only in tests.
- **Test setup didn't work at first:** its plan assumed the `loci` app has no migrations package, but the
  project had an empty `loci/migrations/`, so test tables were not created. It was fixed with
  `MIGRATION_MODULES = {"loci": None}` in the test settings.
- **Bugs found in review:** its review caught that overriding `permission_classes` on the view had dropped the
  global `IsAuthenticated` (anonymous access), and that the base serializer leaked `locusMembers` to `normal`.
  I fixed both, and the tests cover them now.
