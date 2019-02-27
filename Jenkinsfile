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
        stage('Deliver for development') {
            when {
                branch 'development'
            }
            steps {
                sh 'echo helloworld'
                input message: 'Finished using the web site? (Click "Proceed" to continue)'
                sh 'echo kill-server'
            }
        }
        stage('Deploy for production') {
            when {
                branch 'production'
            }
            steps {
                sh 'echo helloworld'
                input message: 'Finished using the web site? (Click "Proceed" to continue)'
                sh 'echo kill-server'
            }
        }
    }
}
