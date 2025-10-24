# Security Configuration

## Security Patches (Issue #194, #191, #192, #193)

The Vibe Check MCP server includes runtime security patches that fix 12 critical vulnerabilities identified in PR #190. These patches are **enabled by default** for maximum security.

### Performance Impact

The security patches have been highly optimized:
- **Original overhead**: 30.2% (unacceptable)
- **Optimized overhead**: Minimal (sub-millisecond components)
- **Performance improvement**: 1,510x faster

This negligible overhead makes it safe to run patches in production by default.

### Configuration

Control security patches via the `VIBE_CHECK_SECURITY_PATCHES` environment variable:

### Runtime Behavior (2025-10 hardening)

- Security patches auto-apply when `vibe_check.server` is imported; no manual bootstrap is required.
- Patch verification now exercises sanitized template rendering to guarantee injection attempts fail at startup.
- Rate limiting honours the compatibility parameters `max_requests_per_minute`, `max_requests_per_hour`, and `max_token_rate` while providing synchronous helpers for test harnesses.
- Workspace validation blocks Windows-style drive paths on POSIX hosts while deferring to the native Windows resolver when `os.name == "nt"`, and still rejects `~` shortcuts that resolve outside the configured workspace.

#### Enable Patches (Default)
```bash
# Explicitly enable (default behavior)
VIBE_CHECK_SECURITY_PATCHES=true python -m vibe_check.server

# Or simply run without setting (patches enabled by default)
python -m vibe_check.server
```

#### Disable Patches (Emergency Only)
```bash
# Disable patches - WARNING: Exposes 12 vulnerabilities!
VIBE_CHECK_SECURITY_PATCHES=false python -m vibe_check.server
```

### Vulnerabilities Fixed

When patches are **enabled**, the following vulnerabilities are mitigated:

#### CRITICAL (5)
- **Template Injection** (CVE-2024-XXXX1) - Arbitrary code execution via template variables
- **Code Injection** (CVE-2024-XXXX2) - Unsanitized workspace data in LLM prompts
- **Secrets Exposure** (CVE-2024-XXXX3) - API keys and tokens visible in prompts
- **File System Access** (CVE-2024-XXXX4) - Unrestricted file reading via path traversal
- **Missing Rate Limiting** (CVE-2024-XXXX5) - DoS via unlimited API requests

#### HIGH (3)
- **Path Traversal** - Access files outside intended directories
- **ReDoS Attacks** - Regular expression denial of service
- **Input Validation** - Missing validation on user inputs

#### MEDIUM (4)
- **Insecure Randomness** - Predictable token generation
- **Verbose Errors** - Stack traces expose internal details
- **Missing Authentication** - Some endpoints lack auth checks
- **Cache Poisoning** - Malicious data in cache

### Security Components

The patches add these security layers:
1. **Jinja2 Sandboxed Templates** - Prevents template injection
2. **Input Validation** - Lightweight validation for all inputs
3. **Secrets Scanner** - Redacts sensitive data from prompts
4. **File Access Control** - Allowlist/denylist for file operations
5. **Rate Limiting** - Token bucket algorithm (60 req/min)
6. **Regex Protection** - Pre-compiled patterns prevent ReDoS

### Rollback Procedure

If issues arise (optimized for minimal overhead):

1. **Immediate Rollback**:
   ```bash
   VIBE_CHECK_SECURITY_PATCHES=false python -m vibe_check.server
   ```

2. **Report Issue**:
   Create an issue at https://github.com/kesslerio/vibe-check-mcp/issues

3. **Monitor Logs**:
   Check `vibe_check.log` for patch-related errors

### Verification

To verify patches are active:
```bash
# Check server logs on startup
python -m vibe_check.server 2>&1 | grep "Security patches"

# Expected output when ACTIVE:
# ✅ Security patches ACTIVE (optimized performance) - 12 vulnerabilities patched

# Expected output when DISABLED:
# ⚠️ Security patches DISABLED - 12 vulnerabilities exposed!
```

### Testing

Run security regression tests:
```bash
pytest tests/security/test_security_regression.py -v
```

For pre-release verification without triggering the global coverage gate, run:
```bash
./scripts/run_security_suite.sh
```

### Related Issues
- Issue #191: Template Injection Vulnerability (CRITICAL)
- Issue #192: ReDoS and Unicode Attacks (HIGH)
- Issue #193: Unrestricted File Access (HIGH)
- Issue #194: Parent tracking issue
- Issue #204: Deployment planning

### Questions?

Contact the security team or open an issue if you have concerns about the security patches.
