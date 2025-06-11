#!/usr/bin/env python3
"""
Test script for MLFlow 3.0 migration validation.

This script tests the key migration components to ensure everything works correctly.
"""

import os
import tempfile
from pathlib import Path

def test_imports():
    """Test that all required imports work."""
    print("Testing imports...")
    
    try:
        import mlflow
        print(f"✓ MLFlow version: {mlflow.__version__}")
        
        # Check if we have MLFlow 3.x
        major_version = int(mlflow.__version__.split('.')[0])
        if major_version >= 3:
            print("✓ MLFlow 3.x detected")
        else:
            print(f"⚠ MLFlow version {mlflow.__version__} detected, 3.x recommended")
            
        # Test key MLFlow 3 components
        from mlflow.models import infer_signature
        print("✓ infer_signature import successful")
        
        import mlflow.pyfunc
        print("✓ mlflow.pyfunc import successful")
        
        # Test other dependencies
        import dspy
        print(f"✓ DSPy version: {dspy.__version__}")
        
        from openai import OpenAI
        print("✓ OpenAI import successful")
        
        from PIL import Image
        print("✓ Pillow import successful")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_model_file_structure():
    """Test that model files exist and are properly structured."""
    print("\nTesting model file structure...")
    
    base_path = Path("open_llms_play_pokemon/agents")
    
    # Check if model files exist
    model_files = [
        "dspy_pokemon_model.py",
        "openai_pokemon_model.py", 
        "log_models_mlflow3.py",
        "main_dspy_mlflow3.py"
    ]
    
    all_exist = True
    for file in model_files:
        file_path = base_path / file
        if file_path.exists():
            print(f"✓ {file} exists")
        else:
            print(f"✗ {file} missing")
            all_exist = False
    
    # Check model files contain required components
    if all_exist:
        dspy_model_path = base_path / "dspy_pokemon_model.py"
        with open(dspy_model_path, 'r') as f:
            content = f.read()
            
        if "mlflow.pyfunc.PythonModel" in content:
            print("✓ DSPy model inherits from PythonModel")
        else:
            print("✗ DSPy model missing PythonModel inheritance")
            all_exist = False
            
        if "mlflow.models.set_model" in content:
            print("✓ DSPy model contains set_model call")
        else:
            print("✗ DSPy model missing set_model call")
            all_exist = False
    
    return all_exist


def test_signature_inference():
    """Test signature inference functionality."""
    print("\nTesting signature inference...")
    
    try:
        from mlflow.models import infer_signature
        
        # Test with sample data
        input_example = {"action": "start_game", "headless": True}
        output_example = {
            "status": "success",
            "screen_base64": "base64_string",
            "action_executed": "test_action",
            "success": True
        }
        
        signature = infer_signature(input_example, output_example)
        print("✓ Signature inference successful")
        print(f"  Input schema: {signature.inputs}")
        print(f"  Output schema: {signature.outputs}")
        
        return True
        
    except Exception as e:
        print(f"✗ Signature inference failed: {e}")
        return False


def test_model_logging_api():
    """Test the MLFlow 3 model logging API without actually logging."""
    print("\nTesting model logging API...")
    
    try:
        import mlflow
        import mlflow.pyfunc
        from mlflow.models import infer_signature
        
        # Test that we can access the new API
        log_model_func = getattr(mlflow.pyfunc, 'log_model', None)
        if log_model_func is None:
            print("✗ mlflow.pyfunc.log_model not available")
            return False
            
        print("✓ mlflow.pyfunc.log_model API accessible")
        
        # Check for required parameters in MLFlow 3
        import inspect
        signature = inspect.signature(log_model_func)
        params = list(signature.parameters.keys())
        
        required_params = ['name', 'python_model']  # New in MLFlow 3
        for param in required_params:
            if param in params:
                print(f"✓ Parameter '{param}' available")
            else:
                print(f"✗ Parameter '{param}' missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Model logging API test failed: {e}")
        return False


def test_environment_setup():
    """Test environment and configuration."""
    print("\nTesting environment setup...")
    
    # Check for environment variables
    env_vars = [
        "OPENROUTER_API_KEY",
        "OPENAI_API_KEY"
    ]
    
    for var in env_vars:
        if os.getenv(var):
            print(f"✓ {var} is set")
        else:
            print(f"⚠ {var} not set (may be required for full functionality)")
    
    # Check Python version compatibility
    import sys
    python_version = sys.version_info
    if python_version.major == 3 and python_version.minor >= 10:
        print(f"✓ Python version {python_version.major}.{python_version.minor} is compatible")
    else:
        print(f"⚠ Python version {python_version.major}.{python_version.minor} may not be optimal")
    
    return True


def test_mlflow_tracking_setup():
    """Test basic MLFlow tracking setup."""
    print("\nTesting MLFlow tracking setup...")
    
    try:
        import mlflow
        
        # Test setting tracking URI
        mlflow.set_tracking_uri("file:///tmp/mlflow_test")
        print("✓ Tracking URI set successfully")
        
        # Test experiment creation
        experiment_name = "test_migration_experiment"
        mlflow.set_experiment(experiment_name)
        print("✓ Experiment creation successful")
        
        # Test basic run functionality
        with mlflow.start_run():
            mlflow.log_param("test_param", "test_value")
            mlflow.set_tag("test_tag", "test_value")
            print("✓ Basic run functionality works")
        
        return True
        
    except Exception as e:
        print(f"✗ MLFlow tracking setup failed: {e}")
        return False


def run_all_tests():
    """Run all migration tests."""
    print("="*60)
    print("MLFlow 3.0 Migration Validation Tests")
    print("="*60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Model File Structure", test_model_file_structure),
        ("Signature Inference", test_signature_inference),
        ("Model Logging API", test_model_logging_api),
        ("Environment Setup", test_environment_setup),
        ("MLFlow Tracking", test_mlflow_tracking_setup),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * len(test_name))
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:.<40} {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Migration appears successful.")
        return True
    else:
        print(f"⚠ {total - passed} test(s) failed. Please review the issues above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)