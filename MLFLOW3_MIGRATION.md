# MLFlow 3.0 Migration Guide

This document outlines the migration of the Pokemon Red AI agents to MLFlow 3.0 and demonstrates the new model logging capabilities using `mlflow.pyfunc.log_model`.

## Overview

MLFlow 3.0 introduces significant improvements for AI model management, particularly beneficial for GenAI applications and agent-based systems. The key innovation is the **"Models from Code"** logging approach, which allows logging models as code rather than serialized objects.

## What Changed in MLFlow 3.0

### Key Differences from MLFlow 2.x

1. **Models from Code Logging**: Log models as code files instead of pickled objects
2. **New `name` parameter**: Use `name` instead of `artifact_path` in `log_model()`
3. **LoggedModel concept**: Models are first-class citizens, not just run artifacts
4. **Model artifact storage**: Stored under `models/` instead of `runs/`
5. **No active run required**: Can log models without `mlflow.start_run()`

### Benefits for Our Use Case

- **Agent-based models**: Perfect for our Pokemon Red agents that are code-based rather than trained models
- **External API integration**: Ideal for models that call external services (OpenAI, OpenRouter)
- **Reproducibility**: Code-based logging ensures exact model behavior reproduction
- **Version control**: Better integration with code versioning systems

## Migration Steps

### 1. Update Dependencies

```toml
# pyproject.toml
[dependency-groups]
dev = [
    # ... other dependencies
    "mlflow>=3.0.0",  # Updated from mlflow>=2.22.1
]
```

### 2. Create MLFlow-Compatible Model Classes

We created new model wrapper classes that inherit from `mlflow.pyfunc.PythonModel`:

- `PokemonRedDSPyModel` - Wraps the DSPy-based agent
- `PokemonRedOpenAIModel` - Wraps the OpenAI-based agent

These classes follow the MLFlow 3 "Models from Code" pattern with:
- `load_context()` method for initialization
- `predict()` method for inference
- `mlflow.models.set_model()` call at the end

### 3. Implement Model Logging

The new logging approach uses:

```python
model_info = mlflow.pyfunc.log_model(
    name="dspy_pokemon_agent",  # New: 'name' instead of 'artifact_path'
    python_model="path/to/model_code.py",  # Path to model code file
    signature=signature,
    input_example=input_example,
    pip_requirements=[...],
    metadata={...}
)
```

## New Files Created

### Model Definitions
- `open_llms_play_pokemon/agents/dspy_pokemon_model.py` - DSPy agent as MLFlow model
- `open_llms_play_pokemon/agents/openai_pokemon_model.py` - OpenAI agent as MLFlow model

### Scripts and Examples
- `open_llms_play_pokemon/agents/log_models_mlflow3.py` - Model logging demonstration
- `open_llms_play_pokemon/agents/main_dspy_mlflow3.py` - Updated main script with MLFlow 3

## Usage Examples

### Logging Models

```python
from open_llms_play_pokemon.agents.log_models_mlflow3 import main

# Run the model logging demonstration
main()
```

This will:
1. Set up MLFlow tracking
2. Log both DSPy and OpenAI agent models
3. Demonstrate model loading and inference
4. Show MLFlow 3 features in action

### Using the Updated Main Script

```python
from open_llms_play_pokemon.agents.main_dspy_mlflow3 import main

# Run the game with MLFlow 3 integration
main()
```

This demonstrates:
- Model logging during gameplay
- MLFlow 3 tracking features
- Loading and using logged models

### Loading and Using Logged Models

```python
import mlflow

# Load a model using MLFlow 3
model_uri = "models:/dspy_pokemon_agent/1"  # New URI format
loaded_model = mlflow.pyfunc.load_model(model_uri)

# Use the model for inference
result = loaded_model.predict({
    "action": "start_game",
    "headless": True
})
```

## Model Interface

Both agent models now support a unified interface:

### Input Format
```python
{
    "action": "start_game" | "step",  # Required
    "headless": True | False          # Optional, defaults to True
}
```

### Output Format
```python
{
    "status": "success" | "error",
    "screen_base64": "...",           # Current game screen
    "action_executed": "...",         # Action that was performed
    "success": bool,                  # Whether action succeeded
    "ai_response": "...",            # AI reasoning (OpenAI model only)
    "error": "..."                   # Error message (if status is "error")
}
```

## MLFlow 3 Features Demonstrated

1. **Models from Code Logging**
   - Model code stored as files, not pickled objects
   - Better version control integration
   - More transparent model behavior

2. **Enhanced Metadata**
   - Richer model descriptions
   - Better categorization and searchability
   - Custom metadata fields

3. **Improved Model URIs**
   - New format: `models:/<model_id>` instead of `runs:/<run_id>/<artifact_path>`
   - Direct model referencing
   - Better model lifecycle management

4. **Signature Inference**
   - Automatic model signature detection
   - Better type safety
   - Improved API documentation

## Migration Benefits

### For Development
- **Cleaner model definitions**: Code-based models are easier to understand and modify
- **Better debugging**: Model logic is visible as code, not hidden in pickled objects
- **Version control**: Model changes tracked alongside code changes

### For Deployment
- **Reproducibility**: Exact model behavior recreation from code
- **Environment independence**: No pickle compatibility issues
- **Scalability**: Better suited for microservices and containerized deployments

### For MLOps
- **Model governance**: Better model lifecycle management
- **Traceability**: Clear lineage from code to deployed model
- **Monitoring**: Enhanced observability and debugging capabilities

## Best Practices

1. **Model Code Organization**
   - Keep model logic in separate files
   - Use descriptive names and documentation
   - Include proper error handling

2. **Dependency Management**
   - Specify exact pip requirements
   - Use consistent dependency versions
   - Document external service dependencies

3. **Testing and Validation**
   - Test model loading and inference
   - Validate input/output schemas
   - Check environment compatibility

4. **Metadata and Documentation**
   - Provide comprehensive model descriptions
   - Tag models appropriately
   - Document usage patterns

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are properly specified in `pip_requirements`
2. **Path Issues**: Use absolute paths for model code files
3. **Environment Variables**: Make sure required environment variables are set
4. **Model Loading**: Check that `mlflow.models.set_model()` is called in model code

### Debugging Tips

1. Check MLFlow UI for detailed error messages
2. Verify model artifacts are properly stored
3. Test model loading in isolation
4. Review dependency compatibility

## Next Steps

1. **Monitor Performance**: Track model performance in MLFlow 3 UI
2. **Experiment with Features**: Explore new MLFlow 3 capabilities
3. **Production Deployment**: Consider deployment strategies for code-based models
4. **Integration**: Connect with CI/CD pipelines and model registry

## Resources

- [MLFlow 3.0 Blog Post](https://mlflow.org/blog/mlflow-3-launch)
- [Models from Code Guide](https://mlflow.org/blog/models_from_code)
- [MLFlow 3.0 Documentation](https://mlflow.org/docs/latest/)
- [Pyfunc Model Documentation](https://mlflow.org/docs/latest/python_api/mlflow.pyfunc.html)

---

This migration showcases how MLFlow 3.0's "Models from Code" approach is particularly well-suited for AI agents and GenAI applications, providing better reproducibility, maintainability, and deployment capabilities.