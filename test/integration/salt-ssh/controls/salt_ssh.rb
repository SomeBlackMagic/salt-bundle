salt_ssh = ->(arguments, output = 'json') { "sh -c 'salt-ssh --out=#{output} kitchen-target #{arguments}'" }

# Types listed in Salt SSH's mod_data sync_refs for each branch. This is an
# expected-capability matrix, not a record of what currently passes: a failure
# means SaltBundle's integration with an advertised type needs investigation.
# Keep this explicit: an unreviewed branch must fail the version control below.
salt_version = command('salt-ssh --version').stdout[/\b\d{4}\.\d+\b/]
salt_branch = salt_version&.split('.')&.first
salt_ssh_features = {
  '3006' => %w[modules states grains renderers returners],
  '3007' => %w[modules states grains renderers returners utils],
  '3008' => %w[modules states grains renderers returners utils wrapper tops pillar serializers executors cache sdb]
}.fetch(salt_branch, [])
supports_salt_ssh = ->(feature) { salt_ssh_features.include?(feature) }

control 'salt-ssh-version-matrix' do
  describe command('salt-ssh --version') do
    its('stdout') { should match(/\b(?:3006|3007|3008)\.\d+\b/) }
  end
end

control 'salt-ssh-utils' do
  only_if('Salt SSH does not deliver custom utils in this branch') { supports_salt_ssh.call('utils') }
  describe json(command: salt_ssh.call('test_module.use_utils')) do
    its(['kitchen-target']) { should eq 'utils loaded' }
  end

  describe json(command: salt_ssh.call('test_extension.use_utils')) do
    its(['kitchen-target']) { should eq 'extension utils loaded' }
  end
end

control 'salt-ssh-states-list' do
  describe json(command: salt_ssh.call('cp.list_states')) do
    its(['kitchen-target']) { should include 'foo' }
    its(['kitchen-target']) { should include 'foo.python' }
    its(['kitchen-target']) { should_not include 'example.foo-formula' }
  end
end

control 'salt-ssh-bundlefs' do
  only_if('Salt SSH cp.cache_file cannot fetch salt:// files in these branches') { supports_salt_ssh.call('cache_file') }
  describe json(command: salt_ssh.call('cp.get_file_str salt://foo/init.sls')) do
    its(['kitchen-target']) { should include 'foo_ready:' }
  end
end

control 'salt-ssh-top' do
  describe json(command: salt_ssh.call('state.show_top')) do
    its(['kitchen-target', 'base']) { should include 'foo' }
    its(['kitchen-target', 'base']) { should include 'kitchen_base' }
  end
end

control 'salt-ssh-module' do
  only_if('Salt SSH does not deliver custom modules in this branch') { supports_salt_ssh.call('modules') }
  describe json(command: salt_ssh.call('test_module.ping')) do
    its(['kitchen-target']) { should eq 'module loaded' }
  end
end

control 'salt-ssh-formula-sls-execution' do
  describe json(command: salt_ssh.call('state.sls foo')) do
    its(['kitchen-target']) do
      should satisfy { |states| states.is_a?(Hash) && states.values.any? { |state| state['__id__'] == 'foo_ready' && state['result'] == true } }
    end
  end

  describe json(command: salt_ssh.call('state.sls foo.python')) do
    its(['kitchen-target']) do
      should satisfy { |states| states.is_a?(Hash) && states.values.any? { |state| state['__id__'] == 'python_ready' && state['result'] == true } }
    end
  end
end

control 'salt-ssh-state-apply' do
  describe json(command: salt_ssh.call('state.sls foo test=True')) do
    its(['kitchen-target']) do
      should satisfy { |states| states.is_a?(Hash) && states.any? { |key, state| key.include?('foo_ready') && state['result'] != false } }
    end
  end
end

control 'salt-ssh-states' do
  only_if('Salt SSH does not deliver custom states in this branch') { supports_salt_ssh.call('states') }
  describe json(command: salt_ssh.call('state.single test_state.present name=smoketest')) do
    its(['kitchen-target']) do
      should satisfy { |states| states.is_a?(Hash) && states.values.any? { |state| state['name'] == 'smoketest' && state['result'] == true && state['comment'] == 'state loaded' } }
    end
  end
end

control 'salt-ssh-extension-module' do
  only_if('Salt SSH does not deliver custom modules in this branch') { supports_salt_ssh.call('modules') }
  describe json(command: salt_ssh.call('test_extension.ping')) do
    its(['kitchen-target']) { should eq 'extension loaded' }
  end
end

control 'salt-ssh-extension-state' do
  only_if('Salt SSH does not deliver custom states in this branch') { supports_salt_ssh.call('states') }
  describe json(command: salt_ssh.call('state.single test_extension.present name=extension-smoketest')) do
    its(['kitchen-target']) do
      should satisfy { |states| states.is_a?(Hash) && states.values.any? { |state| state['name'] == 'extension-smoketest' && state['result'] == true && state['comment'] == 'extension state loaded' } }
    end
  end
end

control 'salt-ssh-python-rendered-formula' do
  describe json(command: salt_ssh.call('state.show_sls foo.python')) do
    its(['kitchen-target']) { should include 'python_ready' }
  end
end

control 'salt-ssh-grains' do
  only_if('Salt SSH does not deliver custom grains in this branch') { supports_salt_ssh.call('grains') }
  describe json(command: salt_ssh.call('grains.get test_grain')) do
    its(['kitchen-target']) { should eq 'loaded' }
  end

  describe json(command: salt_ssh.call('grains.get extension_grain')) do
    its(['kitchen-target']) { should eq 'extension grain loaded' }
  end
end

control 'salt-ssh-loader-registries' do
  only_if('Salt SSH does not deliver custom modules and states in this branch') do
    supports_salt_ssh.call('modules') && supports_salt_ssh.call('states')
  end
  {
    'sys.list_modules' => 'test_module',
    'sys.list_state_modules' => 'test_state'
  }.each do |function, entry|
    describe json(command: salt_ssh.call(function)) do
      its(['kitchen-target']) { should include entry }
    end
  end
end

{
  'tops' => { 'base' => ['foo'] },
  'pillar' => { 'test_pillar' => 'pillar loaded' },
  'cache' => { 'bank' => 'test-bank', 'key' => 'test-key', 'source' => 'cache loaded' },
  'sdb' => 'sdb loaded'
}.each do |loader, expected|
  control "salt-ssh-#{loader}" do
    only_if("Salt SSH does not deliver custom #{loader} in this branch") { supports_salt_ssh.call(loader) }
    describe json(command: salt_ssh.call('test_module.probe_loaders')) do
      its(['kitchen-target', loader]) { should eq expected }
    end
  end
end

{
  'beacons' => [true, 'valid'],
  'engines' => 'engine loaded',
  'executors' => 'executor loaded',
  'matchers' => true,
  'serializers' => 'loaded',
  'wrapper' => true
}.each do |loader, expected|
  control "salt-ssh-#{loader}" do
    only_if("Salt SSH does not deliver custom #{loader} in this branch") { supports_salt_ssh.call(loader) }
    describe json(command: salt_ssh.call('test_module.probe_loaders')) do
      its(['kitchen-target', loader]) { should eq expected }
    end
  end
end

{
  'renderers' => 'test_renderer',
  'returners' => 'test_returner'
}.each do |loader, entry|
  control "salt-ssh-#{loader}" do
    only_if("Salt SSH does not deliver custom #{loader} in this branch") { supports_salt_ssh.call(loader) }
    describe json(command: salt_ssh.call("sys.list_#{loader}")) do
      its(['kitchen-target']) { should include entry }
    end
  end
end

control 'salt-ssh-output' do
  only_if('This check calls a custom module unavailable in this branch') { supports_salt_ssh.call('modules') }
  describe command(salt_ssh.call('test_module.ping', 'test_output')) do
    its('exit_status') { should eq 0 }
    its('stdout') { should include 'output loaded:' }
    its('stdout') { should include 'module loaded' }
  end
end
