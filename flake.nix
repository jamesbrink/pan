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
          # Allow unfree packages but disable CUDA-related packages
          config = { 
            allowUnfree = true;
            # Disable CUDA to avoid platform compatibility issues
            cudaSupport = false;
          };
        };
        
        # Determine if we're on Darwin (macOS)
        isDarwin = pkgs.stdenv.isDarwin;
        
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
          # Use CPU-only torch to avoid CUDA dependencies 
          # But make sure to use only one torch version (either torch or torch-bin, not both)
          (if isDarwin then torch else torch-bin)
          python-dotenv
          huggingface-hub
          
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

        # Define shell hooks as separate functions for better organization
        welcomeMessage = ''
          echo "===== Welcome to PAN Development Environment ====="
          echo "Python version: $(python --version)"
          echo "Platform: ${pkgs.stdenv.hostPlatform.system}"
          echo "Packages from nixpkgs/nixos-unstable"
          echo ""
        '';
        
        setupPipEnvironment = ''
          # Create local pip directory if it doesn't exist
          mkdir -p .pip
          export PIP_TARGET="$(pwd)/.pip"
          export PYTHONPATH="$PIP_TARGET:$PYTHONPATH"
          export PATH="$PIP_TARGET/bin:$PATH"
          
          # Install just the hf_xet extension which isn't available in nixpkgs
          echo "Installing hf_xet extension for Hugging Face hub..."
          pip install --target="$PIP_TARGET" --quiet hf_xet
        '';
        
        printPackageVersions = ''
          # Print package versions for key dependencies
          echo "Python package versions:"
          python -c '
          import sys
          import importlib.util
          
          packages = ["transformers", "huggingface_hub", "accelerate"]
          
          for pkg in packages:
              spec = importlib.util.find_spec(pkg)
              if spec is not None:
                  try:
                      mod = importlib.import_module(pkg)
                      version = getattr(mod, "__version__", "unknown")
                      print(f"{pkg}: {version}")
                  except:
                      print(f"{pkg}: error importing")
              else:
                  print(f"{pkg}: not installed")
          '
        '';
        
        setupEnvironmentFile = ''
          # Check if we need to create a local .env file with default settings
          if [ ! -f .env ]; then
            echo "No .env file found, creating from .env.example..."
            cp .env.example .env
            
            # Always set quantization to none for better cross-platform compatibility
            echo "Setting MODEL_QUANTIZATION_LEVEL=none in .env for compatibility"
            sed -i.bak 's/^MODEL_QUANTIZATION_LEVEL=.*/MODEL_QUANTIZATION_LEVEL=none/' .env
            rm -f .env.bak 2>/dev/null || true
          fi
        '';
        
        printHelpCommands = ''
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
          buildInputs = [
            pythonEnv
            pkgs.git
            pkgs.pre-commit
          ] ++ baseSystemDeps;
          
          # Combine shell hook functions in a clean, modular way
          shellHook = ''
            ${welcomeMessage}
            ${setupPipEnvironment}
            ${printPackageVersions}
            ${setupEnvironmentFile}
            ${printHelpCommands}
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