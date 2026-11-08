salt_call = ->(arguments) { "sh -c 'salt-call --local -c /workspace/etc/salt #{arguments}'" }

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

# {
#   'beacons' => '_beacons/test_beacon.py',
#   'utils' => '_utils/test_utils.py',
#   'serializers' => '_serializers/test_serializer.py',
#   'executors' => '_executors/test_executor.py',
#   'engines' => '_engines/test_engine.py',
#   'wrappers' => '_wrapper/test_wrapper.py',
#   'matchers' => '_matchers/test_matcher.py'
# }.each do |loader, path|
#   control "salt-call-#{loader}-fixture" do
#     describe file("#{fixtures_dir}/vendor/example/foo-formula/#{path}") do
#       it { should exist }
#       it { should be_file }
#     end
#   end
# end

control 'salt-call-output' do
  describe command(salt_call.call('test_module.ping --out=test_output')) do
    its('exit_status') { should eq 0 }
    its('stdout') { should include 'output loaded:' }
    its('stdout') { should include 'module loaded' }
  end
end
