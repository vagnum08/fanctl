project('fanctl', 
  version : '0.1.0',
  default_options: [ 'warning_level=3',
		     'systemddir=/lib/systemd',
                   ],
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())

configure_file(
  input: 'fanctl.py',
  output: 'fanctl',
  configuration: conf,
  install: true,
  install_dir: join_paths(get_option('prefix'),
		          get_option('bindir'))
)

install_data('fanctl.service',
  install_dir: join_paths(get_option('systemddir'), 'system')
)


install_data('config.yml',
  install_dir: join_paths(get_option('sysconfdir'), 'fanctl')
)


# test('basic', exe)
