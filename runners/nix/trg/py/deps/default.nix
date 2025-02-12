{ pkgs
, lib
, wasmShell
, ...
}@args:
let
	allDeps =
		builtins.map (x: import x args) [
			./bz2.nix
			./zlib.nix
			./xz.nix
			./ffi
		]
	;
	allDepsStr = lib.concatStringsSep " " (builtins.map (x: x.outPath) allDeps);
in wasmShell.stdenv.mkDerivation {
	name = "genvm-py-deps";

	outputHash = "sha256-bR4Ds30vnQ525VC7adX79HBTW4cUhE7tTozRKIW8fJQ=";
	outputHashMode = "recursive";

	srcs = ../../none;
	buildInputs = allDeps;

	installPhase = ''
		mkdir -p "$out/lib"
		mkdir -p "$out/include"
		mkdir -p "$out/share"
		for i in ${allDepsStr}
		do
			cp -r "$i/"* "$out/"
		done
	'';

	dontConfigure = true;
	dontBuild = true;
	dontPatchELF = true;
}
