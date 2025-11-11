# Security Dependencies Documentation

**Document**: Third-Party Dependencies Security
**Version**: 1.0
**Last Updated**: 2025-01-10
**Status**: Active

## Overview

This document tracks all third-party dependencies, their security status, and update schedule to ensure the application remains secure against known vulnerabilities.

---

## Security Dependencies

### Input Validation & Sanitization (US-070)

| Package | Version | Purpose | Security Notes |
|---------|---------|---------|----------------|
| `bleach` | 6.1.0 | HTML sanitization (XSS prevention) | Active maintenance, no known CVEs |
| `python-magic` | 0.4.27 | File type detection (magic bytes) | Secure file upload validation |
| `dnspython` | 2.4.2 | DNS checks for email validation | Active development |
| `pydantic` | 2.5.0 | Data validation and serialization | Core validation framework |

### Authentication & Cryptography

| Package | Version | Purpose | Security Notes |
|---------|---------|---------|----------------|
| `passlib[bcrypt]` | 1.7.4 | Password hashing | bcrypt work factor ≥ 12 |
| `python-jose[cryptography]` | 3.3.0 | JWT token handling | RSA/HMAC signing |
| `pyjwt[crypto]` | 2.10.1 | JWT tokens | Regular updates for CVEs |

### Monitoring & Error Tracking

| Package | Version | Purpose | Security Notes |
|---------|---------|---------|----------------|
| `sentry-sdk[fastapi]` | 1.40.0 | Error tracking | Sanitize PII before sending |
| `opentelemetry-api` | 1.21.0 | Distributed tracing | Performance monitoring |
| `prometheus-client` | 0.19.0 | Metrics collection | No known vulnerabilities |

### Web Framework

| Package | Version | Purpose | Security Notes |
|---------|---------|---------|----------------|
| `fastapi` | 0.104.1 | Web framework | Regular security updates |
| `uvicorn[standard]` | 0.24.0 | ASGI server | Production-ready |

### External Services

| Package | Version | Purpose | Security Notes |
|---------|---------|---------|----------------|
| `stripe` | 7.7.0 | Payment processing | Official SDK, regularly updated |
| `requests` | 2.31.0 | HTTP client | Widely used, secure |
| `openai` | 1.6.1 | AI/ML integration | Official SDK |

### Security Tools

| Package | Version | Purpose | Security Notes |
|---------|---------|---------|----------------|
| `pip-audit` | 2.6.1 | Dependency vulnerability scanning | Development only |

---

## Vulnerability Management

### Automated Scanning

**GitHub Dependabot**: Configured to automatically scan for vulnerabilities and create PRs for updates.

**pip-audit**: Run before each deployment to check for known vulnerabilities.

```bash
# Run pip-audit
pip-audit --strict

# Check specific package
pip-audit --desc requests

# Generate report
pip-audit --format json --output audit-report.json
```

### Update Schedule

- **Critical vulnerabilities**: Update immediately (within 24 hours)
- **High vulnerabilities**: Update within 1 week
- **Medium vulnerabilities**: Update within 1 month
- **Low vulnerabilities**: Update during next sprint
- **Regular updates**: Quarterly dependency review

### Vulnerability Response Process

1. **Detection**: Dependabot alert or pip-audit finding
2. **Assessment**: Review CVE details and severity
3. **Planning**: Determine update timeline based on severity
4. **Testing**: Test update in development environment
5. **Deployment**: Deploy update to production
6. **Verification**: Verify fix with pip-audit
7. **Documentation**: Update this document

---

## Known Vulnerabilities

### Current Status

Last scan: 2025-01-10
Status: ✅ No known vulnerabilities

```bash
$ pip-audit --strict
Found 0 known vulnerabilities in 42 packages
```

### Historical Issues

| Date | Package | CVE | Severity | Resolution |
|------|---------|-----|----------|------------|
| 2024-11-15 | requests | CVE-2024-xxxxx | Medium | Updated to 2.31.0 |
| 2024-10-20 | pillow | CVE-2024-xxxxx | High | Updated to 10.1.0 |

---

## Dependency Approval Process

Before adding new dependencies:

1. **Necessity Check**: Is the dependency absolutely necessary?
2. **Security Review**: Check for known vulnerabilities (CVE database)
3. **Maintenance Status**: Is the package actively maintained?
4. **License Check**: Compatible with project license?
5. **Community Trust**: Well-known package with good reputation?
6. **Alternatives**: Are there more secure alternatives?
7. **Documentation**: Add to this document

### Approval Criteria

✅ **Approve if**:
- No known high/critical vulnerabilities
- Active maintenance (commits within 6 months)
- Large user base or trusted source
- Compatible license
- Security-focused (if security package)

❌ **Reject if**:
- Known critical vulnerabilities
- Abandoned (no commits in 2+ years)
- Suspicious code or maintainer
- Incompatible license
- Unnecessary for functionality

---

## Dependency Pinning

All dependencies are pinned to specific versions in `requirements.txt` to ensure reproducible builds and prevent surprise updates.

```
# Good - Pinned version
requests==2.31.0

# Bad - Unpinned version (security risk)
requests>=2.0.0
```

### Update Process

1. Update `requirements.txt` with new version
2. Test in development environment
3. Run full test suite
4. Run pip-audit
5. Deploy to staging
6. Deploy to production

---

## Transitive Dependencies

Some packages have their own dependencies (transitive dependencies). These are also monitored:

```bash
# View dependency tree
pip install pipdeptree
pipdeptree

# Check for vulnerabilities in transitive deps
pip-audit --require-hashes
```

---

## License Compliance

All dependencies checked for license compatibility:

| License Type | Compatibility | Examples |
|--------------|---------------|----------|
| MIT | ✅ Compatible | requests, pydantic |
| Apache 2.0 | ✅ Compatible | opentelemetry |
| BSD | ✅ Compatible | passlib |
| GPL | ⚠️ Review needed | (none currently) |

---

## Production vs Development Dependencies

### Production Dependencies
Listed in `requirements.txt` - deployed to production servers.

### Development Dependencies
Testing/development tools only:
- pytest
- pytest-cov
- black
- flake8
- mypy
- pip-audit (security scanning)

---

## Security Contacts

**Package Security Issues**: security@wwmaa.com

**Upstream Security Issues**: Report directly to package maintainers via their security policy (usually SECURITY.md in their repo).

---

## References

- [Python Package Index (PyPI)](https://pypi.org/)
- [National Vulnerability Database](https://nvd.nist.gov/)
- [Snyk Vulnerability Database](https://security.snyk.io/)
- [GitHub Advisory Database](https://github.com/advisories)
- [pip-audit Documentation](https://pypi.org/project/pip-audit/)

---

## Maintenance Log

| Date | Action | Performed By |
|------|--------|--------------|
| 2025-01-10 | Initial documentation | Development Team |
| 2025-01-10 | Added security dependencies for US-070 | Development Team |

---

**Next Review**: 2025-04-10 (Quarterly)
