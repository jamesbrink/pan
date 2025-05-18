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
        
        # Python packages organized by category for better readability
        pythonPackages = with pkgs.python312.pkgs; {
          devTools = [
            black
            pylint
            isort
            pytest
            pytest-cov
            mypy
            types-requests
            pip  # Ensure pip is available
          ];
          
          core = [
            pyttsx3
            speechrecognition
            pyaudio
            requests
            transformers
            torch
            python-dotenv
            huggingface-hub
            accelerate
          ];
          
          macos = [
            pyobjc-core
            pyobjc-framework-Cocoa
          ];
          
          utils = [
            numpy
            sqlalchemy
            python-dateutil
            beautifulsoup4
          ];
        };
        
        # System dependencies
        systemDeps = [
          pkgs.portaudio
          pkgs.ffmpeg
          pkgs.espeak-ng  # Alternative TTS engine
        ];
        
        # Create the Python environment with all required packages
        pythonEnv = pkgs.python312.withPackages (ps: 
          pythonPackages.devTools ++
          pythonPackages.core ++
          pythonPackages.macos ++
          pythonPackages.utils
        );
        
        # Script to check installed packages
        checkPackageScript = name: ''
          echo -n "${name}: "
          python -c "
          import sys
          try:
              import ${name}
              print(${name}.__version__)
          except (ImportError, AttributeError):
              print('not installed')
          "
        '';
        
        # Environment setup script
        setupEnvScript = ''
          # Create local pip directory if it doesn't exist
          mkdir -p .pip
          export PIP_TARGET="$(pwd)/.pip"
          export PYTHONPATH="$PIP_TARGET:$PYTHONPATH"
          export PATH="$PIP_TARGET/bin:$PATH"
          
          # Install extensions not available in nixpkgs
          pip install --target="$PIP_TARGET" --quiet hf_xet
        '';
        
        # Script to set up .env file if needed
        setupEnvFileScript = ''
          if [ ! -f .env ]; then
            echo "No .env file found, creating from .env.example..."
            cp .env.example .env
            
            # Set quantization to none by default
            # This avoids issues on various platforms
            cp .env .env.tmp
            grep -v "MODEL_QUANTIZATION_LEVEL=" .env.tmp > .env
            echo "MODEL_QUANTIZATION_LEVEL=none" >> .env
            rm .env.tmp
            echo "MODEL_QUANTIZATION_LEVEL=none set in .env"
          fi
        '';
        
        # Welcome message and help script
        welcomeScript = ''
          echo "===== Welcome to PAN Development Environment ====="
          echo "Python version: $(python --version)"
          echo "Packages from nixpkgs/nixos-unstable"
          echo ""
          
          echo "Installing additional dependencies for model management..."
          echo "Python package versions:"
          ${checkPackageScript "transformers"}
          ${checkPackageScript "huggingface_hub"}
          ${checkPackageScript "accelerate"}
          echo ""
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
        
      in {
        devShells.default = pkgs.mkShell {
          # Package dependencies
          buildInputs = [
            pythonEnv
            pkgs.git
            pkgs.pre-commit
          ] ++ systemDeps;
          
          # Shell hook for environment setup
          shellHook = ''
            ${setupEnvScript}
            ${welcomeScript}
            ${setupEnvFileScript}
          '';
          
          # Environment variables
          PYTHONPATH = "./";
          
          # Library paths for system dependencies
          LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath systemDeps;
          DYLD_LIBRARY_PATH = pkgs.lib.makeLibraryPath systemDeps;
        };
      }
    );
}