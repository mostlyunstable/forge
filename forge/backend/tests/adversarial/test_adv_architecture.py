import pytest
import os
from pathlib import Path
from tests.architecture.test_dependency_rules import (
    TestDomainIsolation,
    TestThirdPartyInfrastructureImports,
    DOMAIN_DIR
)

def test_adversarial_architecture_test_strength(tmp_path):
    """
    Test if the architecture tests actually catch violations.
    We temporarily inject a violation and manually run the test method.
    """
    # Create a fake domain file with an infrastructure import
    fake_domain_file = DOMAIN_DIR / "fake_adv_violation.py"
    
    try:
        # Write an explicit violation: Domain importing Infrastructure and SQLAlchemy
        fake_domain_file.write_text("import sqlalchemy\nfrom forge.infrastructure.database import connection")
        
        # Now run the test methods. They should RAISE an AssertionError
        tester_domain = TestDomainIsolation()
        tester_3p = TestThirdPartyInfrastructureImports()
        
        # 1. Catch internal layer violation
        with pytest.raises(AssertionError) as excinfo1:
            tester_domain.test_domain_has_no_infrastructure_imports()
            
        assert "Domain imports Infrastructure" in str(excinfo1.value)
        
        # 2. Catch 3rd party violation
        with pytest.raises(AssertionError) as excinfo2:
            tester_3p.test_domain_has_no_third_party_infrastructure_imports()
            
        assert "Domain imports third-party infrastructure" in str(excinfo2.value)
        
    finally:
        # Clean up
        if fake_domain_file.exists():
            fake_domain_file.unlink()
