control 'salt-ssh-loader' do
  impact 1.0
  title 'Matched formula is loaded by the real Salt SSH process'

  describe command('bash /tmp/verify-salt-ssh.sh') do
    its('exit_status') { should eq 0 }
    its('stdout') { should match /With master_tops:.*foo/ }
    its('stdout') { should match /Without master_tops: \['kitchen_base'\]/ }
    its('stdout') { should match /Loaded module: module loaded/ }
    its('stdout') { should match /Applied SLS:.*foo_ready/ }
  end
end
