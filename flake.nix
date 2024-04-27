{
  inputs = {
    nixpkgs.url = "nixpkgs/nixos-23.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }: flake-utils.lib.eachDefaultSystem (system: 
    let 
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = true;
      };

      lib = pkgs.lib;
    in 
    {
      packages = rec {
        proj = pkgs.python3Packages.callPackage ./proj.nix { };

        pytest-skip-slow = pkgs.python3Packages.buildPythonPackage rec {
          pname = "pytest-skip-slow";
          version = "0.0.5";
          pyproject = true;

          src = pkgs.python3Packages.fetchPypi {
            inherit pname version;
            sha256 = "sha256-ZV6lx0jHKUfg0wIzTn+o75mSkleiorySj2MN21oWHYg=";
          };

          nativeBuildInputs = [
            pkgs.python3Packages.flit-core
          ];

          build-system = with pkgs.python3Packages; [
            flit 
          ];
        };


        proj-nvim = pkgs.vimUtils.buildVimPlugin {
          name = "proj-nvim";
          src = ./vim;
          buildInputs = [ self.packages.${system}.proj ];

          postPatch = ''
            substituteInPlace UltiSnips/cpp.snippets --replace "%PROJPATH%" "${proj}/${pkgs.python3.sitePackages}"
          '';
        };
        rapidcheckFull = pkgs.symlinkJoin {
          name = "rapidcheckFull";
          paths = (with pkgs; [ rapidcheck.out rapidcheck.dev ]);
        };

        default = proj;
      };

      apps.default = {
        type = "app";
        program = "${self.packages.${system}.proj}/bin/proj";
      };

      devShells.default = pkgs.mkShell {
        inputsFrom = [ self.packages.${system}.proj ];

        buildInputs = builtins.concatLists [
          (with pkgs; [
            doctest
            cmake
            ccache
            nlohmann_json
            fmt
          ])
          (with pkgs.python3Packages; [
            ipython
            mypy
            python-lsp-server
            pylsp-mypy
            python-lsp-ruff
            black
            toml
            pytest
          ])
          (with self.packages.${system}; [
            rapidcheckFull
            pytest-skip-slow
          ])
        ];
      };
    }
  );
}
# vim: set tabstop=2 shiftwidth=2 expandtab:
