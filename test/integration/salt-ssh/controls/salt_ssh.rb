salt_ssh = ->(arguments, output = 'json') { "sh -c 'salt-ssh --out=#{output} kitchen-target #{arguments}'" }

control 'salt-ssh-utils' do
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
  describe json(command: salt_ssh.call('state.single test_state.present name=smoketest')) do
    its(['kitchen-target']) do
      should satisfy { |states| states.is_a?(Hash) && states.values.any? { |state| state['name'] == 'smoketest' && state['result'] == true && state['comment'] == 'state loaded' } }
    end
  end
end

control 'salt-ssh-extension-module' do
  describe json(command: salt_ssh.call('test_extension.ping')) do
    its(['kitchen-target']) { should eq 'extension loaded' }
  end
end

control 'salt-ssh-extension-state' do
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
  describe json(command: salt_ssh.call('grains.get test_grain')) do
    its(['kitchen-target']) { should eq 'loaded' }
  end

  describe json(command: salt_ssh.call('grains.get extension_grain')) do
    its(['kitchen-target']) { should eq 'extension grain loaded' }
  end
end

control 'salt-ssh-loader-registries' do
  {
    'sys.list_modules' => 'test_module',
    'sys.list_state_modules' => 'test_state'
  }.each do |function, entry|
    describe json(command: salt_ssh.call(function)) do
      its(['kitchen-target']) { should include entry }
    end
  end
end

control 'salt-ssh-formula-other-loaders' do
  describe json(command: salt_ssh.call('test_module.probe_loaders')) do
    its(['kitchen-target', 'beacons']) { should eq [true, 'valid'] }
    its(['kitchen-target', 'engines']) { should eq 'engine loaded' }
    its(['kitchen-target', 'executors']) { should eq 'executor loaded' }
    its(['kitchen-target', 'matchers']) { should eq true }
    its(['kitchen-target', 'serializers']) { should eq 'loaded' }
    its(['kitchen-target', 'wrapper']) { should eq true }
  end
end

{
  'renderers' => 'test_renderer',
  'returners' => 'test_returner'
}.each do |loader, entry|
  control "salt-ssh-#{loader}" do
    describe json(command: salt_ssh.call("sys.list_#{loader}")) do
      its(['kitchen-target']) { should include entry }
    end
  end
end

control 'salt-ssh-output' do
  describe command(salt_ssh.call('test_module.ping', 'test_output')) do
    its('exit_status') { should eq 0 }
    its('stdout') { should include 'output loaded:' }
    its('stdout') { should include 'module loaded' }
  end
end
