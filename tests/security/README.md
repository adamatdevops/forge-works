# Security Testing

ForgeWorks security testing suite using OWASP ZAP and related tools.

## OWASP ZAP Configuration

The `zap-config.yaml` file configures the OWASP ZAP Automation Framework for security scanning.

### Prerequisites

- Docker installed and running
- Backend API running on `http://localhost:8000`

### Running the Security Scan

```bash
# From the project root directory
docker run -v $(pwd):/zap/wrk:rw ghcr.io/zaproxy/zaproxy:stable \
  zap.sh -cmd -autorun /zap/wrk/tests/security/zap-config.yaml
```

### What the Scan Does

1. **Spider**: Crawls the application to discover endpoints
   - Max duration: 5 minutes
   - Max depth: 5 levels
   - Max children per node: 10

2. **OpenAPI Import**: Imports API spec from `/openapi.json`
   - Ensures all documented endpoints are tested

3. **Active Scan**: Tests for vulnerabilities
   - Uses "API-Minimal" policy
   - Max scan duration: 30 minutes
   - Tests for OWASP Top 10 vulnerabilities

4. **Passive Scan**: Analyzes responses for security issues
   - Max duration: 5 minutes

5. **Reports**: Generates HTML and JSON reports
   - Output directory: `tests/security/reports/`

### Report Files

After running, reports are generated in `tests/security/reports/`:

- `zap-report.html` - Human-readable HTML report
- `zap-report.json` - Machine-readable JSON report for CI integration

### Configuring Authentication

If the API requires authentication, uncomment and configure the authentication section in `zap-config.yaml`:

```yaml
authentication:
  method: "form"
  parameters:
    loginUrl: "http://localhost:8000/api/v1/auth/login"
    loginRequestData: "email={%username%}&password={%password%}"
  verification:
    method: "response"
    loggedInRegex: "\\Qaccess_token\\E"
```

### CI Integration

Add to your CI pipeline:

```yaml
security-scan:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4

    - name: Start API Server
      run: |
        docker compose up -d api
        sleep 10

    - name: Run ZAP Scan
      run: |
        mkdir -p tests/security/reports
        docker run -v $(pwd):/zap/wrk:rw \
          --network host \
          ghcr.io/zaproxy/zaproxy:stable \
          zap.sh -cmd -autorun /zap/wrk/tests/security/zap-config.yaml

    - name: Upload Security Report
      uses: actions/upload-artifact@v4
      with:
        name: zap-security-report
        path: tests/security/reports/

    - name: Check for Critical Issues
      run: |
        if grep -q '"risk": "High"' tests/security/reports/zap-report.json; then
          echo "High risk vulnerabilities found!"
          exit 1
        fi
```

### Excluded Paths

The following are excluded from scanning:
- Static assets (`.js`, `.css`, images, fonts)
- These don't contain security vulnerabilities in the traditional sense

### Scan Policies

The default "API-Minimal" policy is configured for API testing. For full application scanning, change the policy in `zap-config.yaml`:

```yaml
- type: activeScan
  parameters:
    policy: "Default Policy"  # Full scan
```

## Additional Security Tools

### Trivy (Container Scanning)

```bash
# Scan Docker images for vulnerabilities
trivy image forge-works/api:latest
trivy image forge-works/frontend:latest
```

### npm audit (Dependency Scanning)

```bash
# Frontend dependencies
cd src/frontend && npm audit

# Fix automatically where possible
npm audit fix
```

### pip-audit (Python Dependency Scanning)

```bash
# Backend dependencies
cd src/backend && pip-audit
```

## Security Checklist

Before release, verify:

- [ ] ZAP scan completed with no High/Critical issues
- [ ] Container images scanned with Trivy
- [ ] npm audit shows no high/critical vulnerabilities
- [ ] pip-audit shows no high/critical vulnerabilities
- [ ] Secrets scanning (e.g., gitleaks) passed
- [ ] HTTPS enforced in production
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Input validation in place
- [ ] Authentication tokens properly secured
