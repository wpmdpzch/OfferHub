# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI/CD workflows (Backend Test, Frontend Build, Crawler Test)
- CONTRIBUTING.md with contribution guidelines
- GitHub Issue templates (Bug Report, Feature Request)
- GitHub PR template
- Changelog documentation

### Changed
- README.md redesign: added badges, roadmap, feature table, improved structure
- seed_crawl.py: add empty-source guard clause to skip crawl gracefully
- smoke_test.py: refactor global `req()` into `TestRunner.req()` method for proper state encapsulation

### Security
- SSRF protection in next.config.js (image domain whitelist)
- All dependency vulnerabilities from code review addressed

---

## [1.0.0] - 2026-04-01

### Added
- **Backend**: FastAPI backend with full REST API (articles, auth, comments, admin)
- **Frontend**: Next.js 14 with TypeScript, TailwindCSS, responsive UI
- **Database**: PostgreSQL with zhparser Chinese full-text search
- **Crawler**: RSS + GitHub API采集器 with deduplication
- **Auth**: JWT-based authentication (access + refresh tokens)
- **Content**: UGC投稿 with review workflow
- **Search**: Full-text search with PostgreSQL pg_trgm + zhparser
- **Deployment**: Docker Compose setup for single-server deployment
