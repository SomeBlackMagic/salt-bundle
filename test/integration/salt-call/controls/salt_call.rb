salt_call = ->(arguments) { "sh -c 'salt-call --local -c /workspace/etc/salt #{arguments}'" }

control 'salt-call-utils' do
  describe json(command: salt_call.call('test_module.use_utils --out=json')) do
    its(['local']) { should eq 'utils loaded' }
  end

  describe json(command: salt_call.call('test_extension.use_utils --out=json')) do
    its(['local']) { should eq 'extension utils loaded' }
  end
end

control 'salt-call-bundlefs' do
  describe json(command: salt_call.call('cp.list_states --out=json')) do
    its(['local']) { should include 'foo' }
    its(['local']) { should include 'foo.python' }
  end

  describe json(command: salt_call.call('cp.get_file_str salt://foo/init.sls --out=json')) do
    its(['local']) { should include 'foo_ready:' }
  end
end

control 'salt-call-formula-sls-execution' do
  describe json(command: salt_call.call('state.sls foo --out=json')) do
    its(['local']) do
      should satisfy { |states| states.is_a?(Hash) && states.values.any? { |state| state['__id__'] == 'foo_ready' && state['result'] == true } }
    end
  end

  describe json(command: salt_call.call('state.sls foo.python --out=json')) do
    its(['local']) do
      should satisfy { |states| states.is_a?(Hash) && states.values.any? { |state| state['__id__'] == 'python_ready' && state['result'] == true } }
    end
  end
end

control 'salt-call-modules' do
  describe json(command: salt_call.call('test_module.ping --out=json')) do
    its(['local']) { should eq 'module loaded' }
  end

end

control 'salt-call-states' do
  describe json(command: salt_call.call('state.single test_state.present name=smoketest --out=json')) do
    its(['local']) do
      should satisfy { |states| states.is_a?(Hash) && states.values.any? { |state| state['name'] == 'smoketest' && state['result'] == true && state['comment'] == 'state loaded' } }
    end
  end
end

control 'salt-call-extension-module' do
  describe json(command: salt_call.call('test_extension.ping --out=json')) do
    its(['local']) { should eq 'extension loaded' }
  end

end

control 'salt-call-extension-state' do
  describe json(command: salt_call.call('state.single test_extension.present name=extension-smoketest --out=json')) do
    its(['local']) do
      should satisfy { |states| states.is_a?(Hash) && states.values.any? { |state| state['name'] == 'extension-smoketest' && state['result'] == true && state['comment'] == 'extension state loaded' } }
    end
  end
end

control 'salt-call-python-rendered-formula' do
  describe json(command: salt_call.call('state.show_sls foo.python --out=json')) do
    its(['local']) { should include 'python_ready' }
  end
end

control 'salt-call-grains' do
  describe json(command: salt_call.call('grains.get test_grain --out=json')) do
    its(['local']) { should eq 'loaded' }
  end

  describe json(command: salt_call.call('grains.get extension_grain --out=json')) do
    its(['local']) { should eq 'extension grain loaded' }
  end
end

control 'salt-call-loader-registries' do
  {
    'sys.list_modules' => 'test_module',
    'sys.list_state_modules' => 'test_state'
  }.each do |function, entry|
    describe json(command: salt_call.call("#{function} --out=json")) do
      its(['local']) { should include entry }
    end
  end
end

control 'salt-call-formula-other-loaders' do
  describe json(command: salt_call.call('test_module.probe_loaders --out=json')) do
    its(['local', 'beacons']) { should eq [true, 'valid'] }
    its(['local', 'engines']) { should eq 'engine loaded' }
    its(['local', 'executors']) { should eq 'executor loaded' }
    its(['local', 'matchers']) { should eq true }
    its(['local', 'serializers']) { should eq 'loaded' }
    its(['local', 'wrapper']) { should eq true }
  end
end

{
  'renderers' => 'test_renderer',
  'returners' => 'test_returner'
}.each do |loader, entry|
  control "salt-call-#{loader}" do
    describe json(command: salt_call.call("sys.list_#{loader} --out=json")) do
      its(['local']) { should include entry }
    end
  end
end

control 'salt-call-output' do
  describe command(salt_call.call('test_module.ping --out=test_output')) do
    its('exit_status') { should eq 0 }
    its('stdout') { should include 'output loaded:' }
    its('stdout') { should include 'module loaded' }
  end
end
