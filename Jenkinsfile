pipeline {
  agent {
    label "development"
  }
  // parameters {
  //   string(name: 'Greeting', defaultValue: InetAddress.localHost.hostAddress, description: 'How should I greet the world?')
  // }
  environment {
    CI = 'true'
    PWDD = pwd()
    WORKSPACE = "${env.PWDD}/image-archive/"
  }
  stages {
    stage('Start') {
      steps {
        showChangeLogs()
        load "image-archive/environments/development/env.groovy"
        // echo "${params.Greeting} World!"
        echo "PUBILC_IP: ${env.PUBILC_IP}"
        sh "env"
      }
    }
    stage('Stop Tmuxinator') {
      when {
        expression { // Tmuxinator if it is already running
          sh (
            script: "tmux ls | grep AIM",
            returnStatus: true
          ) == 0
        }
      }
      steps {
        sh "tmux kill-session -t AIM"
      }
    }
    stage('Start Tmux') {
      steps {
        dir('image-archive/environments/development/') {
          sh "export WORKSPACE=${env.WORKSPACE} && nohup tmuxinator &"
        }
      }
    }
  }

  // post {
    // Always runs. And it runs before any of the other post conditions.
    // always {
      // Let's wipe out the workspace before we finish!
      // deleteDir()
    // }
    
    // Mail disabled because of error:
    // javax.mail.MessagingException: Could not connect to SMTP host: localhost, port: 25;
    // success {
    //   mail(from: "danielsnider12@gmail.com", 
    //        to: "danielsnider12@gmail.com", 
    //        subject: "That build passed.",
    //        body: "Nothing to see here")
    // }

    // failure {
    //   mail(from: "danielsnider12@gmail.com", 
    //        to: "danielsnider12@gmail.com", 
    //        subject: "That build failed!", 
    //        body: "Nothing to see here")
    // }
  // }

  // The options directive is for configuration that applies to the whole job.
  options {
    // For example, we'd like to make sure we only keep 10 builds at a time, so
    // we don't fill up our storage!
    buildDiscarder(logRotator(numToKeepStr:'10'))
    
    // And we'd really like to be sure that this build doesn't hang forever, so
    // let's time it out after an hour.
    timeout(time: 60, unit: 'MINUTES')
  }
}

@NonCPS
def showChangeLogs() {
  // This has definitely worked
  echo "CHANGEZ"
  def changeLogSets = currentBuild.rawBuild.changeSets
  for (int i = 0; i < changeLogSets.size(); i++) {
     def entries = changeLogSets[i].items
     for (int j = 0; j < entries.length; j++) {
          def entry = entries[j]
          echo "CHANGEZ  ${entry.commitId} by ${entry.author} on ${new Date(entry.timestamp)}: ${entry.msg}"
          def files = new ArrayList(entry.affectedFiles)
          for (int k = 0; k < files.size(); k++) {
              def file = files[k]
              echo "CHANGEZ  ${file.editType.name} ${file.path}"
          }
      }
  }
}


// SETUP OF JENKINS AGENT WORKER

// echo vm.max_map_count=262144 | sudo tee -a /etc/sysctl.conf && sudo sysctl -p    # for Elastic Compute
// echo fs.inotify.max_user_watches=582222 | sudo tee -a /etc/sysctl.conf && sudo sysctl -p    # for NodeJS to watch more files

// sudo apt-get install jq

// curl -sL https://deb.nodesource.com/setup_11.x | sudo -E bash -
// sudo apt-get install -y nodejs

// curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
// echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
// sudo apt-get update && sudo apt-get install yarn

// sudo apt install tmuxinator tmux

// Install de-id requirements

// Install Jenkins on host
