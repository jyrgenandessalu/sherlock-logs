Vagrant.configure("2") do |config|
  config.vm.box = "bento/ubuntu-22.04"
  config.vm.boot_timeout = 600

  # --------------------------------------------------------
  # Shared folder for automation token exchange
  # --------------------------------------------------------
  config.vm.synced_folder "./shared", "/vagrant/shared", create: true

  # --------------------------------------------------------
  # Other Servers (boot first)
  # --------------------------------------------------------
  servers = {
    "web1-server-auto"   => "192.168.56.21",
    "web2-server-auto"   => "192.168.56.22",
    "app-server-auto"    => "192.168.56.23",
    "backup-server-auto" => "192.168.56.24",
    "monitoring-server-auto" => "192.168.56.25"
  }

  servers.each do |name, ip|
    config.vm.define name do |node|
      node.vm.hostname = name
      node.vm.network "private_network", ip: ip

      node.vm.provider "virtualbox" do |vb|
        vb.name = name
        vb.memory = 1024
        vb.cpus = 1
      end

      # Prepare for SSH key injection
      node.vm.provision "shell", inline: <<-SHELL
        mkdir -p /home/vagrant/.ssh
        chmod 700 /home/vagrant/.ssh
      SHELL
    end
  end

  # --------------------------------------------------------
  # Load Balancer (Ansible Control Node)
  # --------------------------------------------------------
  config.vm.define "lb-server-auto" do |lb|
    lb.vm.hostname = "lb-server-auto"
    lb.vm.network "private_network", ip: "192.168.56.20"

    lb.vm.provider "virtualbox" do |vb|
      vb.name = "lb-server-auto"
      vb.memory = 2048
      vb.cpus = 2
    end

    # Wait for others, set up key sharing
    lb.vm.provision "shell", inline: <<-SHELL
      echo "Waiting for other VMs to start..."
      sleep 45
      echo "Setting up SSH key for automation..."
      mkdir -p /home/vagrant/.ssh
      chmod 700 /home/vagrant/.ssh

      # Install sshpass before using it
      sudo apt-get update -y
      sudo apt-get install -y sshpass

      cp /vagrant/.vagrant/machines/lb-server-auto/virtualbox/private_key /home/vagrant/.ssh/id_ed25519
      chmod 600 /home/vagrant/.ssh/id_ed25519
      chown vagrant:vagrant /home/vagrant/.ssh/id_ed25519

      # Copy public key to all target servers for passwordless SSH
      echo "Copying public key to all other servers..."
      PUB_KEY=$(ssh-keygen -y -f /home/vagrant/.ssh/id_ed25519)
      for ip in 192.168.56.21 192.168.56.22 192.168.56.23 192.168.56.24 192.168.56.25; do
        # Try to connect, but don't fail if VM doesn't exist yet
        if sshpass -p "vagrant" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 vagrant@$ip "mkdir -p ~/.ssh && echo $PUB_KEY >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys" 2>/dev/null; then
          echo "Successfully added SSH key to $ip"
        else
          echo "Warning: Could not connect to $ip (VM may not exist yet, will retry on next provision)"
        fi
      done
    SHELL

    # Run Ansible from lb-server-auto after SSH access is set
    lb.vm.provision "ansible_local" do |ansible|
      ansible.playbook = "ansible/site.yml"
      ansible.inventory_path = "ansible/inventory.ini"
      ansible.compatibility_mode = "2.0"
      ansible.limit = "all"
      ansible.raw_arguments = [
        "--ssh-extra-args='-o StrictHostKeyChecking=no -i /home/vagrant/.ssh/id_ed25519'"
      ]
    end
  end
end
