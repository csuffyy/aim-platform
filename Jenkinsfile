pipeline {
  agent {
    label "production"
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
        load "image-archive/environments/production/env.groovy"
        // echo "${params.Greeting} World!"
        echo "PUBILC_IP: ${env.PUBILC_IP}"
        echo "WORKSPACE: ${env.WORKSPACE}"
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
        sh "sudo systemctl stop aim.service"
      }
    }
    stage('Install Docker') {
      steps {
        sh "sudo jenkins/install_docker.sh"
      }
    }
    stage('Install ElasticSearch') {
      when {
        expression { // Skip if elasticsearch container already exists
          sh (
            script: "sudo docker ps | grep elasticsearch",
            returnStatus: true
          ) != 0
        }
      }
      steps {
        dir('image-archive/elastic-search/') {
          sh "sudo docker rm -f elasticsearch || true"
          sh "./start_elastic.sh"
          sh """bash -c 'while [[ "`curl -v -s -o /dev/null -w ''%{http_code}'' localhost:9200`" != "200" ]]; do echo "trying again"; sleep 5; done; curl localhost:9200; echo "ELASTIC UP"'"""
          sh "sudo docker logs elasticsearch"
          sh "./init_elastic.sh"
          // sh "sudo docker run -p 1358:1358 -d appbaseio/dejavu"
        }
      }
      // post {
      //   failure {
      //       sh "sudo docker rm -f elasticsearch"
      //   }
      // }
    }
    stage("Install DWV") {
      steps {
        dir("image-archive/dwv/") {
          sh "yarn install"
          sh "yarn run start &"
          sh """bash -c 'while [[ "`curl -v -s -o /dev/null -w ''%{http_code}'' localhost:8080`" != "200" ]]; do echo "trying again"; sleep 5; done; curl localhost:8080; echo "DWV UP"'"""
        }
      }
    }
    stage('Install ReactiveSearch') {
      steps {
        dir('image-archive/reactive-search/') {
          sh 'npm install --verbose --color false 2>&1'
          sh 'patch --verbose --ignore-whitespace -p 10 -F 10 node_modules/@appbaseio/reactivesearch/lib/server/index.js < server-side-provide-headers-to-elastic.patch'
          sh 'patch --verbose --ignore-whitespace -p 10 -F 10 node_modules/@appbaseio/reactivesearch/lib/components/result/ReactiveList.js < comma-seperated-numbers.patch'
          sh 'npm run dev &'
cp -r image-archive/reactive-search/appbase-js/* image-archive/reactive-search/node_modules/appbase-js/
          // sh """bash -c 'source ../environments/production/env.sh; while [[ "`curl --cookie "token=${env.AUTH_TOKEN}" -s -o /dev/null -w ''%{http_code}'' localhost:3000`" != "200" ]]; do echo "trying again"; sleep 5; done; echo "ReactiveSearch UP"'"""
        }
      }
    }
    stage('Load Sample Images') {
      when {
          not {
              branch 'production'
          }
      }
      steps {
        dir('image-archive/de-id/') {
          sh 'python3 load_elastic.py ../images/sample-dicom/image_list.txt ../reactive-search/static/thumbnails/'
          sh 'cp ../images/sample-dicom/*.dcm ../reactive-search/static/dicom/'
        }
      }
    }
    stage('Start Tmux') {
      steps {
        sh "sudo systemctl start aim.service"
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
    // buildDiscarder(logRotator(numToKeepStr:'10')) // Disabled because it was removing most recent builds?
    
    // And we'd really like to be sure that this build doesn't hang forever, so
    // let's time it out after an hour.
    timeout(time: 40, unit: 'MINUTES')
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
