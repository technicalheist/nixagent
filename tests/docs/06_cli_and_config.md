# Configuration and Command Line Interface

Beyond Python imports, `nixagent` provides an integrated CLI wrapper allowing interactive reasoning loops without building a script.

### Using the CLI (`app.py`)
If you have `nixagent` cloned out structurally:

```bash
# Direct Question
python app.py "What text files exist in the public/ directory?"

# Interactive Mode
python app.py
```
*Note: Interactive Mode boots up a persistent conversational loop that maintains message history recursively until you `exit`.*

### Setting up Logging
`nixagent` relies explicitly on safe environment configurations. You can optionally expose deep execution iteration logs to a specific local file natively by defining standard logger values inside the `.env`:

```bash
LOG_LEVEL=DEBUG    # Can be INFO, DEBUG, ERROR, WARNING
LOG_FILE=nix_debug.log 
```

### Safety Mechanics (`MAX_ITERATIONS`)
The framework operates as an autonomous multi-iteration orchestrator. If the model continually decides to chain functions together recursively, `nixagent` securely stops the logic execution automatically to prevent infinite API billing loops.

You can modify this ceiling explicitly:

```bash
# Default is 15. Set to higher value for extreme file-systems operations
MAX_ITERATIONS=50
``` 
