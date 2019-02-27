pipeline {
    agent {
        label "development"
    }
    environment {
        CI = 'true'
    }
    stages {
        stage('Build') {
            steps {
                sh 'touch /home/ubuntu/build'
            }
        }
        stage('Test') {
            steps {
                sh 'touch /home/ubuntu/test'
            }
        }
    }
}
