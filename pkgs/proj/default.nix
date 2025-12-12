{ pkgs
, buildPythonApplication
, pytestCheckHook
, typing-extensions
, enlighten
, immutables
, setuptools
, pytest-skip-slow
, pytest
, nclib
, valgrind
, kcachegrind
, ff-clang-format
, bencher-cli
, hotspot
, perf
, ccache
, compdb
, cmake
, mypy
, doctest
, gbenchmark
, libassert
, rapidcheckFull
, nlohmann_json
, fmt
, tree
, lcov
, gdb
, pytest-xdist
# TODO use these if we ever update nixpkgs
# , writableTmpDirAsHomeHook
# , addBinAsPathHook
, ...
}:

let
  lib = pkgs.lib;
  stdenv = pkgs.stdenv;

  bins = [
    ff-clang-format
    ccache
    compdb
    cmake
    lcov
  ] ++ lib.optionals stdenv.isLinux [
    bencher-cli
    hotspot
    valgrind
    kcachegrind
    perf
  ];
in 
buildPythonApplication {
  pname = "proj";
  version = "0.0.1";
  src = ../../.;

  dontUseCmakeConfigure = true;

  propagatedBuildInputs = [
    typing-extensions
    enlighten
    immutables
  ] ++ bins;

  build-system = [
    setuptools
  ];

  checkPhase = ''
    runHook preCheck

    export HOME="$(mktemp -d)"
    export PATH="$out/bin:$PATH"
    mypy proj/ tests/
    TMP=/dev/shm pytest -n $NIX_BUILD_CORES --dist loadgroup -x -s -vvvv tests/ -m 'not no_sandbox' --log-level=DEBUG --slow

    runHook postCheck
  '';

  checkInputs = [
    doctest
    gbenchmark
    rapidcheckFull
    libassert
    nlohmann_json
    fmt
  ];

  nativeCheckInputs = [
    pytest
    pytest-skip-slow
    pytest-xdist
    mypy
    nclib
    gdb
  ] ++ bins;
}
