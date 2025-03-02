{ stdenv
, lib
, autoPatchelfHook
, fetchurl
}:

stdenv.mkDerivation rec {
  pname = "ff-clang-format";
  version = "master-f4f85437";

  system = "x86_64-linux";

  src = fetchurl {
    url = "https://github.com/muttleyxd/clang-tools-static-binaries/releases/download/${version}/clang-format-16_linux-amd64";
    hash = "sha256-5eTzOVcmuvSNGr2lyQrBO2Rs0vOed5k7ICPw0IPq4sE=";
  };

  nativeBuildInputs = [
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
    platforms = platforms.linux;
  };
}
