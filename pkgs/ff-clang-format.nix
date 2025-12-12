{ pkgs
, stdenv
, lib
, autoPatchelfHook
, fetchurl
}:

stdenv.mkDerivation rec {
  pname = "ff-clang-format";
  version = "master-f4f85437";

  system = "x86_64-linux";

  src = let
    blobs = {
      x86_64-linux = {
        url = "https://github.com/muttleyxd/clang-tools-static-binaries/releases/download/${version}/clang-format-16_linux-amd64";
        hash = "sha256-5eTzOVcmuvSNGr2lyQrBO2Rs0vOed5k7ICPw0IPq4sE=";
      };
      x86_64-darwin = {
        url = "https://github.com/muttleyxd/clang-tools-static-binaries/releases/download/${version}/clang-format-16_macosx-amd64";
        hash = "sha256-I9F/mn3I+ZAq2aDw0Mc9Imo+AJMwbzsjalqBSo/7DL4=";
      };
    };
  in
    fetchurl blobs.${pkgs.system};

  nativeBuildInputs = lib.optionals stdenv.isLinux [
    autoPatchelfHook
  ];

  dontUnpack = true;

  installPhase = ''
    runHook preInstall
    install -m755 -D $src $out/bin/ff-clang-format
    runHook postInstall
  '';

  meta = with lib; {
    homepage = "https://github.com/muttleyxd/clang-tools-static-binaries";
    platforms = platforms.linux ++ platforms.darwin;
  };
}
