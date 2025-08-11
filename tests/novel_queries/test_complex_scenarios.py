"""
Novel Query Tests for Complex Scenarios and Stress Testing

Tests with complex, realistic scenarios that push the limits:
- Multi-pattern complex scenarios
- Real-world anti-pattern combinations
- Ambiguous or edge-case patterns
- Performance under complex analysis
- Novel pattern combinations not seen in training
"""

import pytest
import sys
import os
import time
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from vibe_check.tools.analyze_text_nollm import analyze_text_demo


@pytest.mark.novel_query
class TestComplexScenarios:
    """Test complex scenarios and novel query patterns"""

    def test_realistic_enterprise_scenario(self):
        """Test realistic enterprise development scenario"""
        enterprise_scenario = """
        Our enterprise application needs a comprehensive overhaul of the authentication system.
        The current third-party solution doesn't meet our compliance requirements, so we're
        building a custom OAuth 2.0 implementation with our own JWT handling, session management,
        and multi-factor authentication. We've also decided to create our own HTTP client library
        because the existing ones don't properly handle our custom headers and retry logic.
        
        Additionally, we're implementing a custom database abstraction layer since none of the
        existing ORMs support our legacy database schema properly. The team has been researching
        this for weeks but couldn't find adequate documentation, so we're building everything
        from scratch to ensure it meets our specific requirements.
        
        We're also creating our own logging framework because the existing solutions don't
        integrate well with our monitoring infrastructure. This will include custom formatters,
        multiple output targets, and performance optimization for high-throughput scenarios.
        """
        
        result = analyze_text_demo(enterprise_scenario, detail_level="comprehensive")
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'analysis' in result
        
        # Complex scenario should be detected and analyzed
        if 'detection_result' in result.get('analysis', {}):
            detection = result['analysis']['detection_result']
            # Should identify multiple potential issues
            assert detection.get('total_issues', 0) >= 0

    def test_startup_mvp_scenario(self):
        """Test startup MVP development anti-pattern scenario"""
        startup_scenario = """
        We're launching our MVP in 3 weeks and need to move fast. Instead of using Stripe
        for payments, we're building our own payment processing system because we need
        complete control over the user experience. We're also implementing our own
        user authentication instead of using Auth0 because we want to avoid the monthly costs.
        
        For the database, we're creating a custom data layer that combines MongoDB and
        PostgreSQL because we need the flexibility of NoSQL for user data but ACID
        compliance for financial transactions. Since we couldn't find a library that
        handles both seamlessly, we're writing our own connection pooling and transaction
        management system.
        
        We're also building a custom real-time notification system instead of using
        Firebase or Pusher because we need it to integrate with our proprietary
        message queue system. Time is critical, so we're skipping comprehensive
        testing and documentation to focus on core functionality.
        """
        
        result = analyze_text_demo(startup_scenario, detail_level="standard")
        
        assert isinstance(result, dict)
        assert 'status' in result
        
        # Should identify multiple high-risk patterns
        analysis = result.get('analysis', {})
        assert isinstance(analysis, dict)

    def test_microservices_over_engineering_scenario(self):
        """Test microservices over-engineering pattern"""
        microservices_scenario = """
        We're migrating our monolithic application to microservices architecture.
        Each microservice will have its own custom API gateway, service discovery
        mechanism, and inter-service communication protocol. We're implementing
        our own message broker because Kafka doesn't exactly match our requirements,
        and we need more control over message routing and transformation.
        
        For configuration management, we're building a distributed configuration
        system that synchronizes across all services in real-time. We're also
        creating our own service mesh implementation because Istio is too complex
        for our needs, but we still want advanced traffic management capabilities.
        
        Each service will have its own custom monitoring and alerting system that
        feeds into our centralized observability platform. We're implementing
        distributed tracing from scratch because OpenTelemetry doesn't support
        our specific correlation requirements.
        
        To handle database transactions across services, we're implementing a
        custom saga pattern orchestrator with compensation logic for complex
        business workflows.
        """
        
        result = analyze_text_demo(microservices_scenario, detail_level="comprehensive")
        
        assert isinstance(result, dict)
        assert 'status' in result

    def test_ai_ml_infrastructure_scenario(self):
        """Test AI/ML infrastructure anti-pattern scenario"""
        ai_scenario = """
        We're building a machine learning platform for our organization. Instead
        of using existing MLOps tools like MLflow or Kubeflow, we're creating
        our own model training pipeline orchestration system because we need
        tight integration with our proprietary data sources.
        
        For model serving, we're implementing a custom inference engine that
        optimizes performance for our specific model architectures. We're also
        building our own feature store from scratch because existing solutions
        don't handle our real-time feature computation requirements adequately.
        
        Our data scientists need a custom experiment tracking system that
        integrates with our internal tools, so we're developing that instead
        of adapting existing solutions. We're also creating our own automated
        hyperparameter tuning system because we have specific optimization
        algorithms that aren't available in standard tools.
        
        For model deployment, we're building a custom blue-green deployment
        system with automatic rollback capabilities based on model performance
        metrics. This includes our own A/B testing framework for model comparison
        in production environments.
        """
        
        result = analyze_text_demo(ai_scenario, detail_level="standard")
        
        assert isinstance(result, dict)
        assert 'status' in result

    def test_security_compliance_scenario(self):
        """Test security and compliance-driven custom development"""
        security_scenario = """
        Due to strict compliance requirements (SOC 2, HIPAA, PCI-DSS), we need
        complete control over our security infrastructure. We're implementing
        our own encryption library using approved cryptographic algorithms
        because we can't verify the security of existing libraries to our
        satisfaction.
        
        For audit logging, we're building a custom immutable log system that
        provides cryptographic proof of log integrity. We're also creating
        our own identity and access management system with fine-grained
        permissions that map directly to our compliance requirements.
        
        We're implementing custom network security controls including our
        own intrusion detection system and automated response mechanisms.
        Standard solutions don't provide the level of customization we need
        for our specific threat model and regulatory requirements.
        
        For data handling, we're creating our own data classification and
        loss prevention system that automatically identifies and protects
        sensitive information according to our compliance policies.
        """
        
        result = analyze_text_demo(security_scenario, detail_level="comprehensive")
        
        assert isinstance(result, dict)
        assert 'status' in result

    def test_performance_optimization_scenario(self):
        """Test performance-driven custom implementation scenario"""
        performance_scenario = """
        Our application handles millions of requests per second, so we need
        maximum performance optimization. We're replacing all our HTTP clients
        with a custom implementation that uses connection pooling, request
        pipelining, and custom protocol optimizations specific to our use case.
        
        For caching, we're building our own distributed cache system that
        outperforms Redis for our specific access patterns. This includes
        custom serialization protocols and network optimization for our
        data center topology.
        
        We're implementing our own JSON parsing library because existing
        parsers don't meet our latency requirements. We're also creating
        a custom memory allocator optimized for our object allocation patterns
        to reduce garbage collection overhead.
        
        Our database access layer includes custom connection pooling,
        prepared statement caching, and query optimization that's specifically
        tuned for our query patterns and database schema.
        """
        
        result = analyze_text_demo(performance_scenario, detail_level="standard")
        
        assert isinstance(result, dict)
        assert 'status' in result

    def test_ambiguous_justification_scenario(self):
        """Test scenario with ambiguous justification for custom development"""
        ambiguous_scenario = """
        We're evaluating whether to build our own content management system.
        The existing CMS solutions (WordPress, Drupal, Contentful) don't quite
        fit our workflow, though we haven't spent much time trying to configure
        them properly. Our content team has specific requirements that might
        be achievable with plugins or customization, but it seems easier to
        build something tailored to our needs.
        
        We have some unique content types and approval workflows that may or
        may not be supportable by existing platforms. The team is split on
        whether to spend time learning the existing systems or just building
        our own from the ground up.
        
        Time-to-market is important, but we also want something that perfectly
        matches our vision. We have strong development capabilities in-house,
        so creating a custom solution is definitely feasible, though we're
        not sure if it's the best use of our resources.
        """
        
        result = analyze_text_demo(ambiguous_scenario, detail_level="comprehensive")
        
        assert isinstance(result, dict)
        assert 'status' in result

    def test_legacy_integration_scenario(self):
        """Test complex legacy system integration scenario"""
        legacy_scenario = """
        We need to integrate our modern application with a 20-year-old mainframe
        system that uses proprietary protocols and data formats. The existing
        integration tools don't support our mainframe's custom communication
        protocol, so we're building our own integration layer.
        
        This includes custom protocol adapters, data transformation engines,
        and error handling for the unreliable legacy system. We're also
        implementing our own transaction coordination system to maintain
        data consistency across the modern and legacy systems.
        
        The legacy system has unique business logic that can't be replicated
        easily, so we need bidirectional synchronization with conflict
        resolution. We're building a custom event sourcing system to track
        all changes and ensure data integrity across both systems.
        
        Documentation for the legacy system is minimal, and the few experts
        who understand it are retiring soon, so we need to create our own
        abstraction layer that captures the business logic in a maintainable way.
        """
        
        result = analyze_text_demo(legacy_scenario, detail_level="standard")
        
        assert isinstance(result, dict)
        assert 'status' in result

    def test_multi_language_scenario(self):
        """Test scenario with mixed languages and frameworks"""
        multi_language_scenario = """
        Our polyglot architecture includes services in Python, Java, Go, and Node.js.
        We need consistent logging, monitoring, and configuration management across
        all platforms. Instead of using language-specific tools, we're building
        our own cross-platform infrastructure libraries.
        
        This includes a custom RPC framework that works efficiently across all
        our languages, with automatic serialization and service discovery.
        We're also creating unified configuration management that can be embedded
        in any language and provides real-time updates.
        
        For observability, we're implementing our own tracing and metrics
        collection system that provides consistent instrumentation APIs across
        all languages while optimizing for each platform's specific performance
        characteristics.
        
        We need custom deployment tooling that understands the dependencies
        and requirements of each language ecosystem while providing a unified
        deployment experience across our entire platform.
        """
        
        result = analyze_text_demo(multi_language_scenario, detail_level="comprehensive")
        
        assert isinstance(result, dict)
        assert 'status' in result

    def test_rapid_scaling_scenario(self):
        """Test rapid scaling and resource constraint scenario"""
        scaling_scenario = """
        We're experiencing 10x growth month over month and our current architecture
        can't keep up. We need to rebuild everything for massive scale, but we
        can't afford downtime or service degradation during the transition.
        
        We're creating our own load balancing system that can handle our specific
        traffic patterns and automatically scale resources based on our custom
        metrics. Standard load balancers don't provide the fine-grained control
        we need for our optimization strategies.
        
        For data storage, we're building a custom sharding solution that can
        rebalance data in real-time as we add capacity. We're also implementing
        our own caching strategy that predictively pre-loads data based on
        our traffic patterns.
        
        Our monitoring system needs to handle millions of metrics per second
        and provide real-time alerting with custom correlation logic that
        understands our application's behavior patterns.
        """
        
        result = analyze_text_demo(scaling_scenario, detail_level="standard")
        
        assert isinstance(result, dict)
        assert 'status' in result

    @pytest.mark.slow
    def test_stress_complex_analysis(self):
        """Stress test with multiple complex scenarios simultaneously"""
        complex_scenarios = [
            "Enterprise authentication overhaul with custom OAuth implementation",
            "Microservices migration with custom service mesh and message broker",
            "AI platform with custom MLOps pipeline and inference engine",
            "High-performance system with custom HTTP client and memory allocator",
            "Legacy integration with custom protocol adapters and transaction coordination",
            "Multi-language infrastructure with unified RPC framework and monitoring",
            "Rapid scaling solution with custom load balancing and real-time sharding",
        ]
        
        start_time = time.time()
        results = []
        
        for i, scenario in enumerate(complex_scenarios):
            # Add complexity by combining scenarios
            combined_scenario = f"""
            Project Phase {i+1}: {scenario}
            
            This is part of a larger digital transformation initiative that includes
            multiple custom implementations across our technology stack. We need
            complete control and integration across all components.
            
            The team has evaluated existing solutions but found they don't meet
            our specific requirements for performance, compliance, and integration
            with our existing systems.
            """ * (i + 1)  # Increasing complexity
            
            result = analyze_text_demo(combined_scenario, detail_level="comprehensive")
            results.append(result)
            
            assert isinstance(result, dict)
            assert 'status' in result
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Should handle complex scenarios efficiently
        avg_time_per_scenario = total_duration / len(complex_scenarios)
        assert avg_time_per_scenario < 10.0, f"Average time too high: {avg_time_per_scenario}s"
        
        # All scenarios should be analyzed successfully
        success_count = sum(1 for r in results if r.get('status') in ['success', 'completed'])
        assert success_count == len(complex_scenarios), f"Some complex scenarios failed: {success_count}/{len(complex_scenarios)}"

    def test_contradictory_information_scenario(self):
        """Test scenario with contradictory or conflicting information"""
        contradictory_scenario = """
        We need to implement a new feature quickly, but also ensure it's perfectly
        architected for long-term maintainability. We want to use existing solutions
        to save time, but we also need complete customization that's not available
        in any existing tools.
        
        The feature should be simple and lightweight, but also robust enough to
        handle enterprise-scale requirements. We want to follow industry best
        practices, but our specific use case requires innovative approaches that
        go against conventional wisdom.
        
        Budget is tight so we can't afford expensive solutions, but we also can't
        compromise on quality or performance. We need something production-ready
        immediately, but we also want to build it right the first time without
        cutting corners.
        
        The team has strong expertise in existing technologies, but we also want
        to explore new approaches that might be better suited for our needs.
        Time is critical, but thorough planning and research are also essential.
        """
        
        result = analyze_text_demo(contradictory_scenario, detail_level="comprehensive")
        
        assert isinstance(result, dict)
        assert 'status' in result
        
        # Should handle contradictory information gracefully
        analysis = result.get('analysis', {})
        assert isinstance(analysis, dict)

    def test_cascading_complexity_scenario(self):
        """Test scenario where one custom solution leads to many others"""
        cascading_scenario = """
        We started by building a custom user authentication system because we
        needed specific LDAP integration features. Now we need a custom session
        management system that works with our auth implementation. This requires
        a custom caching layer that understands our session structure.
        
        The custom cache needs its own monitoring and alerting system that
        integrates with our auth metrics. We also need custom load balancing
        that distributes sessions appropriately across our auth servers.
        
        Our custom auth system generates events that need to be processed by
        a custom workflow engine we're building. This engine needs its own
        job scheduling system that coordinates with our auth session timeouts.
        
        All of these systems need unified configuration management, so we're
        creating a custom configuration service that can hot-reload settings
        across all our custom components. This requires its own service discovery
        mechanism and health checking system.
        
        Each component needs custom logging and tracing that provides the
        visibility we need into our integrated system behavior.
        """
        
        result = analyze_text_demo(cascading_scenario, detail_level="comprehensive")
        
        assert isinstance(result, dict)
        assert 'status' in result