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

  nativeCheckInputs = [ 
    proj
    # cmake 
    doctest
    gbenchmark
    rapidcheckFull
    nlohmann_json
    fmt
    # compdb
    # ccache
    # ff-clang-format
    # bencher-cli
    # hotspot
    # valgrind
    # kcachegrind

    python3Packages.pytest
    pytest-skip-slow
  ];

  buildPhase = ''
    export HOME="$(mktemp -d)"

    pytest -s -vvvv --log-level DEBUG -m 'e2e and not no_sandbox' --slow
  '';
}
