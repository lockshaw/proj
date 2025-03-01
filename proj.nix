{ buildPythonApplication
, python3Packages
, bencher-cli
, pkgs
, hotspot
, valgrind
, pytestCheckHook
, typing-extensions
, enlighten
, immutables
, setuptools
}:

buildPythonApplication {
  pname = "proj";
  version = "0.0.1";
  src = ./.;

  buildInputs = [
    bencher-cli
    hotspot
    valgrind

    # for perf the kernel version doesn't matter as it's entirely in perl
    # see https://discourse.nixos.org/t/which-perf-package/22399
    pkgs.linuxPackages_latest.perf 
  ];

  dependencies = [
    typing-extensions
    enlighten
    immutables
  ];

  build-system = [
    setuptools
  ];

  nativeCheckInputs = [
    pytestCheckHook
  ];
}
