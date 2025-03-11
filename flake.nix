{
  nixConfig = {
    bash-prompt-prefix = "(proj) ";
  };

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

      packages = rec {
        proj = pkgs.python3Packages.callPackage ./pkgs/proj { 
          inherit pytest-skip-slow;
          inherit bencher-cli;
          inherit ff-clang-format;
          inherit rapidcheckFull;
          inherit doctest;

          # for perf the kernel version doesn't matter as it's entirely in perl
          # see https://discourse.nixos.org/t/which-perf-package/22399
          perf = pkgs.linuxPackages_latest.perf;
        };
        bencher-cli = pkgs.callPackage ./pkgs/bencher.nix { };
        ff-clang-format = pkgs.callPackage ./pkgs/ff-clang-format.nix { };
        doctest = pkgs.callPackage ./pkgs/doctest { };
        pytest-skip-slow = pkgs.python3Packages.callPackage ./pkgs/pytest-skip-slow.nix { };
        proj-nvim = pkgs.callPackage ./pkgs/proj-nvim.nix { inherit proj; };

        rapidcheckFull = pkgs.symlinkJoin {
          name = "rapidcheckFull";
          paths = (with pkgs; [ rapidcheck.out rapidcheck.dev ]);
        };

        default = proj;
      };
    in
    rec {
      inherit packages;

      apps = {
        default = {
          type = "app";
          program = "${self.packages.${system}.proj}/bin/proj";
        };
      };

      devShells = {
        ci = pkgs.mkShell {
          inputsFrom = [ self.packages.${system}.proj ];
        };

        default = pkgs.mkShell {
          inputsFrom = [ 
            self.packages.${system}.proj 
          ];

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
      };
    }
  );
}
# vim: set tabstop=2 shiftwidth=2 expandtab:
