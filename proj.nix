{ buildPythonApplication
, python3Packages
, bencher-cli
, pkgs
, hotspot
, valgrind
, pytestCheckHook
}:

buildPythonApplication {
  pname = "proj";
  version = "0.0.1";
  src = ./.;

  propagatedBuildInputs = [
    python3Packages.typing-extensions
    python3Packages.enlighten
    python3Packages.immutables
    bencher-cli
    hotspot
    valgrind

    # for perf the kernel version doesn't matter as it's entirely in perl
    # see https://discourse.nixos.org/t/which-perf-package/22399
    pkgs.linuxPackages_latest.perf 
  ];

  nativeCheckInputs = [
    pytestCheckHook
  ];
}
