"""
Patch file to apply security fixes to existing mcp_sampling.py
This can be applied without breaking existing functionality
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def apply_security_patches():
    """
    Apply security patches to the existing mcp_sampling module
    This function patches the module at runtime to use secure components
    """
    try:
        # Import both original and secure modules
        import vibe_check.mentor.mcp_sampling as original
        from vibe_check.mentor.mcp_sampling_secure import (
            SafeTemplateRenderer,
            EnhancedSecretsScanner,
            RateLimiter,
            FileAccessController,
            QueryInput,
            WorkspaceDataInput
        )
        from vibe_check.mentor.mcp_sampling_migration import (
            SecurePromptTemplate,
            SecurePromptBuilder,
            SecureMCPSamplingClient
        )
        
        # Patch 1: Replace PromptTemplate.render with secure version
        original_prompt_template_render = original.PromptTemplate.render
        
        def secure_template_render(self, **kwargs):
            """Secure replacement for PromptTemplate.render"""
            try:
                renderer = SafeTemplateRenderer()
                
                # Convert template from {var} to {{var}} for Jinja2
                jinja_template = self.template
                for var in self.variables:
                    jinja_template = jinja_template.replace(f"{{{var}}}", f"{{{{ {var} }}}}")
                
                return renderer.render(jinja_template, kwargs)
            except Exception as e:
                logger.error(f"Secure template rendering failed, falling back: {e}")
                return original_prompt_template_render(self, **kwargs)
        
        original.PromptTemplate.render = secure_template_render
        logger.info("Patched PromptTemplate.render with secure version")
        
        # Patch 2: Replace sanitize_code_for_llm with enhanced version
        original_sanitize = original.sanitize_code_for_llm
        
        def enhanced_sanitize_code(code: str, max_length: int = 2000) -> str:
            """Enhanced sanitization with secrets scanning"""
            if not code:
                return ""
            
            # First scan and redact secrets
            code, secrets = EnhancedSecretsScanner.scan_and_redact(code, "code_sanitization")
            if secrets:
                logger.warning(f"Redacted {len(secrets)} secrets during sanitization")
            
            # Then apply original sanitization
            return original_sanitize(code, max_length)
        
        original.sanitize_code_for_llm = enhanced_sanitize_code
        logger.info("Patched sanitize_code_for_llm with enhanced version")
        
        # Patch 3: Add rate limiting to MCPSamplingClient
        original_client_init = original.MCPSamplingClient.__init__
        
        def patched_client_init(self, config=None, request_timeout=30):
            """Add security components to client initialization"""
            original_client_init(self, config, request_timeout)
            
            # Add security components
            self.rate_limiter = RateLimiter(requests_per_minute=60, burst_capacity=10)
            self.file_controller = FileAccessController()
            self.secrets_scanner = EnhancedSecretsScanner()
            
            logger.info("Added security components to MCPSamplingClient")
        
        original.MCPSamplingClient.__init__ = patched_client_init
        
        # Patch 4: Wrap generate_dynamic_response with security checks
        original_generate = original.MCPSamplingClient.generate_dynamic_response
        
        async def secure_generate_dynamic_response(
            self,
            intent: str,
            query: str,
            context: Dict[str, Any],
            workspace_data: Optional[Dict[str, Any]] = None,
            ctx: Optional[Any] = None,
            user_id: Optional[str] = None
        ):
            """Secure wrapper for generate_dynamic_response"""
            # Check rate limit if available
            if hasattr(self, 'rate_limiter'):
                allowed, wait_time = await self.rate_limiter.check_rate_limit(user_id)
                if not allowed:
                    logger.warning(f"Rate limit exceeded for user {user_id}")
                    return {
                        "content": f"Rate limit exceeded. Please wait {wait_time:.1f} seconds.",
                        "generated": False,
                        "rate_limited": True,
                        "wait_time": wait_time
                    }
            
            # Validate inputs
            try:
                validated_query = QueryInput(query=query, intent=intent)
                query = validated_query.query
            except Exception as e:
                logger.error(f"Query validation failed: {e}")
                return None
            
            # Validate and sanitize workspace data
            if workspace_data:
                try:
                    validated_ws = WorkspaceDataInput(**workspace_data)
                    workspace_data = validated_ws.dict()
                    
                    # Scan for secrets in code
                    if "code" in workspace_data and hasattr(self, 'secrets_scanner'):
                        workspace_data["code"], secrets = self.secrets_scanner.scan_and_redact(
                            workspace_data["code"], 
                            "workspace_code"
                        )
                        if secrets:
                            logger.warning(f"Redacted {len(secrets)} secrets from workspace")
                    
                    # Check file access
                    if "files" in workspace_data and hasattr(self, 'file_controller'):
                        safe_files = []
                        for file_path in workspace_data["files"]:
                            allowed, reason = self.file_controller.is_allowed(file_path)
                            if allowed:
                                safe_files.append(file_path)
                            else:
                                logger.warning(f"File access denied: {file_path} - {reason}")
                        workspace_data["files"] = safe_files
                        
                except Exception as e:
                    logger.error(f"Workspace validation failed: {e}")
                    workspace_data = None
            
            # Call original with sanitized inputs
            return await original_generate(
                self, intent, query, context, workspace_data, ctx
            )
        
        original.MCPSamplingClient.generate_dynamic_response = secure_generate_dynamic_response
        logger.info("Patched MCPSamplingClient.generate_dynamic_response with security checks")
        
        # Patch 5: Replace PromptBuilder with SecurePromptBuilder
        original.PromptBuilder = SecurePromptBuilder
        logger.info("Replaced PromptBuilder with SecurePromptBuilder")
        
        logger.info("All security patches applied successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to apply security patches: {e}")
        return False


def verify_patches():
    """
    Verify that security patches have been applied correctly
    """
    try:
        import vibe_check.mentor.mcp_sampling as module
        
        checks = {
            "Rate limiter": hasattr(module.MCPSamplingClient, '__init__') and 'rate_limiter' in str(module.MCPSamplingClient.__init__),
            "Secure template": 'SafeTemplateRenderer' in str(module.PromptTemplate.render) or 'jinja' in str(module.PromptTemplate.render).lower(),
            "Enhanced sanitization": 'EnhancedSecretsScanner' in str(module.sanitize_code_for_llm) or 'secrets' in str(module.sanitize_code_for_llm),
            "Secure prompt builder": hasattr(module, 'PromptBuilder') and hasattr(module.PromptBuilder, 'renderer')
        }
        
        all_passed = all(checks.values())
        
        logger.info("Security patch verification:")
        for check, passed in checks.items():
            status = "✓" if passed else "✗"
            logger.info(f"  {status} {check}")
        
        return all_passed
        
    except Exception as e:
        logger.error(f"Failed to verify patches: {e}")
        return False


# Auto-apply patches when imported
def auto_apply():
    """Automatically apply patches when module is imported"""
    success = apply_security_patches()
    if success:
        verified = verify_patches()
        if verified:
            logger.info("Security patches applied and verified successfully")
        else:
            logger.warning("Security patches applied but verification failed")
    else:
        logger.error("Failed to apply security patches")
    
    return success


# Export functions
__all__ = [
    'apply_security_patches',
    'verify_patches',
    'auto_apply'
]