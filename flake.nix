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
          config = { allowUnfree = true; };
        };
        
        # Determine if we're on Darwin (macOS)
        isDarwin = pkgs.stdenv.isDarwin;
        
        # Check if bitsandbytes is available (without using deepSeq)
        hasBitsAndBytes = builtins.hasAttr "bitsandbytes" pkgs.python312.pkgs;
        
        # Base Python packages needed on all platforms
        basePythonPackages = with pkgs.python312.pkgs; [
          # Development tools
          black
          pylint
          isort
          pytest
          pytest-cov
          mypy
          types-requests
          pip
          
          # Core dependencies
          pyttsx3
          speechrecognition
          pyaudio
          requests
          transformers
          torch
          python-dotenv
          huggingface-hub
          # Add bitsandbytes if available
          (if hasBitsAndBytes then bitsandbytes else null)
          accelerate
          
          # Utility packages
          numpy
          sqlalchemy
          python-dateutil
          beautifulsoup4
        ];
        
        # Platform-specific Python packages
        platformPythonPackages = with pkgs.python312.pkgs; 
          if isDarwin then [
            # macOS specific dependencies
            pyobjc-core
            pyobjc-framework-Cocoa
          ] else [];
        
        # Create Python environment with all packages
        pythonEnv = pkgs.python312.withPackages (ps: 
          basePythonPackages ++ platformPythonPackages
        );
        
        # System dependencies common to all platforms
        baseSystemDeps = [
          pkgs.portaudio
          pkgs.ffmpeg
          pkgs.espeak-ng  # Alternative TTS engine
        ];
        
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.git
            pkgs.pre-commit
          ] ++ baseSystemDeps;
          
          shellHook = ''
            echo "===== Welcome to PAN Development Environment ====="
            echo "Python version: $(python --version)"
            echo "Platform: ${pkgs.stdenv.hostPlatform.system}"
            echo "Packages from nixpkgs/nixos-unstable"
            echo ""
            
            # Create local pip directory if it doesn't exist
            mkdir -p .pip
            export PIP_TARGET="$(pwd)/.pip"
            export PYTHONPATH="$PIP_TARGET:$PYTHONPATH"
            export PATH="$PIP_TARGET/bin:$PATH"
            
            # Install just the hf_xet extension which isn't available in nixpkgs
            echo "Installing hf_xet extension for Hugging Face hub..."
            pip install --target="$PIP_TARGET" --quiet hf_xet
            
            # Print package versions for key dependencies
            echo "Python package versions:"
            for pkg in transformers huggingface_hub accelerate; do
              echo -n "$pkg: "
              python -c "
              import sys
              try:
                  import $pkg
                  print($pkg.__version__)
              except (ImportError, AttributeError):
                  print('not installed')
              "
            done
            
            # Check for bitsandbytes
            echo -n "bitsandbytes: "
            python -c "
            import sys
            try:
                import bitsandbytes
                print(bitsandbytes.__version__)
            except (ImportError, AttributeError):
                print('not installed (quantization will be disabled)')
            "
            
            # Check if we need to create a local .env file with default settings
            if [ ! -f .env ]; then
              echo "No .env file found, creating from .env.example..."
              cp .env.example .env
              
              # Disable quantization by default on Linux and Apple Silicon
              if [ "$(uname -s)" = "Linux" ] || [ "$(uname -sm)" = "Darwin arm64" ]; then
                echo "Setting MODEL_QUANTIZATION_LEVEL=none in .env for compatibility"
                sed -i.bak 's/^MODEL_QUANTIZATION_LEVEL=.*/MODEL_QUANTIZATION_LEVEL=none/' .env
                rm -f .env.bak 2>/dev/null || true
              fi
            fi
            
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
          
          # Set environment variables
          PYTHONPATH = "./";
          
          # Set platform-specific library paths
          LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath baseSystemDeps;
          DYLD_LIBRARY_PATH = if isDarwin then pkgs.lib.makeLibraryPath baseSystemDeps else null;
        };
      }
    );
}