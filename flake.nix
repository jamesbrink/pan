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
        };
        
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
            
            echo "Installing hf_xet for faster model downloads..."
            pip install --target="$PIP_TARGET" --quiet hf_xet
            echo "hf_xet successfully installed to .pip directory."
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
