{ stdenv
, proj
, cmake
, doctest
, gbenchmark
, rapidcheckFull
, nlohmann_json
, fmt
, compdb
, ccache
, ff-clang-format
, bencher-cli
, hotspot
, valgrind
, pkgs
, python3Packages
, pytest-skip-slow
, kcachegrind
, ...
}:

stdenv.mkDerivation {
  pname = "proj-test-e2e";
  version = proj.version;

  src = proj.src;

  dontUseCmakeConfigure = true;

  nativeBuildInputs = [ 
    proj
    cmake 
    doctest
    gbenchmark
    rapidcheckFull
    nlohmann_json
    fmt
    compdb
    ccache
    ff-clang-format
    bencher-cli
    hotspot
    valgrind
    kcachegrind

    # for perf the kernel version doesn't matter as it's entirely in perl
    # see https://discourse.nixos.org/t/which-perf-package/22399
    pkgs.linuxPackages_latest.perf 
    python3Packages.pytest
    pytest-skip-slow
  ];

  buildPhase = ''
    export HOME="$(mktemp -d)"

    pytest -s -vvvv --log-level DEBUG -m 'e2e and not no_sandbox' --slow
    touch $out
  '';
}
