include_dir 'trg/py/modules/genvm-cpython-ext/sdk-rust'

reconfigure_on_change cur_src.join('hashes.json')

base_target = target_command(
	output_file: cur_build.join('nix-tools-done'),
	commands: [
		['nix', 'build', '.#genvm-py-precompile', '--no-link'],
		['nix', 'build', '.#genvm-make-runner', '--no-link'],
		['touch', cur_build.join('nix-tools-done')],
	],
	dependencies: (
		cur_src.join('tools').glob('**/*') +
		cur_src.join('envs').glob('**/*') +
		['flake.nix', 'flake.lock'].map { |sub| cur_src.join(sub) }
	),
	pool: 'console',
)

deps = Dir.glob(cur_src.to_s + "/**/*")

hashes = JSON.load_file(cur_src.join('hashes.json'))

sdk_rust = find_target /\/sdk-rust$/

command_target = target_command(
	output_file: [
		config.runners_dir.join('cpython', hashes['cpython'] + '.tar'),
		config.runners_dir.join('softfloat', hashes['softfloat'] + '.tar'),
	],
	commands: [
		[
			'nix', 'build', '.#genvm-runners-all',
			'-o', cur_build.join('nix-out'),
			'--print-build-logs', '--show-trace'
		],
		['cp', '--no-preserve=timestamps,mode,ownership', '-r', cur_build.join('nix-out', 'share'), config.out_dir]
	],
	tags: ['all', 'runner'],
	dependencies: deps + [base_target, sdk_rust],
	pool: 'console',
)

target_alias('nix', command_target) {
	meta.cpython_id = 'cpython:' + hashes['cpython']
	meta.softfloat_id = 'softfloat:' + hashes['softfloat']
}

nix_src = cur_src

$runner_nix_target = base_target

$runner_precompile_command = Proc.new { |dir|
	[
		'nix', 'run', '--', "#{nix_src}#genvm-py-precompile", dir
	]
}

$runner_package_command = Proc.new { |*opts|
	[
		'nix', 'run', '--', "#{nix_src}#genvm-make-runner",
	] + opts
}
