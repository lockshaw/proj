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

      bencher = ({ stdenv
        , lib
        , fetchurl
        , alsaLib
        , openssl
        , zlib
        , pulseaudio
        , autoPatchelfHook
      }:

      stdenv.mkDerivation rec {
        pname = "bencher-cli";
        version = "0.4.33";

        system = "x86_64-linux";

        src = fetchurl {
          url = "https://github.com/bencherdev/bencher/releases/download/v${version}/bencher-v${version}-linux-x86-64";
          hash = "sha256-3q2ZGSqbcMaUcNMGJN+IsEP/+RlYHnsmiWdJ2oV2qmw=";
        };

        nativeBuildInputs = [
          autoPatchelfHook
        ];

        dontUnpack = true;

        installPhase = ''
        ls
        runHook preInstall
        install -m755 -D $src $out/bin/bencher
        runHook postInstall
        '';

        meta = with lib; {
          homepage = "https://bencher.dev/";
          platforms = platforms.linux;
        };
      });
    in 
    {
      packages = rec {
        proj = pkgs.python3Packages.callPackage ./proj.nix { inherit bencher-cli; };
        bencher-cli = pkgs.callPackage bencher { };

        doctest = pkgs.doctest.overrideAttrs ( old: rec {
          version = "2.4.9";
          src = pkgs.fetchFromGitHub {
            owner = "doctest";
            repo = "doctest";
            rev = "v${version}";
            sha256 = "sha256-ugmkeX2PN4xzxAZpWgswl4zd2u125Q/ADSKzqTfnd94=";
          };
          patches = [
            ./.flake/patches/doctest-template-test.patch
          ];
        });

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
            cmake
            ccache
            nlohmann_json
            fmt
            cmake
            gbenchmark
          ])
          (with pkgs.python3Packages; [
            pip
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
            doctest
          ])
        ];
      };
    }
  );
}
# vim: set tabstop=2 shiftwidth=2 expandtab:
