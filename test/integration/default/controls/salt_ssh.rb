project_dir = '/tmp/salt-pkg'
salt_ssh = ->(arguments) { "sh -c 'cd #{project_dir} && salt-ssh -c #{project_dir}/etc/salt-ssh --out=json kitchen-target #{arguments}'" }

control 'salt-ssh-states-list' do
  describe json(command: salt_ssh.call('cp.list_states')) do
    its(['kitchen-target']) { should include 'foo' }
    its(['kitchen-target']) { should_not include 'example.foo-formula' }
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

control 'salt-ssh-state-apply' do
  describe json(command: salt_ssh.call('state.sls foo test=True')) do
    its(['kitchen-target']) do
      should satisfy { |states| states.is_a?(Hash) && states.any? { |key, state| key.include?('foo_ready') && state['result'] != false } }
    end
  end
end

control 'salt-ssh-without-master-tops' do
  describe json(command: "sh -c 'cd #{project_dir} && salt-ssh -c #{project_dir}/etc/salt-ssh-no-tops --out=json kitchen-target state.show_top'") do
    its(['kitchen-target', 'base']) { should eq ['kitchen_base'] }
  end
end
