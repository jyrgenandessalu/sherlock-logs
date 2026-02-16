pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://gitea.kood.tech/jurgenandessalu/sherlock-logs.git',
                    credentialsId: 'gitea-cred'
            }
        }

        stage('Build') {
            steps {
                echo 'Preparing for deployment...'
                sh '''
                    echo "Code checked out successfully"
                    echo "Ready to deploy updated application"
                '''
            }
        }

        stage('Deploy') {
            steps {
                echo 'Deploying application using Ansible...'
                sh '''
                    # Ensure Ansible is available (should be installed via Ansible role)
                    if ! command -v ansible-playbook &> /dev/null; then
                        echo "Installing Ansible..."
                        sudo apt-get update -qq
                        sudo apt-get install -y ansible sshpass
                    fi
                    
                    # Ensure SSH key exists and has correct permissions
                    echo "Setting up SSH key for Jenkins..."
                    sudo mkdir -p /var/lib/jenkins/.ssh
                    sudo chmod 700 /var/lib/jenkins/.ssh
                    sudo chown jenkins:jenkins /var/lib/jenkins/.ssh
                    
                    # Setup or fix SSH key (same approach as manual fix)
                    if [ -f /var/lib/jenkins/.ssh/id_ed25519 ]; then
                        echo "SSH key exists, fixing permissions..."
                        sudo chmod 600 /var/lib/jenkins/.ssh/id_ed25519
                        sudo chown jenkins:jenkins /var/lib/jenkins/.ssh/id_ed25519
                    elif [ -f /home/vagrant/.ssh/id_ed25519 ]; then
                        echo "Copying SSH key from vagrant user..."
                        sudo cp /home/vagrant/.ssh/id_ed25519 /var/lib/jenkins/.ssh/id_ed25519
                        sudo chmod 600 /var/lib/jenkins/.ssh/id_ed25519
                        sudo chown jenkins:jenkins /var/lib/jenkins/.ssh/id_ed25519
                        echo "SSH key copied successfully"
                    else
                        echo "ERROR: SSH key not found! Please set it up manually."
                        exit 1
                    fi
                    
                    # Verify key exists and permissions are correct
                    if [ -f /var/lib/jenkins/.ssh/id_ed25519 ]; then
                        PERMS=$(stat -c "%a" /var/lib/jenkins/.ssh/id_ed25519)
                        OWNER=$(stat -c "%U:%G" /var/lib/jenkins/.ssh/id_ed25519)
                        echo "SSH key permissions: $PERMS, owner: $OWNER"
                        if [ "$PERMS" != "600" ]; then
                            echo "Fixing permissions: $PERMS -> 600"
                            sudo chmod 600 /var/lib/jenkins/.ssh/id_ed25519
                        fi
                        if [ "$OWNER" != "jenkins:jenkins" ]; then
                            echo "Fixing owner: $OWNER -> jenkins:jenkins"
                            sudo chown jenkins:jenkins /var/lib/jenkins/.ssh/id_ed25519
                        fi
                        # Final verification
                        PERMS_FINAL=$(stat -c "%a" /var/lib/jenkins/.ssh/id_ed25519)
                        OWNER_FINAL=$(stat -c "%U:%G" /var/lib/jenkins/.ssh/id_ed25519)
                        if [ "$PERMS_FINAL" != "600" ] || [ "$OWNER_FINAL" != "jenkins:jenkins" ]; then
                            echo "ERROR: Failed to set correct permissions/owner!"
                            echo "Permissions: $PERMS_FINAL (expected 600)"
                            echo "Owner: $OWNER_FINAL (expected jenkins:jenkins)"
                            ls -la /var/lib/jenkins/.ssh/
                            exit 1
                        fi
                        echo "SSH key verified: permissions=600, owner=jenkins:jenkins"
                        ls -la /var/lib/jenkins/.ssh/
                    else
                        echo "ERROR: SSH key not found after setup!"
                        exit 1
                    fi
                    
                    # Run Ansible playbook to deploy to web and app servers
                    cd ansible
                    ansible-playbook -i inventory.ini site.yml --limit web,app -v
                '''
            }
        }
    }

    post {
        success {
            echo '✅ Deployment successful.'
        }
        failure {
            echo '❌ Deployment failed.'
        }
    }
}
