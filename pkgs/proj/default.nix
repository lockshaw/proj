{ buildPythonApplication
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
, rapidcheckFull
, nlohmann_json
, fmt
, tree
, lcov
, gdb
# TODO use these if we ever update nixpkgs
# , writableTmpDirAsHomeHook
# , addBinAsPathHook
, ...
}:

let
  bins = [
    valgrind
    kcachegrind
    ff-clang-format
    bencher-cli
    hotspot
    perf
    ccache
    compdb
    cmake
    lcov
    gdb
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
    pytest -x -s -vvvv tests/ -m 'not no_sandbox' --log-level=DEBUG --slow

    runHook postCheck
  '';

  checkInputs = [
    doctest
    gbenchmark
    rapidcheckFull
    nlohmann_json
    fmt
  ];

  nativeCheckInputs = [
    pytest
    pytest-skip-slow
    mypy
    nclib
  ] ++ bins;
}
