compile_cpython_ext = find_target(/\/cpython\/extension$/)

docker_build_files = Dir::glob(cur_src.join('scripts').to_s + '/**/*')
docker_build_files << cur_src.join('Dockerfile').to_s
docker_build_files.sort!()

docker_compile_files = Dir::glob(cur_src.join('scripts-py').to_s + '/**/*')
docker_compile_files.sort!()

docker_id_file = cur_build.join('docker-id.txt')

docker_build_dev_container = target_command(
	command: [RbConfig.ruby, root_src.join('build-scripts', 'docker-build.rb'), cur_build.join('build-log'), docker_id_file],
	dependencies: docker_build_files + docker_compile_files + [root_src.join('build-scripts', 'docker-build.rb')],
	cwd: cur_src,
	output_file: docker_id_file,
	pool: 'console',
)

loc_cur_src = cur_src

target_alias('dev-container', docker_build_dev_container) {
	meta.output_file = docker_build_dev_container.output_file
	meta.dir = loc_cur_src
}

out_dir = cur_build.join('build-out')
cpython_libs_zip = out_dir.join('cpython.zip')
cpython_raw_wasm_path = out_dir.join('cpython.raw.wasm')

build_py_raw = target_command(
	command: [
		RbConfig.ruby, root_src.join('build-scripts', 'docker-run-in.rb'),
		'--log', cur_build.join('run-log'),
		'--id-file', docker_id_file,
		'--out-dir', out_dir,
		'--cp', compile_cpython_ext.meta.output_file,
		'--entrypoint', '/scripts-py/build.sh'
	],
	dependencies: docker_compile_files + [docker_build_dev_container, root_src.join('build-scripts', 'docker-run-in.rb'), compile_cpython_ext],
	cwd: cur_src,
	output_file: cpython_libs_zip,
	pool: 'console',
) {
	outputs.push cpython_raw_wasm_path
}

target_command(
	command: ['diff', '--ignore-all-space', out_dir.join('checksums'), cur_src.join('objs.sha256')],
	tags: ['checksum'],
	output_file: cur_build.join('check-sha256.dirty'),
	dependencies: [build_py_raw],
)


patcher_trg = find_target /\/softfloat\/patcher$/

cpython_softfloat_wasm_path = out_dir.join('cpython.wasm')

build_py_softfloat = target_command(
	command: [
		patcher_trg.meta.output_file,
		cpython_raw_wasm_path,
		cpython_softfloat_wasm_path,
	],
	dependencies: [patcher_trg, build_py_raw],
	output_file: cpython_softfloat_wasm_path,
)

softfloat_target = find_target /\/softfloat\/runner$/

py_runner_target = target_publish_runner(
	name_base: 'genvm-cpython',
	out_dir: config.runners_dir,
	files: [
		{ include: cpython_libs_zip },
		{ path: 'cpython.wasm', read_from: cpython_softfloat_wasm_path }
	],
	runner_dict: {
		"depends": [
			"softfloat:#{softfloat_target.meta.expected_hash}"
		],
		"actions": [
			{ "AddEnv": { "name": "pwd", "val": "/" } },
			{ "MapFile": { "to": "/py/std", "file": "py/" }},
			{ "AddEnv": { "name": "PYTHONPATH", "val": "/py/std" } },
			{ "StartWasm": { "file": "cpython.wasm" } }
		]
	},
	dependencies: [build_py_raw, build_py_softfloat],
	create_test_runner: false,
	expected_hash: config.runners.cpython.hash,
)

target_alias(
	'runner',
	py_runner_target,
	tags: ['all', 'runner'],
	inherit_meta: ['expected_hash'],
) {
	meta.output_file = py_runner_target.output_file
}