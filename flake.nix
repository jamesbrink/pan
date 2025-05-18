{
  description = "Pan Personality ai voice recognition digital assistant";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          # Allow unfree packages for CUDA dependencies
          config = {
            allowUnfree = true;
          };
        };
        
        # Check if bitsandbytes is available in the current system's packages
        # We use a simpler approach to avoid deepSeq warnings
        hasBitsAndBytes = builtins.hasAttr "bitsandbytes" pkgs.python312.pkgs;
        
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          # Development tools
          black
          pylint
          isort
          pytest
          pytest-cov
          mypy
          types-requests
          pip  # Ensure pip is available
          
          # Core dependencies
          pyttsx3
          speechrecognition
          pyaudio
          requests
          transformers
          torch
          python-dotenv
          # Add huggingface_hub for model downloads
          huggingface-hub
          # Add bitsandbytes for model quantization, if available on this system
          (if hasBitsAndBytes then bitsandbytes else null)
          accelerate
          
          # macOS specific dependencies
          pyobjc-core
          pyobjc-framework-Cocoa
          
          # Utility packages
          numpy
          sqlalchemy
          python-dateutil
          beautifulsoup4
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.git
            pkgs.pre-commit
            # Additional system dependencies
            pkgs.portaudio
            pkgs.ffmpeg
            pkgs.espeak-ng  # Alternative TTS engine
          ];
          
          shellHook = ''
            echo "===== Welcome to PAN Development Environment ====="
            echo "Python version: $(python --version)"
            echo "Packages from nixpkgs/nixos-unstable"
            echo ""
            
            # Create local pip directory if it doesn't exist
            mkdir -p .pip
            export PIP_TARGET="$(pwd)/.pip"
            export PYTHONPATH="$PIP_TARGET:$PYTHONPATH"
            export PATH="$PIP_TARGET/bin:$PATH"
            
            echo "Installing additional dependencies for model management..."
            # Create local pip directory if it doesn't exist
            mkdir -p .pip
            
            # Install just the hf_xet extension which isn't available in nixpkgs
            echo "Installing hf_xet extension for Hugging Face hub..."
            pip install --target="$PIP_TARGET" --quiet hf_xet
            
            # Print package versions for key dependencies
            echo "Python package versions:"
            # Check for installed packages using separate Python commands
            echo -n "transformers: "
            python -c "import transformers; print(transformers.__version__)"
            
            echo -n "bitsandbytes: "
            python -c "
import sys
try:
    import bitsandbytes
    print(bitsandbytes.__version__)
except (ImportError, AttributeError):
    print('not installed (quantization will be disabled)')
"
            
            echo -n "accelerate: "
            python -c "
import sys
try:
    import accelerate
    print(accelerate.__version__)
except (ImportError, AttributeError):
    print('not installed')
"
            
            echo -n "huggingface_hub: "
            python -c "
import sys
try:
    import huggingface_hub
    print(huggingface_hub.__version__)
except (ImportError, AttributeError):
    print('not installed')
"
            
            # Check if we need to create a local .env file with default settings
            if [ ! -f .env ]; then
              echo "No .env file found, creating from .env.example..."
              cp .env.example .env
              
              # Check if bitsandbytes is available and update the .env file accordingly
              # Try to import it first to see if it's actually available at runtime
              echo '
import sys
try:
    import bitsandbytes
    exit(0)
except ImportError:
    exit(1)
' > /tmp/check_bnb.py
              
              # Set quantization to none if:
              # 1. bitsandbytes fails to import, or
              # 2. We're on Apple Silicon (which has known compatibility issues), or
              # 3. We're on Linux (which may have different compatibility issues)
              if ! python /tmp/check_bnb.py || [ "$(uname -sm)" = "Darwin arm64" ] || [ "$(uname -s)" = "Linux" ]; then
                echo "bitsandbytes not available or running on Apple Silicon, setting MODEL_QUANTIZATION_LEVEL=none in .env"
                # Use simple approach that works everywhere
                cp .env .env.tmp
                grep -v "MODEL_QUANTIZATION_LEVEL=" .env.tmp > .env
                echo "MODEL_QUANTIZATION_LEVEL=none" >> .env
                rm .env.tmp
              fi
            fi
            echo "Additional model dependencies successfully installed to .pip directory."
            echo ""
            echo "Development Commands:"
            echo "  make format    - Format code with black and isort"
            echo "  make lint      - Lint code with pylint"
            echo "  make init      - Initialize the database"
            echo "  make all       - Run format, lint, and init"
            echo "  make help      - Show all available commands"
            echo ""
            echo "Run Application:"
            echo "  python main.py"
            echo ""
            echo "First time setup:"
            echo "  cp .env.example .env   - Create your config file"
            echo "  pre-commit install     - Install pre-commit hooks"
            echo "=================================================="
          '';
          
          # Set environment variables if needed
          PYTHONPATH = "./";
          
          # Ensure library paths are properly set
          LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
            pkgs.portaudio
            pkgs.ffmpeg
            pkgs.espeak-ng
          ];
          
          # Set macOS specific environment variables
          DYLD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
            pkgs.portaudio
            pkgs.ffmpeg
            pkgs.espeak-ng
          ];
        };
      }
    );
}
