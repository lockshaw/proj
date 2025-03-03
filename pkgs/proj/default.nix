{ buildPythonApplication
, pytestCheckHook
, typing-extensions
, enlighten
, immutables
, setuptools
, pytest-skip-slow
, pytest
, valgrind
, kcachegrind
, callPackage
, ff-clang-format
, bencher-cli
, hotspot
, perf
, ccache
, compdb
, cmake
, mypy
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

    mypy proj/ tests/
    pytest -s -vvvv tests/ -m 'not no_sandbox' --log-level=DEBUG

    runHook postCheck
  '';

  nativeCheckInputs = [
    pytestCheckHook
    pytest
    pytest-skip-slow
    mypy
  ];

  passthru.tests = {
    e2e = callPackage ./tests-e2e.nix { };
  };
}
